from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ExtractedDataResponse(BaseModel):
    id: str
    page_number: int
    extracted_text: str
    extraction_method: str
    confidence: float
    structured_entities: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True

class UploadedDocumentResponse(BaseModel):
    id: str
    session_id: Optional[str] = None
    filename: str
    file_type: str
    file_size: int
    processing_status: str
    error_message: Optional[str] = None
    created_at: datetime
    page_count: Optional[int] = 1

    class Config:
        from_attributes = True

class DocumentExtractionResult(BaseModel):
    document_id: str
    filename: str
    status: str
    total_pages_extracted: int
    extractions: List[ExtractedDataResponse] = []
