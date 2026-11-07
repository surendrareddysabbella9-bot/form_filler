# Development & Setup Guide

## Prerequisites
- Python 3.12+
- Node.js 20+ and npm 10+
- (Optional) PostgreSQL 15+ (SQLite is automatically used as a zero-config fallback)
- (Optional) Tesseract OCR (Digital PDF extraction runs natively without OCR)
- (Optional) Groq API Key (Mock engine provides offline deterministic extraction)

---

## Backend Setup

1. **Activate Virtual Environment:**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   ```

2. **Configure Environment Variables:**
   ```powershell
   cp .env.example .env
   # Add your GROQ_API_KEY in .env if available
   ```

3. **Run Database Migrations / Startup:**
   ```powershell
   .\venv\Scripts\python -m app.main
   ```
   Backend will start at: `http://localhost:8000`  
   API Documentation: `http://localhost:8000/docs`

4. **Run Automated Test Suite:**
   ```powershell
   .\venv\Scripts\pytest
   ```

---

## Frontend Setup

1. **Navigate and Install Dependencies:**
   ```powershell
   cd frontend
   npm install
   ```

2. **Start Development Server:**
   ```powershell
   npm run dev
   ```
   Frontend will run at: `http://localhost:5173`

3. **Build for Production:**
   ```powershell
   npm run build
   ```
