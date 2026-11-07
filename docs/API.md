# API Specification & Endpoints

Base URL: `http://localhost:8000/api`
Interactive Swagger UI: `http://localhost:8000/docs`

## Endpoints

### Templates
- `POST /templates/upload` (multipart/form-data: `file`): Uploads a blank form template (.pdf, .docx). Returns `FormTemplateResponse`.
- `GET /templates/{id}`: Retrieves template metadata and detected fields.
- `POST /templates/{id}/analyze`: Re-runs template analyzer to discover and extract fields.

### Documents
- `POST /documents/upload` (multipart/form-data: `files`, `session_id`): Uploads one or more supporting documents.
- `POST /documents/{id}/extract`: Runs text extraction (digital parsing or Tesseract OCR).
- `GET /documents`: Lists all uploaded supporting documents.
- `DELETE /documents/{id}`: Deletes a document and its file.

### Form Sessions
- `POST /sessions` (`{ template_id, title }`): Initializes a new form filling session.
- `GET /sessions`: Lists all sessions for the dashboard.
- `GET /sessions/{id}`: Retrieves session details, fields, documents, and real-time metrics.
- `GET /sessions/{id}/fields`: Retrieves field states with validation and lineage data.
- `PATCH /sessions/{id}/fields/{field_id}` (`{ current_value, confirm }`): Updates and validates a field value.
- `POST /sessions/{id}/analyze`: Runs end-to-end extraction and AI mapping on all session documents.
- `POST /sessions/{id}/generate` (`{ format }`): Generates completed PDF or DOCX.
- `GET /sessions/{id}/download`: Streams completed document file.

### Conversational Assistant
- `GET /sessions/{id}/chat`: Retrieves conversation history for session.
- `POST /sessions/{id}/chat` (`{ message }`): Sends user message to assistant. Updates form fields and returns assistant response.

### System
- `GET /health`: Health status, active AI provider, and engine diagnostics.
