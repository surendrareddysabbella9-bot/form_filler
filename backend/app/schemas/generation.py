from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class GenerationRequest(BaseModel):
    format: str = Field(default="pdf", description="Output format: pdf or docx")
    font_family: Optional[str] = Field(default="Helvetica", description="Font family: Helvetica, Times-Roman, Courier, Arial")
    font_size: Optional[float] = Field(default=10.0, description="Base font size in points (e.g. 8.0, 10.0, 12.0, 14.0)")
    text_color: Optional[str] = Field(default="#0f172a", description="Hex text color string (e.g. #0f172a, #1e3a8a, #000000)")
    signature_data: Optional[str] = Field(default=None, description="Optional base64 digital signature data URL")

class GenerationResponse(BaseModel):
    session_id: str
    document_id: str
    filename: str
    format: str
    download_url: str
    file_size_bytes: int
    generated_at: datetime
    field_count_populated: int
