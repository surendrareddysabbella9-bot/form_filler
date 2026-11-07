import pytest
import asyncio
from pathlib import Path
from app.services.validation.validator import FieldValidator
from app.services.ai.mock_provider import MockAIProvider
from app.services.templates.template_analyzer import TemplateAnalyzer

def test_field_validator_success():
    # Valid email
    status, err = FieldValidator.validate_field("email", "Email Address", "email", "john.doe@example.com", True)
    assert status == "extracted"
    assert err is None

    # Valid PAN
    status, err = FieldValidator.validate_field("pan_number", "PAN", "text", "ABCDE1234F", True)
    assert status == "extracted"
    assert err is None

    # Valid IFSC
    status, err = FieldValidator.validate_field("bank_ifsc_code", "IFSC", "text", "HDFC0001234", True)
    assert status == "extracted"
    assert err is None

    # Valid Date
    status, err = FieldValidator.validate_field("date_of_birth", "Date of Birth", "date", "1992-05-14", True)
    assert status == "extracted"
    assert err is None

def test_field_validator_failures():
    # Invalid email
    status, err = FieldValidator.validate_field("email", "Email", "email", "not-an-email", True)
    assert status == "invalid"
    assert "Invalid email" in err

    # Invalid PAN
    status, err = FieldValidator.validate_field("pan_number", "PAN", "text", "12345ABCDE", True)
    assert status == "invalid"
    assert "PAN must follow format" in err

    # Missing mandatory
    status, err = FieldValidator.validate_field("full_name", "Full Name", "text", "", True)
    assert status == "missing"
    assert "Mandatory" in err

    # Conditional spouse validation
    status, err = FieldValidator.validate_field(
        "spouse_name", "Spouse Name", "text", "", False, {"marital_status": "Married"}
    )
    assert status == "missing"
    assert "Spouse name is required" in err

@pytest.mark.asyncio
async def test_ai_mock_mapping_and_conflicts():
    provider = MockAIProvider()

    # Two documents with conflicting dates of birth
    docs = [
        {
            "document_id": "doc_1",
            "document_name": "Aadhaar_Card.pdf",
            "page": 1,
            "text": "Government of India. Name: Rahul Sharma. Date of Birth: 14/05/1992. PAN: ABCDE1234F. Email: rahul@example.com."
        },
        {
            "document_id": "doc_2",
            "document_name": "Birth_Certificate.pdf",
            "page": 1,
            "text": "Municipal Corporation. Date of Birth: 24/05/1992. Applicant Name: Rahul Sharma."
        }
    ]

    template_fields = [
        {"field_key": "full_name", "label": "Full Name", "required": True},
        {"field_key": "date_of_birth", "label": "Date of Birth", "required": True},
        {"field_key": "pan_number", "label": "PAN", "required": True},
        {"field_key": "email", "label": "Email", "required": True},
        {"field_key": "bank_ifsc_code", "label": "Bank IFSC Code", "required": True},
    ]

    mappings = await provider.map_fields(docs, template_fields)
    mapped_dict = {m["field_key"]: m for m in mappings}

    # Verify full name extracted
    assert mapped_dict["full_name"]["proposed_value"] == "Rahul Sharma"
    assert mapped_dict["full_name"]["status"] in ["extracted", "needs_review"]

    # Verify PAN extracted
    assert mapped_dict["pan_number"]["proposed_value"] == "ABCDE1234F"

    # Verify conflict detected for date of birth!
    dob_mapping = mapped_dict["date_of_birth"]
    assert dob_mapping["status"] == "conflicting"
    assert len(dob_mapping["candidates"]) == 2

    # Verify IFSC is missing
    assert mapped_dict["bank_ifsc_code"]["status"] == "missing"

@pytest.mark.asyncio
async def test_ai_conversational_turn():
    provider = MockAIProvider()

    context = {
        "missing_fields": [{"field_key": "bank_ifsc_code", "label": "Bank IFSC Code"}],
        "conflicting_fields": [],
        "current_fields": []
    }

    # User answers with IFSC code
    result = await provider.chat_turn([], context, "My bank IFSC code is HDFC0001234")
    assert any(u["field_key"] == "bank_ifsc_code" for u in result["updated_fields"])
    assert "HDFC0001234" in result["assistant_reply"]
