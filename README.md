# Intelligent Form Filler
### AI-Powered Document Understanding and Automated Form Completion System

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-CSS%204.0-38B2AC.svg)](https://tailwindcss.com/)
[![Tests](https://img.shields.io/badge/Tests-5%20Passed-emerald.svg)](https://docs.pytest.org/)

The **Intelligent Form Filler** is a generic, AI-powered application designed to simplify and automate the completion of complex structured forms using user-uploaded supporting evidence documents.

---

## 1. Key Capabilities

- **Generic Form Understanding:** Works across all structured forms (Tax filings, University Admissions, Job Applications, Loan Requests, Medical Intake, etc.) — never hardcoded to a single form category.
- **Dual-Path Text & OCR Processing:** Uses native digital extraction for selectable text and OpenCV + Tesseract OCR for scanned physical documents and photographs.
- **AI Field Mapping:** Integrates cloud LLM inference via the Groq API (powered by LangChain) to map extracted facts to form fields with confidence scores and source document lineage.
- **Deterministic Validation Gatekeeper:** Enforces Pydantic format rules (PAN, SSN, IFSC, Dates, Emails, Phones) and conditional logic (e.g., spouse name required when married).
- **Conversational Assistant:** In-context chatbot that clarifies ambiguities, identifies missing information, and asks targeted questions while keeping the form preview in sync.
- **Template Preservation Guarantee:** Populates form fields without altering original template bytes; exports high-fidelity completed PDF and DOCX documents into a separate generated storage directory.

---

## 2. Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18, TypeScript, Tailwind CSS, Lucide React, React Router | Modern SaaS UI/UX inspired by Linear & Stripe |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy, Pydantic | Asynchronous REST API & deterministic validation |
| **Database** | PostgreSQL with SQLite fallback | Persistent data storage with zero-config local fallback |
| **AI Layer** | Groq API, LangChain, Llama 3.3 70B | Cloud-based LLM inference & semantic mapping |
| **Document Processing**| PyMuPDF, pypdf, python-docx, openpyxl | Parsing & populating PDF and Word DOCX templates |
| **OCR & Vision** | Tesseract OCR, OpenCV, Pillow | Image preprocessing and text extraction from scans |

---

## 3. Quickstart & Local Setup

### 3.1 Prerequisites
- Python 3.12+
- Node.js 20+ and npm

### 3.2 Backend Setup & Execution
```powershell
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 3. (Optional) Configure environment variables
# Copy .env.example to .env and add your GROQ_API_KEY if desired
cp .env.example .env

# 4. Start the FastAPI backend server
.\venv\Scripts\python -m app.main
```
The backend starts at `http://localhost:8000`.  
Interactive Swagger API documentation is available at `http://localhost:8000/docs`.

### 3.3 Frontend Setup & Execution
```powershell
# 1. In a separate terminal, navigate to frontend directory
cd frontend

# 2. Start the Vite development server
npm run dev
```
The frontend application will be live at `http://localhost:5173`.

### 3.4 Running the Test Suite
```powershell
cd backend
.\venv\Scripts\pytest
```
All unit and integration tests run in under 1 second.

---

## 4. Application Screens & Workflow

1. **Screen 1: Landing Page (`/`):** Clean, conversion-focused welcome screen explaining the 3-step form-filling process.
2. **Screen 2: Dashboard (`/dashboard`):** Summary metrics (Total, Completed, In Progress, Awaiting Review) and recent form sessions table.
3. **Screen 3: Upload Workspace (`/new-form`):** Guided two-part interface to upload blank templates and multiple supporting documents.
4. **Screen 4: Processing Tracker (`/processing/:id`):** Real-time 6-stage tracker showing template inspection, document reading, OCR, extraction, AI mapping, and validation prep.
5. **Screen 5: Form Completion Workspace (`/workspace/:id`):** 3-panel workspace:
   - *Left Panel:* Form Structure, Sections, and progress gauge.
   - *Center Panel:* Form Preview with live values, status badges, and source lineage.
   - *Right Panel:* Conversational Form Assistant with suggested quick-reply chips and live field synchronization.
6. **Screen 6: Review & Validation (`/review/:id`):** Full checklist of confirmed, missing, and conflicting fields before generation.
7. **Screen 7: Document Download (`/download/:id`):** One-click download for completed PDF/DOCX files.
8. **Screen 8: My Documents (`/documents`):** Repository of uploaded evidence documents with search, type filters, and delete controls.
9. **Screen 9: My Forms (`/forms`):** Management dashboard for all form-filling sessions across draft, in-progress, and completed states.
10. **Screen 10: Settings (`/settings`):** System diagnostics, AI engine status, and privacy parameters.

---

## 5. Architecture Documentation

- [System Architecture Specification](file:///c:/Users/Suren/OneDrive/Desktop/form_filler/docs/ARCHITECTURE.md)
- [REST API Specifications](file:///c:/Users/Suren/OneDrive/Desktop/form_filler/docs/API.md)
- [Developer Setup Guide](file:///c:/Users/Suren/OneDrive/Desktop/form_filler/docs/DEVELOPMENT.md)
- [Master Specification](file:///c:/Users/Suren/OneDrive/Desktop/form_filler/SYSTEM_DOCUMENTATION.md)

---

## 6. License
MIT License. Built with open-source tools for generic AI document automation.
