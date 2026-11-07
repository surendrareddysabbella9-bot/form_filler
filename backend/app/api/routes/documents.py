import hashlib
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.entities import UploadedDocument, ExtractedData, FormSession, GuestSession, generate_uuid
from app.schemas.document import UploadedDocumentResponse, DocumentExtractionResult, ExtractedDataResponse
from app.services.documents.pdf_processor import PDFProcessor
from app.services.documents.docx_processor import DOCXProcessor
from app.services.ocr.tesseract_service import TesseractOCRService
from app.services.session_manager import get_or_create_guest_session, get_session_upload_dir

router = APIRouter(prefix="/documents", tags=["Documents"])

def compute_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

@router.post("/upload", response_model=List[UploadedDocumentResponse], status_code=status.HTTP_201_CREATED)
async def upload_documents(
    session_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Uploads one or more supporting documents scoped to the temporary guest session."""
    uploaded_records = []
    session_upload_dir = get_session_upload_dir(guest.id)

    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format '{ext}' for file '{file.filename}'. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )

        doc_id = generate_uuid()
        saved_filename = f"{doc_id}_{file.filename}"
        saved_path = session_upload_dir / saved_filename

        try:
            with open(saved_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

        file_size = saved_path.stat().st_size
        file_hash = compute_sha256(saved_path)

        doc = UploadedDocument(
            id=doc_id,
            guest_session_id=guest.id,
            session_id=session_id,
            filename=file.filename or "document" + ext,
            file_path=str(saved_path),
            file_type=ext,
            file_size=file_size,
            sha256_hash=file_hash,
            processing_status="pending"
        )
        db.add(doc)
        uploaded_records.append(doc)

    await db.commit()
    for d in uploaded_records:
        await db.refresh(d)

    return uploaded_records

@router.post("/{document_id}/extract", response_model=DocumentExtractionResult)
async def extract_document(
    document_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Extracts text and entities from an uploaded supporting document using digital parsers or local OCR."""
    stmt = (
        select(UploadedDocument)
        .where(UploadedDocument.id == document_id, UploadedDocument.guest_session_id == guest.id)
    )
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in active guest session")

    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Physical document file missing on disk")

    ext = doc.file_type.lower()
    doc.processing_status = "processing"
    await db.commit()

    created_extractions = []
    ocr_service = TesseractOCRService()

    try:
        # Case 1: PDF Document
        if ext == ".pdf":
            processor = PDFProcessor(str(file_path))
            pages = processor.extract_text_pages()
            
            for page in pages:
                text = page["text"]
                method = page["extraction_method"]
                conf = 0.98

                # If selectable text is empty or too sparse, fall back to OCR if available
                if not page["has_selectable_text"] and ocr_service.is_available():
                    try:
                        import fitz
                        fitz_doc = fitz.open(str(file_path))
                        fitz_page = fitz_doc[page["page_number"] - 1]
                        pix = fitz_page.get_pixmap(dpi=200)
                        session_dir = get_session_upload_dir(guest.id)
                        temp_img_path = session_dir / f"temp_{doc.id}_p{page['page_number']}.png"
                        pix.save(str(temp_img_path))
                        fitz_doc.close()

                        ocr_res = ocr_service.extract_text_from_image(temp_img_path)
                        temp_img_path.unlink(missing_ok=True)

                        if ocr_res.get("text"):
                            text = ocr_res["text"]
                            conf = ocr_res.get("confidence", 0.85)
                            method = "ocr_tesseract"
                    except Exception:
                        pass

                ext_record = ExtractedData(
                    document_id=doc.id,
                    page_number=page["page_number"],
                    extracted_text=text,
                    extraction_method=method,
                    confidence=conf,
                )
                db.add(ext_record)
                created_extractions.append(ext_record)

        # Case 2: Word DOCX Document
        elif ext in [".docx", ".doc"]:
            processor = DOCXProcessor(str(file_path))
            data = processor.extract_text_and_tables()
            ext_record = ExtractedData(
                document_id=doc.id,
                page_number=1,
                extracted_text=data["full_text"],
                extraction_method=data["extraction_method"],
                confidence=0.99,
            )
            db.add(ext_record)
            created_extractions.append(ext_record)

        # Case 3: Image (PNG, JPG, TIFF)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff"]:
            ocr_res = ocr_service.extract_text_from_image(file_path)
            ext_record = ExtractedData(
                document_id=doc.id,
                page_number=1,
                extracted_text=ocr_res.get("text", ""),
                extraction_method=ocr_res.get("extraction_method", "ocr_tesseract"),
                confidence=ocr_res.get("confidence", 0.80),
            )
            db.add(ext_record)
            created_extractions.append(ext_record)

        doc.processing_status = "completed"
        await db.commit()

        return DocumentExtractionResult(
            document_id=doc.id,
            filename=doc.filename,
            status="completed",
            total_pages_extracted=len(created_extractions),
            extractions=[ExtractedDataResponse.model_validate(e) for e in created_extractions]
        )

    except Exception as e:
        doc.processing_status = "failed"
        doc.error_message = str(e)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Document extraction failed: {e}")

@router.get("", response_model=List[UploadedDocumentResponse])
async def list_documents(
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Lists supporting documents belonging exclusively to the current guest session."""
    stmt = (
        select(UploadedDocument)
        .where(UploadedDocument.guest_session_id == guest.id)
        .order_by(UploadedDocument.created_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    guest: GuestSession = Depends(get_or_create_guest_session),
    db: AsyncSession = Depends(get_db)
):
    """Deletes an uploaded document and removes its physical file from disk."""
    stmt = (
        select(UploadedDocument)
        .where(UploadedDocument.id == document_id, UploadedDocument.guest_session_id == guest.id)
    )
    res = await db.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in active guest session")

    file_path = Path(doc.file_path)
    file_path.unlink(missing_ok=True)

    await db.delete(doc)
    await db.commit()
    return None
