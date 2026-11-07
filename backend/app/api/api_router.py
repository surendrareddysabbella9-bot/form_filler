from fastapi import APIRouter
from app.api.routes import templates, documents, sessions, chat, guest
from app.core.config import settings

api_router = APIRouter()

api_router.include_router(guest.router)
api_router.include_router(templates.router)
api_router.include_router(documents.router)
api_router.include_router(sessions.router)
api_router.include_router(chat.router)

@api_router.get("/health", tags=["System"])
async def health_check():
    """System health check and provider status."""
    has_groq = bool(settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 5)
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ai_provider": "Groq API (Cloud LLM)" if has_groq else "Mock AI Engine (Deterministic Fallback)",
        "groq_configured": has_groq,
        "tesseract_configured": bool(settings.TESSERACT_CMD),
    }
