"""Main application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .database.models import Base
from .dashboard.routers import video_projects

# Dashboard paths
DASHBOARD_DIR = Path(__file__).parent / "dashboard"
TEMPLATES_DIR = DASHBOARD_DIR / "templates"
STATIC_DIR = DASHBOARD_DIR / "static"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Database setup
engine = create_engine(settings.database.url, echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting AI Content Manager...")

    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Ensure data directories exist
    for directory in [
        settings.video.assets_dir / "characters",
        settings.video.assets_dir / "backgrounds",
        settings.video.assets_dir / "music",
        settings.video.projects_dir / "voiceovers",
        settings.video.projects_dir / "videos",
    ]:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Data directories initialized")

    yield

    # Shutdown
    logger.info("Shutting down AI Content Manager...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Automated video production system for educational content",
    version="0.1.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(video_projects.router)

# Override the database dependency
app.dependency_overrides[video_projects.get_db] = get_db

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the dashboard UI."""
    template_path = TEMPLATES_DIR / "index.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(), status_code=200)
    return HTMLResponse(
        content="<h1>Dashboard not found</h1><p>Templates not configured.</p>",
        status_code=404
    )


@app.get("/api")
async def api_info():
    """API info endpoint."""
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Run the application."""
    import uvicorn

    uvicorn.run(
        "contentmanager.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
