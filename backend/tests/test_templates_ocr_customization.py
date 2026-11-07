import pytest
import io
import base64
from PIL import Image
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db

@pytest.fixture(autouse=True)
async def ensure_db():
    await init_db()

def create_sample_png_bytes(text: str = "Form") -> bytes:
    """Creates a valid 200x100 white PNG in memory."""
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_sample_jpg_bytes() -> bytes:
    """Creates a valid 200x100 white JPEG in memory."""
    img = Image.new("RGB", (200, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

@pytest.mark.asyncio
async def test_image_template_upload_png_and_jpg():
    """Verifies that JPG and PNG image templates are accepted and converted into fillable templates."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload PNG template
        png_bytes = create_sample_png_bytes()
        res_png = await client.post(
            "/api/templates/upload",
            files={"file": ("blank_form.png", io.BytesIO(png_bytes), "image/png")}
        )
        assert res_png.status_code == 201
        data_png = res_png.json()
        assert data_png["file_type"] == ".png"
        assert len(data_png["fields"]) > 0

        # 2. Upload JPG template
        jpg_bytes = create_sample_jpg_bytes()
        res_jpg = await client.post(
            "/api/templates/upload",
            files={"file": ("application.jpg", io.BytesIO(jpg_bytes), "image/jpeg")}
        )
        assert res_jpg.status_code == 201
        data_jpg = res_jpg.json()
        assert data_jpg["file_type"] == ".jpg"
        assert len(data_jpg["fields"]) > 0

@pytest.mark.asyncio
async def test_pdf_template_coordinate_detection():
    """Verifies that PDF and image analysis returns bounding_box coordinate dictionaries."""
    sample_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 75 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Full Name: ________ Date of Birth: ________) Tj\nET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n331\n%%EOF\n"
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post(
            "/api/templates/upload",
            files={"file": ("form_with_coords.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )
        assert res.status_code == 201
        fields = res.json()["fields"]
        assert len(fields) > 0
        # Check that bounding box exists or is captured
        has_coord_field = any(f.get("bounding_box") is not None for f in fields)
        assert has_coord_field

@pytest.mark.asyncio
async def test_font_color_customization_and_digital_signature():
    """Verifies font family, size, color customization and digital signature lifecycle."""
    sample_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 65 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Full Name: ________ Signature: ________) Tj\nET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n320\n%%EOF\n"
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Upload Template
        tpl_res = await client.post(
            "/api/templates/upload",
            files={"file": ("cert_form.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )
        tpl_id = tpl_res.json()["id"]

        # 2. Create Session
        sess_res = await client.post("/api/sessions", json={"template_id": tpl_id, "title": "Custom Style Form"})
        sess_id = sess_res.json()["id"]

        # 3. Save digital signature (draw/type/upload data URL)
        sig_png_bytes = create_sample_png_bytes()
        sig_data_url = f"data:image/png;base64,{base64.b64encode(sig_png_bytes).decode()}"
        sig_res = await client.post(f"/api/sessions/{sess_id}/signature", json={"signature_data": sig_data_url})
        assert sig_res.status_code == 200
        assert sig_res.json()["status"] == "success"

        # 4. Fetch signature
        fetch_sig = await client.get(f"/api/sessions/{sess_id}/signature")
        assert fetch_sig.status_code == 200
        assert fetch_sig.headers["content-type"] == "image/png"

        # 5. Update Style Preferences
        style_res = await client.patch(
            f"/api/sessions/{sess_id}/style",
            json={"font_family": "Courier", "font_size": 12.0, "text_color": "#1e3a8a"}
        )
        assert style_res.status_code == 200
        assert style_res.json()["style_preferences"]["font_family"] == "Courier"

        # 6. Populate a field
        fields_res = await client.get(f"/api/sessions/{sess_id}/fields")
        f_list = fields_res.json()
        for f in f_list:
            await client.patch(
                f"/api/sessions/{sess_id}/fields/{f['field_id']}",
                json={"current_value": "Jane Doe", "confirm": True}
            )

        # 7. Generate Document with custom font, size, color and signature
        gen_res = await client.post(
            f"/api/sessions/{sess_id}/generate",
            json={
                "format": "pdf",
                "font_family": "Times-Roman",
                "font_size": 11.0,
                "text_color": "#1e3a8a",
                "signature_data": sig_data_url,
            }
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert gen_data["format"] == "pdf"

        # 8. Download generated document
        dl_res = await client.get(f"/api/sessions/{sess_id}/download")
        assert dl_res.status_code == 200
        assert len(dl_res.content) > 1000

        # 9. Delete signature
        del_sig = await client.delete(f"/api/sessions/{sess_id}/signature")
        assert del_sig.status_code == 200
