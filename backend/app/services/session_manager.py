import os
import shutil
import secrets
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from fastapi import Request, Response, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import GuestSession, utc_now

logger = logging.getLogger(__name__)

GUEST_COOKIE_NAME = "guest_session_id"
DEFAULT_IDLE_TIMEOUT = 3600  # 1 hour
DEFAULT_MAX_LIFETIME = 86400  # 24 hours

def get_session_upload_dir(guest_session_id: str) -> Path:
    """Returns the isolated upload directory path for a guest session."""
    p = settings.UPLOAD_DIR / "sessions" / guest_session_id
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_session_generated_dir(guest_session_id: str) -> Path:
    """Returns the isolated generated document directory path for a guest session."""
    p = settings.GENERATED_DIR / "sessions" / guest_session_id
    p.mkdir(parents=True, exist_ok=True)
    return p

def purge_session_disk_storage(guest_session_id: str):
    """Securely deletes all temporary files and directories associated with a guest session."""
    upload_p = settings.UPLOAD_DIR / "sessions" / guest_session_id
    if upload_p.exists():
        try:
            shutil.rmtree(upload_p, ignore_errors=True)
            logger.info(f"Purged session upload dir: {upload_p}")
        except Exception as e:
            logger.warning(f"Error purging session upload dir {upload_p}: {e}")

    generated_p = settings.GENERATED_DIR / "sessions" / guest_session_id
    if generated_p.exists():
        try:
            shutil.rmtree(generated_p, ignore_errors=True)
            logger.info(f"Purged session generated dir: {generated_p}")
        except Exception as e:
            logger.warning(f"Error purging session generated dir {generated_p}: {e}")

async def create_new_guest_session(db: AsyncSession) -> GuestSession:
    """Creates a new guest session with a cryptographically unpredictable session token."""
    token = secrets.token_urlsafe(32)
    session = GuestSession(
        id=token,
        created_at=utc_now(),
        last_accessed_at=utc_now(),
        idle_timeout_seconds=DEFAULT_IDLE_TIMEOUT,
        max_lifetime_seconds=DEFAULT_MAX_LIFETIME,
        is_active=True,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Initialize isolated storage folders
    get_session_upload_dir(token)
    get_session_generated_dir(token)
    logger.info(f"Created new guest session: {token[:8]}...")
    return session

def set_guest_session_cookie(response: Response, session_id: str):
    """Sets a secure HTTP-only session cookie and header."""
    response.set_cookie(
        key=GUEST_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=DEFAULT_MAX_LIFETIME,
        secure=False,  # Allows local HTTP; set True via reverse-proxy in prod
        path="/",
    )
    response.headers["X-Guest-Session-ID"] = session_id

def clear_guest_session_cookie(response: Response):
    """Deletes the guest session cookie."""
    response.delete_cookie(
        key=GUEST_COOKIE_NAME,
        path="/",
        httponly=True,
        samesite="lax",
    )

def make_aware(dt: Optional[datetime]) -> datetime:
    """Ensures datetime object is timezone-aware in UTC (compatible with SQLite and Postgres)."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

async def get_or_create_guest_session(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> GuestSession:
    """
    FastAPI dependency that identifies the active guest session.
    Verifies cryptographically secure token, checks idle and max expiration,
    refreshes access timestamp, and guarantees strict guest session isolation.
    """
    # 1. Look for session token from cookie, then X-Session-ID header
    token = request.cookies.get(GUEST_COOKIE_NAME)
    if not token:
        token = request.headers.get("X-Session-ID") or request.headers.get("X-Guest-Session-ID")
    if token:
        token = token.strip().strip('"').strip("'")

    now = datetime.now(timezone.utc)

    if token:
        stmt = select(GuestSession).where(GuestSession.id == token)
        res = await db.execute(stmt)
        guest = res.scalar_one_or_none()

        if guest and guest.is_active:
            last_accessed = make_aware(guest.last_accessed_at)
            created_at = make_aware(guest.created_at)

            idle_seconds = (now - last_accessed).total_seconds()
            lifetime_seconds = (now - created_at).total_seconds()

            if idle_seconds <= guest.idle_timeout_seconds and lifetime_seconds <= guest.max_lifetime_seconds:
                # Active and valid -> refresh last_accessed_at
                guest.last_accessed_at = now
                await db.commit()
                await db.refresh(guest)
                set_guest_session_cookie(response, guest.id)
                return guest
            else:
                logger.info(f"Guest session {token[:8]} expired (idle={idle_seconds:.0f}s, lifetime={lifetime_seconds:.0f}s). Purging.")
                # Expired -> purge files and delete record
                purge_session_disk_storage(guest.id)
                guest.is_active = False
                await db.delete(guest)
                await db.commit()
                clear_guest_session_cookie(response)

    # 2. No valid session found -> create a fresh guest session
    new_guest = await create_new_guest_session(db)
    set_guest_session_cookie(response, new_guest.id)
    return new_guest

async def delete_guest_session(
    session_id: str,
    db: AsyncSession,
    response: Optional[Response] = None
) -> bool:
    """Manually deletes a guest session, all associated database records, and disk files."""
    stmt = select(GuestSession).where(GuestSession.id == session_id)
    res = await db.execute(stmt)
    guest = res.scalar_one_or_none()

    # Purge physical disk storage
    purge_session_disk_storage(session_id)

    if guest:
        await db.delete(guest)
        await db.commit()
        logger.info(f"Deleted guest session {session_id[:8]} and all associated records.")

    if response:
        clear_guest_session_cookie(response)

    return True

async def cleanup_expired_guest_sessions(db: AsyncSession) -> int:
    """Scans and purges all expired guest sessions and their disk directories."""
    stmt = select(GuestSession)
    res = await db.execute(stmt)
    all_sessions = res.scalars().all()

    now = datetime.now(timezone.utc)
    count = 0
    for s in all_sessions:
        last_accessed = make_aware(s.last_accessed_at)
        created_at = make_aware(s.created_at)
        idle_secs = (now - last_accessed).total_seconds()
        life_secs = (now - created_at).total_seconds()

        if not s.is_active or idle_secs > s.idle_timeout_seconds or life_secs > s.max_lifetime_seconds:
            purge_session_disk_storage(s.id)
            await db.delete(s)
            count += 1

    if count > 0:
        await db.commit()
        logger.info(f"Cleaned up {count} expired guest session(s).")
    return count
