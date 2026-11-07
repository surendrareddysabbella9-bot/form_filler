import pytest
import io
import secrets
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import init_db, get_db
from app.models.entities import GuestSession, FormTemplate, FormSession, UploadedDocument
from app.services.session_manager import (
    create_new_guest_session,
    cleanup_expired_guest_sessions,
    delete_guest_session,
    get_session_upload_dir,
    get_session_generated_dir,
)
from sqlalchemy.future import select

@pytest.fixture(autouse=True)
async def ensure_db():
    await init_db()

@pytest.mark.asyncio
async def test_guest_session_token_entropy_and_uniqueness():
    """Verifies that guest session tokens are cryptographically unpredictable and unique."""
    tokens = set()
    async for db in get_db():
        for _ in range(25):
            s = await create_new_guest_session(db)
            assert len(s.id) >= 32
            assert s.id not in tokens
            tokens.add(s.id)
            # Verify directories exist
            up_dir = get_session_upload_dir(s.id)
            gen_dir = get_session_generated_dir(s.id)
            assert up_dir.exists()
            assert gen_dir.exists()
            # Clean up
            await delete_guest_session(s.id, db)
        break

@pytest.mark.asyncio
async def test_guest_session_http_only_cookie_and_header():
    """Verifies that requests automatically receive secure HTTP-only cookies and X-Guest-Session-ID headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/guest/session")
        assert res.status_code == 200
        data = res.json()
        assert "session_id" in data
        assert data["policy"]["mode"] == "temporary_guest_session"
        assert data["policy"]["idle_timeout_hours"] == 1
        assert data["policy"]["max_lifetime_hours"] == 24

        # Check set-cookie header contains guest_session_id and HttpOnly
        set_cookie = res.headers.get("set-cookie", "")
        assert "guest_session_id=" in set_cookie
        assert "httponly" in set_cookie.lower()

        # Check custom header
        guest_header = res.headers.get("x-guest-session-id")
        assert guest_header == data["session_id"]

@pytest.mark.asyncio
async def test_guest_session_isolation():
    """Verifies that two guest sessions are strictly isolated from one another."""
    transport = ASGITransport(app=app)
    
    sample_pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 50 >>\nstream\nBT\n/F1 12 Tf\n100 700 Td\n(Name: ________) Tj\nET\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n300\n%%EOF\n"
    )

    # Client A
    async with AsyncClient(transport=transport, base_url="http://test") as client_a:
        res_a = await client_a.get("/api/guest/session")
        session_id_a = res_a.json()["session_id"]

        # Client A uploads template
        tpl_res_a = await client_a.post(
            "/api/templates/upload",
            files={"file": ("form_a.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
        )
        assert tpl_res_a.status_code == 201
        tpl_a_id = tpl_res_a.json()["id"]

        # Client A creates form session
        form_res_a = await client_a.post("/api/sessions", json={"template_id": tpl_a_id, "title": "Session A"})
        assert form_res_a.status_code == 201
        form_a_id = form_res_a.json()["id"]

        # Client A lists forms
        list_a = await client_a.get("/api/sessions")
        assert any(s["id"] == form_a_id for s in list_a.json())

    # Client B (completely independent session)
    async with AsyncClient(transport=transport, base_url="http://test") as client_b:
        res_b = await client_b.get("/api/guest/session")
        session_id_b = res_b.json()["session_id"]
        assert session_id_b != session_id_a

        # Client B cannot view Client A's form session
        get_fail = await client_b.get(f"/api/sessions/{form_a_id}")
        assert get_fail.status_code == 404

        # Client B cannot see Client A's template
        tpl_fail = await client_b.get(f"/api/templates/{tpl_a_id}")
        assert tpl_fail.status_code == 404

        # Client B's session list does NOT contain Client A's form
        list_b = await client_b.get("/api/sessions")
        assert all(s["id"] != form_a_id for s in list_b.json())

@pytest.mark.asyncio
async def test_manual_guest_session_deletion():
    """Verifies that manual deletion immediately destroys all database records and disk directories."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sess_init = await client.get("/api/guest/session")
        guest_id = sess_init.json()["session_id"]

        # Verify directories exist
        up_dir = get_session_upload_dir(guest_id)
        assert up_dir.exists()

        # Delete session
        del_res = await client.delete("/api/guest/session")
        assert del_res.status_code == 200
        del_data = del_res.json()
        assert del_data["status"] == "deleted"

        # Verify disk directory was purged
        assert not up_dir.exists()

        # Verify database record deleted
        async for db in get_db():
            stmt = select(GuestSession).where(GuestSession.id == guest_id)
            res = await db.execute(stmt)
            assert res.scalar_one_or_none() is None
            break

@pytest.mark.asyncio
async def test_automatic_expiration_and_cleanup():
    """Verifies that expired sessions (idle > 1h or created > 24h) are purged by cleanup."""
    async for db in get_db():
        # Create an expired session (accessed 2 hours ago)
        expired_token = secrets.token_urlsafe(32)
        past_time = datetime.now(timezone.utc) - timedelta(hours=2)
        expired_session = GuestSession(
            id=expired_token,
            created_at=past_time,
            last_accessed_at=past_time,
            idle_timeout_seconds=3600,
            max_lifetime_seconds=86400,
            is_active=True,
        )
        db.add(expired_session)
        await db.commit()

        # Create dummy folder
        up_dir = get_session_upload_dir(expired_token)
        assert up_dir.exists()

        # Run cleanup
        cleaned_count = await cleanup_expired_guest_sessions(db)
        assert cleaned_count >= 1

        # Check directory purged
        assert not up_dir.exists()

        # Check DB record gone
        stmt = select(GuestSession).where(GuestSession.id == expired_token)
        res = await db.execute(stmt)
        assert res.scalar_one_or_none() is None
        break
