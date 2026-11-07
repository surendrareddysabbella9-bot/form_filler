import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.core.database import get_db
from app.models.entities import GuestSession, FormSession, UploadedDocument, utc_now
from datetime import datetime, timezone
from app.services.session_manager import (
    get_or_create_guest_session,
    delete_guest_session,
    clear_guest_session_cookie,
    make_aware,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guest", tags=["Guest Session"])

@router.get("/session")
async def get_guest_session_info(
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns current guest session details, expiration timers, and usage statistics.
    Ensures HTTP-only session cookie is refreshed and active.
    """
    now = datetime.now(timezone.utc)
    last_accessed = make_aware(guest.last_accessed_at)
    created_at = make_aware(guest.created_at)

    idle_elapsed = (now - last_accessed).total_seconds()
    lifetime_elapsed = (now - created_at).total_seconds()

    remaining_idle = max(0, int(guest.idle_timeout_seconds - idle_elapsed))
    remaining_lifetime = max(0, int(guest.max_lifetime_seconds - lifetime_elapsed))

    # Count active forms and documents for this guest
    forms_res = await db.execute(
        select(func.count(FormSession.id)).where(FormSession.guest_session_id == guest.id)
    )
    forms_count = forms_res.scalar() or 0

    docs_res = await db.execute(
        select(func.count(UploadedDocument.id)).where(UploadedDocument.guest_session_id == guest.id)
    )
    docs_count = docs_res.scalar() or 0

    return {
        "session_id": guest.id,
        "guest_session_id": guest.id,
        "is_active": guest.is_active,
        "created_at": guest.created_at.isoformat(),
        "last_accessed_at": guest.last_accessed_at.isoformat(),
        "idle_timeout_seconds": guest.idle_timeout_seconds,
        "max_lifetime_seconds": guest.max_lifetime_seconds,
        "remaining_idle_seconds": remaining_idle,
        "remaining_lifetime_seconds": remaining_lifetime,
        "active_forms_count": forms_count,
        "active_documents_count": docs_count,
        "policy": {
            "mode": "temporary_guest_session",
            "permanent_storage": False,
            "idle_timeout_hours": 1,
            "max_lifetime_hours": 24,
            "summary": "This is a private temporary guest session. All uploaded documents, OCR data, extracted fields, and signatures are automatically purged after 1 hour of inactivity or 24 hours total. Download completed files to your local device.",
            "ai_notice": "Document field extraction uses cloud AI inference (Groq), subject to provider retention and privacy terms."
        }
    }

@router.delete("/session")
async def delete_current_guest_session(
    response: Response,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Manual deletion of the current temporary guest session.
    Immediately purges all uploaded templates, documents, OCR data, signatures,
    generated files, and database records, and clears the session cookie.
    """
    session_id = guest.id
    await delete_guest_session(session_id, db=db, response=response)
    clear_guest_session_cookie(response)
    return {
        "status": "deleted",
        "session_id": session_id,
        "message": "Temporary guest session and all associated files and data were completely deleted."
    }
