from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class MappingCandidate(BaseModel):
    value: str
    source_document_id: str
    source_document_name: str
    source_page: int
    confidence: float
    rationale: Optional[str] = None

class ProposedFieldMapping(BaseModel):
    field_key: str
    proposed_value: Optional[str] = None
    source_document_id: Optional[str] = None
    source_document_name: Optional[str] = None
    source_page: Optional[int] = None
    confidence: float = 0.0
    status: str = "extracted" # extracted, needs_review, conflicting, missing
    reason: Optional[str] = None
    candidates: List[MappingCandidate] = []

class AIAnalysisResult(BaseModel):
    mappings: List[ProposedFieldMapping] = []
    missing_fields: List[str] = []
    conflicting_fields: List[str] = []
    summary: Optional[str] = None
