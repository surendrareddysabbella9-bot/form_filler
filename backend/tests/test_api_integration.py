import pytest
import io
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db

@pytest.fixture(autouse=True)
async def initialize_test_database():
    await init_db()

@pytest.mark.asyncio
async def test_full_api_workflow_end_to_end():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health check
        health_res = await client.get("/api/health")
        assert health_res.status_code == 200
        assert health_res.json()["status"] == "online"

        # 2. Upload sample PDF template
        sample_pdf_bytes = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Length 75 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Full Name: ________ Date of Birth: ________) Tj\nET\nendstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
            b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n331\n%%EOF\n"
        )

        template_file = {"file": ("test_form.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        tpl_res = await client.post("/api/templates/upload", files=template_file)
        assert tpl_res.status_code == 201
        tpl_data = tpl_res.json()
        template_id = tpl_data["id"]
        assert len(tpl_data["fields"]) > 0

        # 3. Create Session
        sess_res = await client.post("/api/sessions", json={"template_id": template_id, "title": "Tax Filing 2026"})
        assert sess_res.status_code == 201
        session_data = sess_res.json()
        session_id = session_data["id"]

        # 4. Upload Supporting Document
        doc_files = [("files", ("identity_proof.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf"))]
        doc_res = await client.post("/api/documents/upload", data={"session_id": session_id}, files=doc_files)
        assert doc_res.status_code == 201
        docs = doc_res.json()
        assert len(docs) == 1

        # 5. Analyze & Map Session
        analyze_res = await client.post(f"/api/sessions/{session_id}/analyze")
        assert analyze_res.status_code == 200

        # 6. Chat with Assistant to provide missing IFSC code
        chat_res = await client.post(f"/api/sessions/{session_id}/chat", json={"message": "My IFSC code is HDFC0001234"})
        assert chat_res.status_code == 200
        chat_data = chat_res.json()
        assert "assistant_reply" in chat_data

        # 7. Check updated fields
        fields_res = await client.get(f"/api/sessions/{session_id}/fields")
        assert fields_res.status_code == 200
        fields = fields_res.json()

        # Confirm all required fields to allow generation
        for f in fields:
            if not f["current_value"]:
                await client.patch(
                    f"/api/sessions/{session_id}/fields/{f['field_id']}",
                    json={"current_value": "N/A" if f["field_type"] == "text" else "1990-01-01", "confirm": True}
                )

        # 8. Generate Completed Document
        gen_res = await client.post(f"/api/sessions/{session_id}/generate", json={"format": "pdf"})
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert "download_url" in gen_data

        # 9. Download Generated Document
        down_res = await client.get(f"/api/sessions/{session_id}/download")
        assert down_res.status_code == 200
        assert len(down_res.content) > 0
