# System Architecture & Technical Design

## 1. High-Level Architecture

The **Intelligent Form Filler** is a generic, AI-powered platform for understanding form templates, extracting text from evidence files, mapping values, detecting ambiguities and conflicts, soliciting conversational clarification, and generating completed forms.

```
[ User Interface: React + TypeScript + Tailwind CSS ]
                       |
               HTTP REST & WebSockets
                       v
       [ FastAPI Asynchronous Gateway ]
                       |
      +----------------+----------------+
      |                |                |
      v                v                v
[ Document & OCR ] [ AI Engine ]  [ Persistence ]
- PyMuPDF / pypdf  - Groq LLM     - PostgreSQL
- python-docx      - LangChain    - Local SQLite
- Tesseract OCR    - Pydantic     - Upload Storage
- OpenCV           - Abstraction  - Generated Docs
```

## 2. Core Subsystems

1. **Document & Template Ingestion (`app/services/documents/` and `app/services/templates/`):**
   - Ingests PDF and DOCX templates.
   - Preserves original files immutably.
   - Detects AcroForms, bounding labels, prompt underlines, tables, and checkboxes.
2. **Dual-Path Text & OCR Engine (`app/services/ocr/`):**
   - Direct text extraction for machine-readable digital documents.
   - Preprocessing (Otsu threshold, deskew) + local Tesseract OCR for scans.
3. **AI Mapping Engine (`app/services/ai/`):**
   - Decoupled via `AIProvider` interface.
   - `GroqAIProvider`: cloud LLM structured mapping using `llama-3.3-70b-versatile`.
   - `MockAIProvider`: offline deterministic regex & rule engine for automated testing and zero-cost operation.
4. **Deterministic Validation Gatekeeper (`app/services/validation/`):**
   - Enforces format rules (PAN, SSN, IFSC, Email, Phone, Date).
   - Validates conditional logic (e.g., spouse name mandatory if married).
5. **Conversational Assistant (`app/api/routes/chat.py`):**
   - Keeps form preview and chat synchronized.
   - Disambiguates conflicts and requests missing fields.
6. **High-Fidelity Document Generation (`app/services/generation/`):**
   - Generates completed PDF and DOCX files into a separate output directory.
   - Preserves original templates unaltered.
