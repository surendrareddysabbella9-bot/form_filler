import logging
from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.groq_provider import GroqAIProvider
from app.services.ai.mock_provider import MockAIProvider

logger = logging.getLogger(__name__)

def get_ai_provider() -> AIProvider:
    """
    Factory function returning the active AI provider.
    Uses GroqAIProvider if GROQ_API_KEY is configured.
    Falls back gracefully to MockAIProvider with structured diagnostics.
    """
    if settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 5:
        return GroqAIProvider(api_key=settings.GROQ_API_KEY, model=settings.GROQ_MODEL)
    else:
        logger.info("GROQ_API_KEY not configured. Active AI provider is MockAIProvider (deterministic regex & rule engine).")
        return MockAIProvider()
