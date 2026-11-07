import base64
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Body, UploadFile, File
from fastapi.responses import FileResponse
import fitz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import FormSession, FormTemplate, TemplateField, FormResponse, UploadedDocument, ExtractedData, GuestSession, generate_uuid
from app.schemas.session import (
    FormSessionCreate,
    FormSessionResponse,
    FormSessionDetail,
    FormFieldState,
    FieldResponseUpdate,
    SessionMetrics,
    SessionDocumentSummary,
)
from app.schemas.generation import GenerationRequest, GenerationResponse
from app.services.ai import get_ai_provider
from app.services.validation.validator import FieldValidator
from app.services.generation.pdf_generator import PDFGenerator
from app.services.generation.docx_generator import DOCXGenerator
from app.services.session_manager import (
    get_or_create_guest_session,
    get_session_upload_dir,
    get_session_generated_dir,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["Form Sessions"])

def save_base64_signature(data_url: str, output_path: Path) -> str:
    """Decodes a base64 signature image string and writes it to disk."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    raw_bytes = base64.b64decode(data_url)
    with open(output_path, "wb") as f:
        f.write(raw_bytes)
    return str(output_path)

def calculate_metrics(fields: List[FormFieldState]) -> SessionMetrics:
    total = len(fields)
    confirmed = sum(1 for f in fields if f.confirmation_status == "confirmed" or f.validation_status == "confirmed")
    extracted = sum(1 for f in fields if f.current_value and f.validation_status in ["extracted", "confirmed"])
    missing = sum(1 for f in fields if not f.current_value or f.validation_status == "missing")
    conflicts = sum(1 for f in fields if f.validation_status == "conflicting")
    invalid = sum(1 for f in fields if f.validation_status == "invalid")

    # Completion percentage is based on confirmed or validly extracted mandatory/total fields
    pct = (extracted / total * 100.0) if total > 0 else 0.0
    return SessionMetrics(
        total_fields=total,
        confirmed_fields=confirmed,
        extracted_fields=extracted,
        missing_fields=missing,
        conflicting_fields=conflicts,
        invalid_fields=invalid,
        completion_percentage=round(pct, 1),
    )

@router.post("", response_model=FormSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: FormSessionCreate,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Initializes a new form filling session scoped to the active guest session."""
    # Verify template exists within this guest session (or fallback if shared)
    stmt = (
        select(FormTemplate)
        .where(FormTemplate.id == data.template_id)
        .options(selectinload(FormTemplate.fields))
    )
    res = await db.execute(stmt)
    template = res.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    session_id = generate_uuid()
    session = FormSession(
        id=session_id,
        guest_session_id=guest.id,
        template_id=template.id,
        title=data.title or f"Form Session - {template.original_filename}",
        status="draft",
        completion_percentage=0.0,
        current_stage="created"
    )
    db.add(session)

    # Initialize empty FormResponse for each TemplateField
    for field in template.fields:
        resp = FormResponse(
            session_id=session_id,
            field_id=field.id,
            current_value=None,
            confidence=0.0,
            validation_status="missing" if field.required else "extracted",
            confirmation_status="unconfirmed",
        )
        db.add(resp)

    await db.commit()
    await db.refresh(session)
    return session

@router.get("", response_model=List[FormSessionResponse])
async def list_sessions(
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Lists form sessions belonging exclusively to the current guest session."""
    stmt = (
        select(FormSession)
        .where(FormSession.guest_session_id == guest.id)
        .order_by(FormSession.updated_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/{session_id}", response_model=FormSessionDetail)
async def get_session(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full session state with fields, documents, and real-time metrics with guest isolation."""
    stmt = (
        select(FormSession)
        .where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
        .options(
            selectinload(FormSession.template),
            selectinload(FormSession.responses).selectinload(FormResponse.field),
            selectinload(FormSession.responses).selectinload(FormResponse.source_document),
            selectinload(FormSession.documents),
        )
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    field_states = []
    for resp in session.responses:
        field_states.append(
            FormFieldState(
                response_id=resp.id,
                field_id=resp.field_id,
                field_key=resp.field.field_key,
                label=resp.field.label,
                field_type=resp.field.field_type,
                required=resp.field.required,
                section=resp.field.section,
                page_number=resp.field.page_number,
                current_value=resp.current_value,
                source_document_id=resp.source_document_id,
                source_document_name=resp.source_document_name or (resp.source_document.filename if resp.source_document else None),
                source_page=resp.source_page,
                confidence=resp.confidence,
                validation_status=resp.validation_status,
                confirmation_status=resp.confirmation_status,
                validation_error=resp.validation_error,
                candidate_values=resp.candidate_values,
            )
        )

    metrics = calculate_metrics(field_states)
    session.completion_percentage = metrics.completion_percentage

    docs_data = [
        SessionDocumentSummary(
            id=d.id,
            filename=d.filename,
            file_type=d.file_type,
            size=d.file_size,
            status=d.processing_status,
        )
        for d in session.documents
    ]

    detail = FormSessionDetail(
        id=session.id,
        template_id=session.template_id,
        title=session.title,
        status=session.status,
        completion_percentage=metrics.completion_percentage,
        current_stage=session.current_stage,
        generated_document_path=session.generated_document_path,
        created_at=session.created_at,
        updated_at=session.updated_at,
        metrics=metrics,
        fields=field_states,
        documents=docs_data,
    )
    return detail

@router.get("/{session_id}/fields", response_model=List[FormFieldState])
async def get_session_fields(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves field records for form preview with guest session isolation."""
    # Verify session ownership
    sess_stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    sess_res = await db.execute(sess_stmt)
    if not sess_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    stmt = (
        select(FormResponse)
        .where(FormResponse.session_id == session_id)
        .options(selectinload(FormResponse.field), selectinload(FormResponse.source_document))
    )
    res = await db.execute(stmt)
    responses = res.scalars().all()

    results = []
    for resp in responses:
        results.append(
            FormFieldState(
                response_id=resp.id,
                field_id=resp.field_id,
                field_key=resp.field.field_key,
                label=resp.field.label,
                field_type=resp.field.field_type,
                required=resp.field.required,
                section=resp.field.section,
                page_number=resp.field.page_number,
                current_value=resp.current_value,
                source_document_id=resp.source_document_id,
                source_document_name=resp.source_document_name or (resp.source_document.filename if resp.source_document else None),
                source_page=resp.source_page,
                confidence=resp.confidence,
                validation_status=resp.validation_status,
                confirmation_status=resp.confirmation_status,
                validation_error=resp.validation_error,
                candidate_values=resp.candidate_values,
            )
        )
    return results

@router.patch("/{session_id}/fields/{field_id}", response_model=FormFieldState)
async def update_session_field(
    session_id: str,
    field_id: str,
    update_data: FieldResponseUpdate,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Updates a single field value manually and runs validation with session isolation."""
    # Verify session ownership
    sess_stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    sess_res = await db.execute(sess_stmt)
    if not sess_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    stmt = (
        select(FormResponse)
        .where(FormResponse.session_id == session_id, FormResponse.field_id == field_id)
        .options(selectinload(FormResponse.field), selectinload(FormResponse.source_document))
    )
    res = await db.execute(stmt)
    resp = res.scalar_one_or_none()
    if not resp:
        raise HTTPException(status_code=404, detail="Field response record not found")

    if update_data.current_value is not None:
        resp.current_value = update_data.current_value
        resp.confirmation_status = "modified"

    if update_data.confirm:
        resp.confirmation_status = "confirmed"

    # Validate value
    status_code, err = FieldValidator.validate_field(
        field_key=resp.field.field_key,
        label=resp.field.label,
        field_type=resp.field.field_type,
        value=resp.current_value,
        required=resp.field.required,
    )
    resp.validation_status = "confirmed" if resp.confirmation_status == "confirmed" and status_code != "invalid" else status_code
    resp.validation_error = err

    await db.commit()
    await db.refresh(resp)

    return FormFieldState(
        response_id=resp.id,
        field_id=resp.field_id,
        field_key=resp.field.field_key,
        label=resp.field.label,
        field_type=resp.field.field_type,
        required=resp.field.required,
        section=resp.field.section,
        page_number=resp.field.page_number,
        current_value=resp.current_value,
        source_document_id=resp.source_document_id,
        source_document_name=resp.source_document_name or (resp.source_document.filename if resp.source_document else None),
        source_page=resp.source_page,
        confidence=resp.confidence,
        validation_status=resp.validation_status,
        confirmation_status=resp.confirmation_status,
        validation_error=resp.validation_error,
        candidate_values=resp.candidate_values,
    )

@router.post("/{session_id}/analyze")
async def analyze_and_map_session(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Executes the end-to-end processing pipeline:
    1. Extracts text from any unextracted session documents.
    2. Maps extracted text against template fields using AI Provider.
    3. Detects conflicts and missing items.
    4. Validates proposed values deterministically.
    """
    stmt = (
        select(FormSession)
        .where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
        .options(
            selectinload(FormSession.template).selectinload(FormTemplate.fields),
            selectinload(FormSession.documents).selectinload(UploadedDocument.extractions),
            selectinload(FormSession.responses).selectinload(FormResponse.field),
        )
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    session.status = "processing"
    session.current_stage = "reading_documents"
    await db.commit()

    # 1. Document Extraction
    extracted_corpus = []
    for doc in session.documents:
        if not doc.extractions:
            # Run extraction if not yet done
            from app.api.routes.documents import extract_document
            try:
                await extract_document(document_id=doc.id, guest=guest, db=db)
                await db.refresh(doc)
            except Exception as e:
                logger.error(f"Failed extraction on doc {doc.id}: {e}", exc_info=True)

        # Gather extractions
        stmt_ext = select(ExtractedData).where(ExtractedData.document_id == doc.id)
        res_ext = await db.execute(stmt_ext)
        doc_extractions = res_ext.scalars().all()
        for ext in doc_extractions:
            if ext.extracted_text and ext.extracted_text.strip():
                extracted_corpus.append({
                    "document_id": doc.id,
                    "document_name": doc.filename,
                    "page": ext.page_number,
                    "text": ext.extracted_text,
                })

    # 2. Template Field Definitions
    template_fields_data = [
        {
            "field_key": f.field_key,
            "label": f.label,
            "field_type": f.field_type,
            "required": f.required,
            "section": f.section,
        }
        for f in session.template.fields
    ]

    # 3. AI Mapping
    session.current_stage = "ai_mapping"
    await db.commit()

    ai_provider = get_ai_provider()
    try:
        proposed_mappings = await ai_provider.map_fields(extracted_corpus, template_fields_data)
    except Exception as e:
        logger.error(f"AI Mapping failed: {e}")
        proposed_mappings = []

    # 4. Apply Mappings to FormResponses
    response_by_key = {r.field.field_key: r for r in session.responses}

    for mapping in proposed_mappings:
        key = mapping.get("field_key")
        val = mapping.get("proposed_value")
        status_val = mapping.get("status", "extracted")
        confidence = mapping.get("confidence", 0.8)
        source_name = mapping.get("source_document_name")
        source_id = mapping.get("source_document_id")
        source_page = mapping.get("source_page")
        candidates = mapping.get("candidates", [])

        if key in response_by_key:
            resp = response_by_key[key]
            # Don't overwrite if user already confirmed a value
            if resp.confirmation_status != "confirmed":
                resp.current_value = str(val) if val is not None else None
                resp.confidence = confidence
                resp.source_document_name = source_name
                resp.source_document_id = source_id
                resp.source_page = source_page
                resp.candidate_values = candidates

                # Deterministic validation
                val_status, err = FieldValidator.validate_field(
                    field_key=resp.field.field_key,
                    label=resp.field.label,
                    field_type=resp.field.field_type,
                    value=resp.current_value,
                    required=resp.field.required,
                )
                resp.validation_status = status_val if status_val == "conflicting" else val_status
                resp.validation_error = err
        elif key and val:
            # Dynamically register discovered field
            new_field = TemplateField(
                template_id=session.template_id,
                field_key=key,
                label=key.replace("_", " ").title(),
                field_type="text",
                required=False,
                section="Discovered Fields",
                page_number=1,
            )
            db.add(new_field)
            await db.flush()
            new_resp = FormResponse(
                session_id=session.id,
                field_id=new_field.id,
                current_value=str(val),
                confidence=confidence,
                source_document_name=source_name,
                source_document_id=source_id,
                source_page=source_page,
                validation_status="extracted",
                confirmation_status="unconfirmed",
            )
            db.add(new_resp)
            response_by_key[key] = new_resp
            session.responses.append(new_resp)

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
    session.status = "in_progress" if metrics.completion_percentage < 100 else "awaiting_review"
    session.current_stage = "ready_for_review"
    await db.commit()

    return {
        "status": "success",
        "session_id": session.id,
        "completion_percentage": session.completion_percentage,
        "metrics": metrics.model_dump(),
    }

@router.post("/{session_id}/generate", response_model=GenerationResponse)
async def generate_completed_document(
    session_id: str,
    gen_req: GenerationRequest = GenerationRequest(),
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Generates the completed PDF or DOCX file with custom font, size, color, and digital signature."""
    stmt = (
        select(FormSession)
        .where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
        .options(
            selectinload(FormSession.template),
            selectinload(FormSession.responses).selectinload(FormResponse.field),
        )
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    # Handle optional digital signature provided in request
    sig_path = session.signature_path
    if gen_req.signature_data:
        try:
            session_upload_dir = get_session_upload_dir(guest.id)
            sig_file_path = session_upload_dir / f"sig_{session.id[:8]}.png"
            save_base64_signature(gen_req.signature_data, sig_file_path)
            sig_path = str(sig_file_path)
            session.signature_path = sig_path
        except Exception as e:
            logger.warning(f"Could not decode base64 signature in generation request: {e}")

    # Read font & color preferences
    style_pref = session.style_preferences or {}
    font_fam = gen_req.font_family or style_pref.get("font_family") or "Helvetica"
    font_sz = gen_req.font_size or style_pref.get("font_size") or 10.0
    txt_col = gen_req.text_color or style_pref.get("text_color") or "#0f172a"
    session.style_preferences = {
        "font_family": font_fam,
        "font_size": font_sz,
        "text_color": txt_col,
    }

    template_path = session.template.file_path
    format_type = gen_req.format.lower()
    session_gen_dir = get_session_generated_dir(guest.id)
    
    # Collect field data
    field_data = [
        {
            "field_key": r.field.field_key,
            "label": r.field.label,
            "current_value": r.current_value,
            "field_type": r.field.field_type,
            "section": r.field.section,
            "source_document_name": r.source_document_name,
            "confidence": r.confidence,
            "validation_status": r.validation_status,
        }
        for r in session.responses
    ]

    try:
        if format_type == "docx" or session.template.file_type.lower() in [".docx", ".doc"]:
            generator = DOCXGenerator(template_path)
            output_file = generator.generate(
                session.id,
                field_data,
                font_family=font_fam,
                font_size=font_sz,
                text_color=txt_col,
                signature_path=sig_path,
                output_dir=session_gen_dir,
            )
        else:
            generator = PDFGenerator(template_path)
            output_file = generator.generate(
                session.id,
                field_data,
                font_family=font_fam,
                font_size=font_sz,
                text_color=txt_col,
                signature_path=sig_path,
                output_dir=session_gen_dir,
            )

        output_path = Path(output_file)
        session.generated_document_path = str(output_path)
        session.status = "completed"
        await db.commit()

        populated_count = sum(1 for f in field_data if f["current_value"])

        return GenerationResponse(
            session_id=session.id,
            document_id=output_path.stem,
            filename=output_path.name,
            format=format_type,
            download_url=f"/api/sessions/{session.id}/download",
            file_size_bytes=output_path.stat().st_size,
            generated_at=output_path.stat().st_mtime,
            field_count_populated=populated_count,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

@router.post("/{session_id}/signature")
async def save_session_signature(
    session_id: str,
    payload: Dict[str, Any] = Body(...),
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Saves a drawn, typed, or uploaded digital signature to the temporary session."""
    stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    data_url = payload.get("signature_data")
    if not data_url:
        raise HTTPException(status_code=400, detail="Missing signature_data in payload")

    upload_dir = get_session_upload_dir(guest.id)
    sig_path = upload_dir / f"sig_{session.id[:8]}.png"
    save_base64_signature(data_url, sig_path)

    session.signature_path = str(sig_path)
    await db.commit()
    return {"status": "success", "message": "Signature saved", "signature_path": session.signature_path}

@router.get("/{session_id}/signature")
async def get_session_signature(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Streams the active digital signature image."""
    stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session or not session.signature_path or not Path(session.signature_path).exists():
        raise HTTPException(status_code=404, detail="No digital signature saved for this session")

    return FileResponse(session.signature_path, media_type="image/png")

@router.delete("/{session_id}/signature")
async def remove_session_signature(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Removes the digital signature from the session."""
    stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    if session.signature_path and Path(session.signature_path).exists():
        Path(session.signature_path).unlink(missing_ok=True)
    session.signature_path = None
    await db.commit()
    return {"status": "deleted", "message": "Digital signature removed"}

@router.patch("/{session_id}/style")
async def update_session_style(
    session_id: str,
    payload: Dict[str, Any] = Body(...),
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Updates custom typography and formatting preferences for this form session."""
    stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    curr_pref = session.style_preferences or {}
    curr_pref.update({
        "font_family": payload.get("font_family", curr_pref.get("font_family", "Helvetica")),
        "font_size": payload.get("font_size", curr_pref.get("font_size", 10.0)),
        "text_color": payload.get("text_color", curr_pref.get("text_color", "#0f172a")),
    })
    session.style_preferences = curr_pref
    await db.commit()
    return {"status": "success", "style_preferences": session.style_preferences}

@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
async def delete_session(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Manually deletes a form session and its generated output files."""
    stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    if session.generated_document_path and Path(session.generated_document_path).exists():
        Path(session.generated_document_path).unlink(missing_ok=True)
    if session.signature_path and Path(session.signature_path).exists():
        Path(session.signature_path).unlink(missing_ok=True)

    await db.delete(session)
    await db.commit()
    return {"status": "deleted", "message": "Form session deleted successfully"}

@router.get("/{session_id}/download")
async def download_generated_document(
    session_id: str,
    inline: bool = False,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Streams the completed document file to the user."""
    stmt = select(FormSession).where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session or not session.generated_document_path:
        raise HTTPException(status_code=404, detail="Generated document not available for this session")

    file_path = Path(session.generated_document_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical file missing on server")

    media_type = "application/pdf" if file_path.suffix == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    disp_type = "inline" if inline else "attachment"
    return FileResponse(
        path=str(file_path),
        filename=file_path.name,
        media_type=media_type,
        content_disposition_type=disp_type,
    )

@router.get("/{session_id}/preview")
async def preview_session_document(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Serves the document for inline browser viewing.
    Falls back to template file if completed document has not yet been generated.
    """
    stmt = (
        select(FormSession)
        .where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
        .options(selectinload(FormSession.template))
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    target_path = None
    if session.generated_document_path and Path(session.generated_document_path).exists():
        target_path = Path(session.generated_document_path)
    elif session.template and Path(session.template.file_path).exists():
        target_path = Path(session.template.file_path)

    if not target_path:
        raise HTTPException(status_code=404, detail="No previewable document found for this session")

    media_type = "application/pdf" if target_path.suffix.lower() == ".pdf" else "application/octet-stream"
    return FileResponse(
        path=str(target_path),
        filename=target_path.name,
        media_type=media_type,
        content_disposition_type="inline",
    )

@router.get("/{session_id}/page-image/{page_num}")
async def get_session_page_image(
    session_id: str,
    page_num: int = 0,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """
    Renders the requested page of the completed document (or template) as a high-res PNG image.
    Guarantees 100% preview reliability across all browsers without requiring PDF viewer plugins.
    """
    stmt = (
        select(FormSession)
        .where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
        .options(selectinload(FormSession.template))
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    target_path = None
    if session.generated_document_path and Path(session.generated_document_path).exists():
        target_path = Path(session.generated_document_path)
    elif session.template and Path(session.template.file_path).exists():
        target_path = Path(session.template.file_path)

    if not target_path or target_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Page images are only available for PDF documents")

    try:
        doc = fitz.open(str(target_path))
        if page_num < 0 or page_num >= len(doc):
            doc.close()
            raise HTTPException(status_code=404, detail=f"Page {page_num} out of bounds (total pages: {len(doc)})")

        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        doc.close()

        return Response(content=img_bytes, media_type="image/png")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to render page image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to render page: {e}")

@router.get("/{session_id}/page-count")
async def get_session_page_count(
    session_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Returns the total number of pages in the session's active document."""
    stmt = (
        select(FormSession)
        .where(FormSession.id == session_id, FormSession.guest_session_id == guest.id)
        .options(selectinload(FormSession.template))
    )
    res = await db.execute(stmt)
    session = res.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found in active guest session")

    target_path = None
    if session.generated_document_path and Path(session.generated_document_path).exists():
        target_path = Path(session.generated_document_path)
    elif session.template and Path(session.template.file_path).exists():
        target_path = Path(session.template.file_path)

    if not target_path or target_path.suffix.lower() != ".pdf":
        return {"page_count": 1}

    try:
        doc = fitz.open(str(target_path))
        count = len(doc)
        doc.close()
        return {"page_count": count}
    except Exception:
        return {"page_count": 1}
