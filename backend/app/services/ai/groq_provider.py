import json
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)

class GroqAIProvider(AIProvider):
    """Integrates Groq API cloud LLM inference via LangChain / Groq SDK with Pydantic validation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model_name = model or settings.GROQ_MODEL

    async def map_fields(
        self,
        extracted_documents: List[Dict[str, Any]],
        template_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        from groq import AsyncGroq
        client = AsyncGroq(api_key=self.api_key)

        # Prepare field requirements summary
        fields_summary = [
            {
                "field_key": f["field_key"],
                "label": f["label"],
                "type": f.get("field_type", "text"),
                "required": f.get("required", False),
                "section": f.get("section", "General"),
            }
            for f in template_fields
        ]

        # Prepare document excerpts (bounded to prevent token limits)
        docs_summary = []
        for doc in extracted_documents:
            text_preview = doc.get("text", "")[:3000] # Cap excerpt
            docs_summary.append({
                "document_id": doc.get("document_id"),
                "document_name": doc.get("document_name", "Document"),
                "page": doc.get("page", 1),
                "text": text_preview,
            })

        system_prompt = (
            "You are an expert AI document parsing and form-mapping engine. "
            "Your objective is to extract facts from the supporting documents and map them to target template form fields. "
            "Rules:\n"
            "1. Only propose values explicitly corroborated by the text. Never hallucinate.\n"
            "2. If multiple documents state conflicting values for the same field (e.g. different dates of birth or different addresses), "
            "set status='conflicting' and include both candidates.\n"
            "3. If a field cannot be found, omit it or set proposed_value=null and status='missing'.\n"
            "4. Return strict JSON with a top-level key 'mappings' containing a list of objects:\n"
            "   - field_key: string\n"
            "   - proposed_value: string or null\n"
            "   - source_document_name: string or null\n"
            "   - source_page: integer or null\n"
            "   - confidence: float between 0.0 and 1.0\n"
            "   - status: 'extracted' | 'needs_review' | 'conflicting' | 'missing'\n"
            "   - reason: brief rationale\n"
            "   - candidates: list of candidate objects if conflict exists\n"
        )

        user_content = json.dumps({
            "target_fields": fields_summary,
            "supporting_documents": docs_summary
        }, indent=2)

        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract and map the fields for these documents:\n\n{user_content}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            raw_text = response.choices[0].message.content
            parsed = json.loads(raw_text)
            return parsed.get("mappings", [])
        except Exception as e:
            logger.error(f"Groq field mapping failed: {e}")
            raise e

    async def chat_turn(
        self,
        conversation_history: List[Dict[str, str]],
        session_context: Dict[str, Any],
        user_message: str
    ) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not configured.")

        from groq import AsyncGroq
        client = AsyncGroq(api_key=self.api_key)

        system_prompt = (
            "You are an intelligent, friendly AI Form Assistant for the Intelligent Form Filler. "
            "You are helping the user complete their form by resolving missing information, confirming extracted values, "
            "or resolving conflicts between documents.\n\n"
            "Context Information:\n"
            f"- Missing mandatory fields: {json.dumps(session_context.get('missing_fields', []))}\n"
            f"- Fields with conflicts: {json.dumps(session_context.get('conflicting_fields', []))}\n"
            f"- Current form fields: {json.dumps(session_context.get('current_fields', []))}\n\n"
            "Instructions:\n"
            "1. If the user provides a value to answer a previous question (e.g. an IFSC code, date of birth, name), "
            "identify which field key it updates.\n"
            "2. If the user answers a confirmation (e.g. 'Yes', 'Correct'), mark that field as confirmed.\n"
            "3. Ask clear, non-technical, one-at-a-time questions for the next missing or conflicting field.\n"
            "4. Return strict JSON with:\n"
            "   - 'assistant_reply': string (your message to display in chat)\n"
            "   - 'suggested_replies': list of 2-3 short strings for quick chips (e.g. ['Yes', 'No, change it'])\n"
            "   - 'updated_fields': list of objects [{'field_key': str, 'value': str, 'confirm': bool}]\n"
        )

        messages = [{"role": "system", "content": system_prompt}]
        for turn in conversation_history[-6:]: # Last 6 turns for context
            messages.append({"role": turn.get("role", "user"), "content": turn.get("message", "")})
        messages.append({"role": "user", "content": user_message})

        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            raw = response.choices[0].message.content
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Groq chat turn failed: {e}")
            raise e
