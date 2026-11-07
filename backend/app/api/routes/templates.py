import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
import fitz
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import FormTemplate, TemplateField, GuestSession, generate_uuid
from app.schemas.template import FormTemplateResponse, TemplateAnalysisResponse, TemplateFieldResponse
from app.services.templates.template_analyzer import TemplateAnalyzer
from app.services.session_manager import get_or_create_guest_session, get_session_upload_dir

router = APIRouter(prefix="/templates", tags=["Templates"])

ALLOWED_TEMPLATE_EXTS = [".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg"]

@router.post("/upload", response_model=FormTemplateResponse, status_code=status.HTTP_201_CREATED)
async def upload_template(
    file: UploadFile = File(...),
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a blank form template (PDF, DOCX, JPG, JPEG, or PNG) scoped to the temporary guest session."""
    # 1. Validate file extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_TEMPLATE_EXTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported template format '{ext}'. Allowed: {', '.join(ALLOWED_TEMPLATE_EXTS)}"
        )

    # 2. Save file to isolated guest session upload directory
    template_id = generate_uuid()
    saved_filename = f"{template_id}_{file.filename}"
    session_upload_dir = get_session_upload_dir(guest.id)
    saved_path = session_upload_dir / saved_filename

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save template: {e}")

    # 3. Handle image templates (.png, .jpg, .jpeg) by creating high-res PDF wrapper for uniform rendering
    active_doc_path = saved_path
    if ext in [".png", ".jpg", ".jpeg"]:
        try:
            img_doc = fitz.open(str(saved_path))
            pdf_bytes = img_doc.convert_to_pdf()
            wrapper_pdf_path = saved_path.with_suffix(".pdf")
            with open(wrapper_pdf_path, "wb") as f:
                f.write(pdf_bytes)
            img_doc.close()
            active_doc_path = wrapper_pdf_path
        except Exception as ie:
            raise HTTPException(status_code=500, detail=f"Failed to process image template: {ie}")

    # 4. Create database entry associated with guest session
    template = FormTemplate(
        id=template_id,
        guest_session_id=guest.id,
        original_filename=file.filename or "template" + ext,
        file_path=str(active_doc_path),
        file_type=ext,
        page_count=1,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    # 5. Automatically run template field analysis (with OCR coordinate detection for images/scans)
    # Analyze the original uploaded file (saved_path) to ensure OCR receives raw pixels
    analyzer = TemplateAnalyzer(str(saved_path))
    try:
        detected_fields = analyzer.analyze()
        for f_data in detected_fields:
            field = TemplateField(
                template_id=template.id,
                field_key=f_data["field_key"],
                label=f_data["label"],
                field_type=f_data.get("field_type", "text"),
                required=f_data.get("required", False),
                section=f_data.get("section", "General"),
                page_number=f_data.get("page_number", 1),
                bounding_box=f_data.get("bounding_box"),
                constraints=f_data.get("constraints", {}),
            )
            db.add(field)
        await db.commit()
    except Exception as e:
        # Don't fail upload if initial analysis has a non-fatal warning
        pass

    # Reload template with fields
    stmt = (
        select(FormTemplate)
        .where(FormTemplate.id == template.id, FormTemplate.guest_session_id == guest.id)
        .options(selectinload(FormTemplate.fields))
    )
    res = await db.execute(stmt)
    full_template = res.scalar_one()

    return full_template

@router.get("/{template_id}", response_model=FormTemplateResponse)
async def get_template(
    template_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves template details and fields scoped to the guest session."""
    stmt = (
        select(FormTemplate)
        .where(FormTemplate.id == template_id, FormTemplate.guest_session_id == guest.id)
        .options(selectinload(FormTemplate.fields))
    )
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found in active guest session")
    return template

@router.post("/{template_id}/analyze", response_model=TemplateAnalysisResponse)
async def analyze_template(
    template_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Re-analyzes template fields with OCR coordinate detection."""
    stmt = (
        select(FormTemplate)
        .where(FormTemplate.id == template_id, FormTemplate.guest_session_id == guest.id)
        .options(selectinload(FormTemplate.fields))
    )
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found in active guest session")

    analyzer = TemplateAnalyzer(template.file_path)
    detected_fields = analyzer.analyze()

    # Clear existing if re-analyzing
    for existing_f in template.fields:
        await db.delete(existing_f)

    created_fields = []
    sections = set()
    for f_data in detected_fields:
        field = TemplateField(
            template_id=template.id,
            field_key=f_data["field_key"],
            label=f_data["label"],
            field_type=f_data.get("field_type", "text"),
            required=f_data.get("required", False),
            section=f_data.get("section", "General"),
            page_number=f_data.get("page_number", 1),
            bounding_box=f_data.get("bounding_box"),
            constraints=f_data.get("constraints", {}),
        )
        db.add(field)
        created_fields.append(field)
        sections.add(f_data.get("section", "General"))

    await db.commit()

    return TemplateAnalysisResponse(
        template_id=template.id,
        filename=template.original_filename,
        total_fields=len(created_fields),
        sections=list(sections),
        fields=[TemplateFieldResponse.model_validate(f) for f in created_fields]
    )

@router.get("/{template_id}/file")
async def get_template_file(template_id: str, db: AsyncSession = Depends(get_db)):
    """Serves the raw template file for in-browser viewing."""
    stmt = select(FormTemplate).where(FormTemplate.id == template_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if not template or not os.path.exists(template.file_path):
        raise HTTPException(status_code=404, detail="Template file not found")
    media_type = "application/pdf" if template.file_type == ".pdf" else "application/octet-stream"
    return FileResponse(template.file_path, media_type=media_type, filename=template.original_filename)
