import re
import logging
from typing import List, Dict, Any
from app.services.ai.base import AIProvider

logger = logging.getLogger(__name__)

class MockAIProvider(AIProvider):
    """
    Deterministic rule-based extractor and conversational engine.
    Used when GROQ_API_KEY is not configured or in automated tests.
    Extracts real facts from text using regex heuristics.
    """

    async def map_fields(
        self,
        extracted_documents: List[Dict[str, Any]],
        template_fields: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        mappings = []

        # Entity extraction patterns across documents
        patterns = {
            "email": (r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", 0.98),
            "phone_number": (r"(?:\+91[\-\s]?)?[6-9]\d{9}|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", 0.95),
            "date_of_birth": (r"\b(?:\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{4}[-/.]\d{1,2}[-/.]\d{1,2})\b", 0.92),
            "pan_number": (r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", 0.99),
            "national_id": (r"\b\d{4}\s\d{4}\s\d{4}\b|\b\d{12}\b|\b\d{3}-\d{2}-\d{4}\b", 0.96),
            "annual_income": (r"(?:(?:₹|Rs\.?|INR|\$)\s*([\d,]+(?:\.\d{2})?))|(?:(?:salary|compensation|income|ctc)\s*[:=-]?\s*(?:₹|Rs\.?|INR|\$)?\s*([\d,]+))", 0.90),
            "bank_account_number": (r"(?:account(?:\s*no\.?)?|a/c)\s*[:=-]?\s*([0-9]{9,18})\b", 0.93),
            "bank_ifsc_code": (r"\b[A-Z]{4}0[A-Z0-9]{6}\b", 0.98),
            "postal_code": (r"\b(?:[1-9][0-9]{5}|\d{5}(?:-\d{4})?)\b", 0.92),
        }

        # Scan each document
        for f in template_fields:
            key = f["field_key"]
            found_candidates = []

            for doc in extracted_documents:
                text = doc.get("text", "")
                doc_name = doc.get("document_name", "Supporting Document")
                doc_id = doc.get("document_id")
                page = doc.get("page", 1)

                if key in patterns:
                    regex, conf = patterns[key]
                    matches = re.findall(regex, text, re.IGNORECASE)
                    for m in matches:
                        val = m if isinstance(m, str) else (m[0] or m[1])
                        val = val.strip()
                        if val:
                            found_candidates.append({
                                "val": val,
                                "source_doc_name": doc_name,
                                "source_doc_id": doc_id,
                                "source_page": page,
                                "confidence": conf
                            })

                # Name extraction heuristics (look for "Name: John Doe" or PAN/Aadhaar name pattern)
                elif key in ["full_name", "first_name"]:
                    name_match = re.search(r"(?:applicant\s+name|employee\s+name|name\s+of\s+applicant|name)\s*[:=-]\s*([A-Za-z\s]{3,35}?)(?=[.,\n\r]|$)", text, re.IGNORECASE)
                    if name_match:
                        raw_name = name_match.group(1).strip()
                        # Avoid matching single words like "Of"
                        if len(raw_name.split()) >= 1 and len(raw_name) >= 3:
                            found_candidates.append({
                                "val": raw_name.title(),
                                "source_doc_name": doc_name,
                                "source_doc_id": doc_id,
                                "source_page": page,
                                "confidence": 0.88
                            })

                # Address extraction heuristics
                elif key == "address":
                    addr_match = re.search(r"(?:address|residence)\s*[:=-]\s*([^\n\r]{10,80}?)(?=[;\n\r]|$)", text, re.IGNORECASE)
                    if addr_match:
                        found_candidates.append({
                            "val": addr_match.group(1).strip(),
                            "source_doc_name": doc_name,
                            "source_doc_id": doc_id,
                            "source_page": page,
                            "confidence": 0.85
                        })

            if len(found_candidates) == 1:
                c = found_candidates[0]
                mappings.append({
                    "field_key": key,
                    "proposed_value": c["val"],
                    "source_document_id": c["source_doc_id"],
                    "source_document_name": c["source_doc_name"],
                    "source_page": c["source_page"],
                    "confidence": c["confidence"],
                    "status": "extracted" if c["confidence"] >= 0.9 else "needs_review",
                    "reason": f"Extracted via pattern match from {c['source_doc_name']}",
                    "candidates": []
                })
            elif len(found_candidates) > 1:
                # Check if values differ (conflict!)
                distinct_vals = list({c["val"] for c in found_candidates})
                if len(distinct_vals) > 1:
                    mappings.append({
                        "field_key": key,
                        "proposed_value": found_candidates[0]["val"],
                        "source_document_id": found_candidates[0]["source_doc_id"],
                        "source_document_name": found_candidates[0]["source_doc_name"],
                        "source_page": found_candidates[0]["source_page"],
                        "confidence": 0.70,
                        "status": "conflicting",
                        "reason": f"Conflicting values detected across {len(found_candidates)} documents",
                        "candidates": [
                            {
                                "value": c["val"],
                                "source_document_id": c["source_doc_id"],
                                "source_document_name": c["source_doc_name"],
                                "source_page": c["source_page"],
                                "confidence": c["confidence"]
                            }
                            for c in found_candidates
                        ]
                    })
                else:
                    c = found_candidates[0]
                    mappings.append({
                        "field_key": key,
                        "proposed_value": c["val"],
                        "source_document_id": c["source_doc_id"],
                        "source_document_name": c["source_doc_name"],
                        "source_page": c["source_page"],
                        "confidence": c["confidence"],
                        "status": "extracted",
                        "reason": f"Extracted with cross-document confirmation",
                        "candidates": []
                    })
            else:
                mappings.append({
                    "field_key": key,
                    "proposed_value": None,
                    "source_document_id": None,
                    "source_document_name": None,
                    "source_page": None,
                    "confidence": 0.0,
                    "status": "missing",
                    "reason": "Not found in uploaded supporting documents",
                    "candidates": []
                })

        return mappings

    async def chat_turn(
        self,
        conversation_history: List[Dict[str, str]],
        session_context: Dict[str, Any],
        user_message: str
    ) -> Dict[str, Any]:
        msg_clean = user_message.strip()
        updated_fields = []
        assistant_reply = ""
        suggested_replies = []

        missing = session_context.get("missing_fields", [])
        conflicting = session_context.get("conflicting_fields", [])

        # 1. Handle user confirming a value
        if msg_clean.lower() in ["yes", "correct", "confirm", "confirmed", "looks good"]:
            unconfirmed = [f for f in session_context.get("current_fields", []) if f.get("confirmation_status") != "confirmed" and f.get("current_value")]
            if unconfirmed:
                target = unconfirmed[0]
                updated_fields.append({"field_key": target["field_key"], "value": target["current_value"], "confirm": True})
                assistant_reply = f"Thank you! I have confirmed your **{target['label']}** ({target['current_value']})."
            else:
                assistant_reply = "All extracted fields have already been confirmed!"

        # 2. Check if user provided an IFSC code pattern
        elif re.search(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", msg_clean, re.IGNORECASE):
            ifsc = re.search(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", msg_clean, re.IGNORECASE).group(0).upper()
            updated_fields.append({"field_key": "bank_ifsc_code", "value": ifsc, "confirm": True})
            assistant_reply = f"Got it! Bank IFSC Code **{ifsc}** has been validated and added to your form."

        # 3. Check if user provided an email
        elif re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", msg_clean):
            email = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", msg_clean).group(0)
            updated_fields.append({"field_key": "email", "value": email, "confirm": True})
            assistant_reply = f"Thank you! Updated your Email Address to **{email}**."

        # 4. Check if user provided a phone number
        elif re.search(r"\b\d{10}\b", msg_clean):
            phone = re.search(r"\b\d{10}\b", msg_clean).group(0)
            updated_fields.append({"field_key": "phone_number", "value": phone, "confirm": True})
            assistant_reply = f"Thank you! Updated your Phone Number to **{phone}**."

        # 5. User provides direct answer to a missing field
        elif missing:
            next_missing = missing[0]
            updated_fields.append({"field_key": next_missing["field_key"], "value": msg_clean, "confirm": True})
            assistant_reply = f"Great! I have saved **{msg_clean}** for your {next_missing['label']}."
        else:
            assistant_reply = f"I received your message: \"{msg_clean}\". All required fields currently have values. You can review them in the preview or proceed to final generation!"

        # Suggest next question if fields still missing
        remaining_missing = [m for m in missing if not any(u["field_key"] == m["field_key"] for u in updated_fields)]
        if remaining_missing:
            next_field = remaining_missing[0]
            assistant_reply += f"\n\nCould you please provide your **{next_field['label']}**?"
            suggested_replies = ["Not applicable", "Skip for now"]
        elif conflicting:
            c = conflicting[0]
            assistant_reply += f"\n\nPlease review the conflict on **{c['label']}** in the preview pane."

        return {
            "assistant_reply": assistant_reply,
            "suggested_replies": suggested_replies,
            "updated_fields": updated_fields
        }
