import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Intelligent Form Filler API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    DEBUG: bool = True
    
    # AI Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    # Database Settings
    # Primary is PostgreSQL; automatically falls back to SQLite if PostgreSQL is unavailable
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://postgres:postgres@localhost:5432/form_filler_db"
    )
    SQLITE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR}/form_filler.db"
    USE_SQLITE_FALLBACK: bool = True
    
    # Storage Paths
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    GENERATED_DIR: Path = BASE_DIR / "generated"
    
    # Upload limits
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tiff"]
    
    # OCR settings
    TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "tesseract")
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.GENERATED_DIR.mkdir(parents=True, exist_ok=True)
