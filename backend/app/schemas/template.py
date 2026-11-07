from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class TemplateFieldBase(BaseModel):
    field_key: str = Field(..., description="Unique programmatic key for field, e.g. annual_income")
    label: str = Field(..., description="Human readable label from template")
    field_type: str = Field(default="text", description="Data type: text, number, date, email, phone, checkbox, select")
    required: bool = Field(default=False)
    section: str = Field(default="General")
    page_number: int = Field(default=1)
    bounding_box: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None

class TemplateFieldCreate(TemplateFieldBase):
    pass

class TemplateFieldResponse(TemplateFieldBase):
    id: str
    template_id: str

    class Config:
        from_attributes = True

class FormTemplateResponse(BaseModel):
    id: str
    original_filename: str
    file_type: str
    page_count: int
    is_fillable: bool
    created_at: datetime
    fields: List[TemplateFieldResponse] = []

    class Config:
        from_attributes = True

class TemplateAnalysisResponse(BaseModel):
    template_id: str
    filename: str
    total_fields: int
    sections: List[str]
    fields: List[TemplateFieldResponse]
