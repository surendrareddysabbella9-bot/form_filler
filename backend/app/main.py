import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.core.config import settings
from app.core.database import init_db, get_db
from app.api.api_router import api_router
from app.services.session_manager import cleanup_expired_guest_sessions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("form_filler")

async def _periodic_session_cleanup():
    """Background task running every 10 minutes to auto-purge expired guest sessions."""
    while True:
        try:
            await asyncio.sleep(600)
            async for db in get_db():
                cleaned = await cleanup_expired_guest_sessions(db)
                if cleaned:
                    logger.info(f"Periodic cleanup purged {cleaned} expired guest session(s).")
                break
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.warning(f"Background session cleanup error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing database connection and schema...")
    await init_db()

    # Initial purge of any previously expired sessions
    try:
        async for db in get_db():
            cleaned = await cleanup_expired_guest_sessions(db)
            if cleaned:
                logger.info(f"Startup cleanup purged {cleaned} stale guest session(s).")
            break
    except Exception as e:
        logger.warning(f"Startup session cleanup note: {e}")

    # Launch background cleanup task
    cleanup_task = asyncio.create_task(_periodic_session_cleanup())
    logger.info(f"{settings.APP_NAME} started successfully.")
    yield
    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Generic AI-powered document understanding and automated form-completion platform.",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Mount frontend production build
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists() and (frontend_dist / "index.html").exists():
    assets_dir = frontend_dist / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not Found")
        target_file = frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(frontend_dist / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs_url": "/docs",
            "api_prefix": settings.API_V1_PREFIX,
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
