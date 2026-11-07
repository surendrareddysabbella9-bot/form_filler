from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class AIProvider(ABC):
    """Abstract Base Class for AI inference providers (Groq, Anthropic, OpenAI, or Local)."""

    @abstractmethod
    async def map_fields(
        self,
        extracted_documents: List[Dict[str, Any]],
        template_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Maps extracted content from supporting documents to the target template fields.
        Returns a list of proposed mappings with source lineage, confidence, and status.
        """
        pass

    @abstractmethod
    async def chat_turn(
        self,
        conversation_history: List[Dict[str, str]],
        session_context: Dict[str, Any],
        user_message: str
    ) -> Dict[str, Any]:
        """
        Processes a conversational message in context of missing, conflicting, or invalid fields.
        Returns the assistant's reply, suggested reply chips, and any detected field updates.
        """
        pass
