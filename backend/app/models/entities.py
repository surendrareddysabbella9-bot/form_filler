import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, JSON, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return uuid.uuid4().hex

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    sessions = relationship("FormSession", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("FormTemplate", back_populates="user", cascade="all, delete-orphan")


class GuestSession(Base):
    __tablename__ = "guest_sessions"

    id = Column(String(64), primary_key=True)  # cryptographically unpredictable token
    created_at = Column(DateTime(timezone=True), default=utc_now)
    last_accessed_at = Column(DateTime(timezone=True), default=utc_now)
    idle_timeout_seconds = Column(Integer, default=3600)  # 1 hour
    max_lifetime_seconds = Column(Integer, default=86400)  # 24 hours
    is_active = Column(Boolean, default=True)

    form_sessions = relationship("FormSession", back_populates="guest_session", cascade="all, delete-orphan")
    templates = relationship("FormTemplate", back_populates="guest_session", cascade="all, delete-orphan")
    documents = relationship("UploadedDocument", back_populates="guest_session", cascade="all, delete-orphan")


class FormTemplate(Base):
    __tablename__ = "form_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    guest_session_id = Column(String(64), ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False) # .pdf, .docx, .png, .jpg, .jpeg
    page_count = Column(Integer, default=1)
    is_fillable = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    guest_session = relationship("GuestSession", back_populates="templates")
    user = relationship("User", back_populates="templates")
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan")
    sessions = relationship("FormSession", back_populates="template", cascade="all, delete-orphan")


class TemplateField(Base):
    __tablename__ = "template_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    template_id = Column(String(36), ForeignKey("form_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    field_key = Column(String(100), nullable=False, index=True) # e.g. "applicant_name"
    label = Column(String(255), nullable=False) # e.g. "Full Legal Name"
    field_type = Column(String(50), default="text") # text, number, date, email, phone, checkbox, select
    required = Column(Boolean, default=False)
    section = Column(String(100), default="General") # e.g. "Personal Information"
    page_number = Column(Integer, default=1)
    bounding_box = Column(JSON, nullable=True) # {"x": 100, "y": 200, "width": 150, "height": 30}
    constraints = Column(JSON, nullable=True) # regex, min, max, options, conditional rules

    template = relationship("FormTemplate", back_populates="fields")
    responses = relationship("FormResponse", back_populates="field", cascade="all, delete-orphan")


class FormSession(Base):
    __tablename__ = "form_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    guest_session_id = Column(String(64), ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    template_id = Column(String(36), ForeignKey("form_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, default="Untitled Form")
    status = Column(String(50), default="draft") # draft, processing, in_progress, awaiting_review, completed, failed
    completion_percentage = Column(Float, default=0.0)
    current_stage = Column(String(100), default="created")
    generated_document_path = Column(String(512), nullable=True)
    signature_path = Column(String(512), nullable=True)
    style_preferences = Column(JSON, nullable=True) # {"font_family": "helv", "font_size": 10, "text_color": "#0f172a"}
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    guest_session = relationship("GuestSession", back_populates="form_sessions")
    user = relationship("User", back_populates="sessions")
    template = relationship("FormTemplate", back_populates="sessions")
    documents = relationship("UploadedDocument", back_populates="session", cascade="all, delete-orphan")
    responses = relationship("FormResponse", back_populates="session", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    guest_session_id = Column(String(64), ForeignKey("guest_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    session_id = Column(String(36), ForeignKey("form_sessions.id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_type = Column(String(50), nullable=False) # .pdf, .docx, .png, etc.
    file_size = Column(Integer, default=0)
    sha256_hash = Column(String(64), nullable=True, index=True)
    processing_status = Column(String(50), default="pending") # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    guest_session = relationship("GuestSession", back_populates="documents")
    session = relationship("FormSession", back_populates="documents")
    extractions = relationship("ExtractedData", back_populates="document", cascade="all, delete-orphan")


class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, default=1)
    extracted_text = Column(Text, nullable=False)
    extraction_method = Column(String(50), default="digital_pdf") # digital_pdf, ocr_tesseract, docx_parser
    confidence = Column(Float, default=1.0)
    structured_entities = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    document = relationship("UploadedDocument", back_populates="extractions")


class FormResponse(Base):
    __tablename__ = "form_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("form_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(String(36), ForeignKey("template_fields.id", ondelete="CASCADE"), nullable=False, index=True)
    current_value = Column(Text, nullable=True)
    source_document_id = Column(String(36), ForeignKey("uploaded_documents.id", ondelete="SET NULL"), nullable=True)
    source_document_name = Column(String(255), nullable=True)
    source_page = Column(Integer, nullable=True)
    confidence = Column(Float, default=0.0)
    validation_status = Column(String(50), default="missing") # extracted, needs_review, confirmed, missing, conflicting, invalid
    confirmation_status = Column(String(50), default="unconfirmed") # unconfirmed, confirmed, modified
    validation_error = Column(Text, nullable=True)
    candidate_values = Column(JSON, nullable=True) # list of candidates when conflict exists: [{"val": "...", "source": "...", "confidence": 0.9}]
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    session = relationship("FormSession", back_populates="responses")
    field = relationship("TemplateField", back_populates="responses")
    source_document = relationship("UploadedDocument")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("form_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False) # assistant, user, system
    message = Column(Text, nullable=False)
    suggested_replies = Column(JSON, nullable=True) # ["Yes", "No, edit value", ...]
    updated_field_ids = Column(JSON, nullable=True) # ["annual_income"]
    created_at = Column(DateTime(timezone=True), default=utc_now)

    session = relationship("FormSession", back_populates="chat_messages")
