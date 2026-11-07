import httpx
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000/api"
SAMPLE_DIR = Path("../sample_test_documents")

def test_live_form_filling():
    print("=== STARTING LIVE END-TO-END WORKFLOW TEST ===")

    # 1. Health Check
    res = httpx.get(f"{BASE_URL}/health")
    print("1. Health Check:", res.json())
    assert res.status_code == 200

    # 2. Upload Template Form
    tpl_path = SAMPLE_DIR / "blank_onboarding_form.pdf"
    with open(tpl_path, "rb") as f:
        res = httpx.post(f"{BASE_URL}/templates/upload", files={"file": (tpl_path.name, f, "application/pdf")})
    assert res.status_code == 201
    tpl_data = res.json()
    template_id = tpl_data["id"]
    print(f"2. Template Uploaded: ID={template_id}, Detected Fields={len(tpl_data['fields'])}")

    # 3. Create Session
    res = httpx.post(f"{BASE_URL}/sessions", json={"template_id": template_id, "title": "David Miller Onboarding Form"})
    assert res.status_code == 201
    session_data = res.json()
    session_id = session_data["id"]
    print(f"3. Session Created: ID={session_id}")

    # 4. Upload Supporting Documents
    id_path = SAMPLE_DIR / "david_identity_card.pdf"
    sal_path = SAMPLE_DIR / "david_salary_slip.pdf"
    files = [
        ("files", (id_path.name, open(id_path, "rb"), "application/pdf")),
        ("files", (sal_path.name, open(sal_path, "rb"), "application/pdf")),
    ]
    res = httpx.post(f"{BASE_URL}/documents/upload", data={"session_id": session_id}, files=files)
    assert res.status_code == 201
    print(f"4. Supporting Documents Attached: {len(res.json())} files")

    # 5. Trigger AI Mapping (Groq live inference)
    print("5. Invoking AI Mapping Engine via Groq API...")
    res = httpx.post(f"{BASE_URL}/sessions/{session_id}/analyze")
    assert res.status_code == 200
    metrics = res.json()["metrics"]
    print(f"   AI Mapping Results: Extracted={metrics['extracted_fields']}, Missing={metrics['missing_fields']}, Conflicts={metrics['conflicting_fields']}, Completion={metrics['completion_percentage']}%")

    # 6. Inspect Fields
    res = httpx.get(f"{BASE_URL}/sessions/{session_id}/fields")
    fields = res.json()
    print("\n--- POPULATED FIELDS ---")
    for f in fields:
        print(f"  • {f['label']} ({f['field_key']}): {f['current_value']} [{f['validation_status']}] (Source: {f['source_document_name'] or 'N/A'})")

    # 7. Test Chatbot Assistant: Supply missing Bank IFSC Code
    print("\n7. Conversing with AI Assistant...")
    chat_payload = {"message": "Here is my bank IFSC code: HDFC0001234"}
    res = httpx.post(f"{BASE_URL}/sessions/{session_id}/chat", json=chat_payload)
    assert res.status_code == 200
    chat_turn = res.json()
    print(f"   User: 'Here is my bank IFSC code: HDFC0001234'")
    print(f"   Assistant: {chat_turn['assistant_reply']}")
    print(f"   Updated Fields: {chat_turn['updated_fields']}")

    # 8. Generate Completed Document
    print("\n8. Generating Completed Document...")
    res = httpx.post(f"{BASE_URL}/sessions/{session_id}/generate", json={"format": "pdf"})
    assert res.status_code == 200
    gen_data = res.json()
    print(f"   Document Generated: {gen_data['filename']} ({gen_data['file_size_bytes']} bytes)")

    # 9. Download Document
    res = httpx.get(f"{BASE_URL}/sessions/{session_id}/download")
    assert res.status_code == 200
    print(f"9. Document Download Verified: {len(res.content)} bytes received with Content-Type={res.headers.get('content-type')}")
    print("\n=== LIVE END-TO-END TEST SUCCEEDED 100%! ===")

if __name__ == "__main__":
    test_live_form_filling()
