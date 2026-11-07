import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.entities import FormSession, FormResponse, ChatMessage, GuestSession
from app.schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatTurnResult
from app.schemas.session import FormFieldState
from app.services.ai import get_ai_provider
from app.services.validation.validator import FieldValidator
from app.services.session_manager import get_or_create_guest_session
from app.api.routes.sessions import calculate_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Conversational Assistant"])

@router.get("/{session_id}/chat", response_model=List[ChatMessageResponse])
async def get_chat_history(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Fetches conversation history for the session with guest session isolation."""
    # Verify session ownership
    sess_stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    sess_res = await db.execute(sess_stmt)
    if not sess_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("/{session_id}/chat", response_model=ChatTurnResult)
async def send_chat_message(
    session_id: str,
    payload: ChatMessageCreate,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends a message to the AI assistant in context of the active form session.
    Automatically interprets answers, validates updates, and keeps form preview synchronized.
    """
    stmt = (
        select(FormSession)
        .where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
        .options(
            selectinload(FormSession.responses).selectinload(FormResponse.field),
            selectinload(FormSession.chat_messages),
        )
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    # 1. Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        message=payload.message,
    )
    db.add(user_msg)
    await db.commit()

    # 2. Compile session context
    missing_fields = []
    conflicting_fields = []
    current_fields = []

    for r in session.responses:
        item = {
            "field_key": r.field.field_key,
            "label": r.field.label,
            "current_value": r.current_value,
            "status": r.validation_status,
            "confirmation_status": r.confirmation_status,
        }
        current_fields.append(item)
        if r.validation_status == "conflicting":
            conflicting_fields.append(item)
        elif not r.current_value or r.validation_status in ["missing", "invalid"]:
            missing_fields.append(item)

    session_context = {
        "missing_fields": missing_fields,
        "conflicting_fields": conflicting_fields,
        "current_fields": current_fields,
    }

    # 3. Compile history
    history = [
        {"role": m.role, "message": m.message}
        for m in sorted(session.chat_messages, key=lambda x: x.created_at)
    ]

    # 4. Invoke AI provider
    ai_provider = get_ai_provider()
    try:
        turn_result = await ai_provider.chat_turn(
            conversation_history=history,
            session_context=session_context,
            user_message=payload.message,
        )
    except Exception as e:
        logger.error(f"Chat turn execution error: {e}")
        turn_result = {
            "assistant_reply": "I encountered a momentary issue processing that answer. Could you please repeat or verify?",
            "suggested_replies": [],
            "updated_fields": [],
        }

    # 5. Apply validated field updates to authoritative state
    updated_field_keys = []
    response_map = {r.field.field_key: r for r in session.responses}

    for update in turn_result.get("updated_fields", []):
        f_key = update.get("field_key")
        val = update.get("value")
        confirm = update.get("confirm", False)

        if f_key in response_map:
            resp = response_map[f_key]
            if val is not None:
                resp.current_value = str(val)
                resp.confirmation_status = "confirmed" if confirm else "modified"

            val_status, err = FieldValidator.validate_field(
                field_key=resp.field.field_key,
                label=resp.field.label,
                field_type=resp.field.field_type,
                value=resp.current_value,
                required=resp.field.required,
            )
            resp.validation_status = "confirmed" if resp.confirmation_status == "confirmed" and val_status != "invalid" else val_status
            resp.validation_error = err
            updated_field_keys.append(f_key)
        elif f_key and val:
            from app.models.entities import TemplateField
            new_f = TemplateField(
                template_id=session.template_id,
                field_key=f_key,
                label=f_key.replace("_", " ").title(),
                field_type="text",
                required=False,
                section="User Additions",
                page_number=1,
            )
            db.add(new_f)
            await db.flush()
            new_r = FormResponse(
                session_id=session.id,
                field_id=new_f.id,
                current_value=str(val),
                confidence=1.0,
                validation_status="confirmed" if confirm else "extracted",
                confirmation_status="confirmed" if confirm else "modified",
            )
            db.add(new_r)
            session.responses.append(new_r)
            response_map[f_key] = new_r
            updated_field_keys.append(f_key)

    # 6. Save assistant message
    asst_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        message=turn_result.get("assistant_reply", ""),
        suggested_replies=turn_result.get("suggested_replies", []),
        updated_field_ids=updated_field_keys,
    )
    db.add(asst_msg)

    # Recalculate metrics
    all_states = [
        FormFieldState(
            response_id=r.id,
            field_id=r.field_id,
            field_key=r.field.field_key,
            label=r.field.label,
            field_type=r.field.field_type,
            required=r.field.required,
            section=r.field.section,
            page_number=r.field.page_number,
            current_value=r.current_value,
            confidence=r.confidence,
            validation_status=r.validation_status,
            confirmation_status=r.confirmation_status,
            validation_error=r.validation_error,
        )
        for r in session.responses
    ]
    metrics = calculate_metrics(all_states)
    session.completion_percentage = metrics.completion_percentage
    if session.completion_percentage >= 100.0 and session.status != "completed":
        session.status = "awaiting_review"

    await db.commit()

    return ChatTurnResult(
        assistant_reply=turn_result.get("assistant_reply", ""),
        suggested_replies=turn_result.get("suggested_replies", []),
        updated_fields=[{"field_key": k} for k in updated_field_keys],
        session_metrics=metrics.model_dump(),
    )
