from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class FieldResponseUpdate(BaseModel):
    current_value: Optional[str] = None
    confirm: bool = False

class FormFieldState(BaseModel):
    response_id: str
    field_id: str
    field_key: str
    label: str
    field_type: str
    required: bool
    section: str
    page_number: int
    current_value: Optional[str] = None
    source_document_id: Optional[str] = None
    source_document_name: Optional[str] = None
    source_page: Optional[int] = None
    confidence: float = 0.0
    validation_status: str # extracted, needs_review, confirmed, missing, conflicting, invalid
    confirmation_status: str # unconfirmed, confirmed, modified
    validation_error: Optional[str] = None
    candidate_values: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

class SessionMetrics(BaseModel):
    total_fields: int
    confirmed_fields: int
    extracted_fields: int
    missing_fields: int
    conflicting_fields: int
    invalid_fields: int
    completion_percentage: float

class FormSessionCreate(BaseModel):
    template_id: str
    title: Optional[str] = "Untitled Form"

class FormSessionResponse(BaseModel):
    id: str
    template_id: str
    title: str
    status: str
    completion_percentage: float
    current_stage: str
    generated_document_path: Optional[str] = None
    signature_path: Optional[str] = None
    style_preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    metrics: Optional[SessionMetrics] = None

    class Config:
        from_attributes = True

class SessionDocumentSummary(BaseModel):
    id: str
    filename: str
    file_type: str
    size: Optional[int] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

class FormSessionDetail(FormSessionResponse):
    fields: List[FormFieldState] = []
    documents: List[SessionDocumentSummary] = []
