"""Main application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .database.models import Base
from .dashboard.routers import video_projects

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

# Override the dependency in the router
video_projects.get_db = get_db

# Include routers
app.include_router(video_projects.router)


@app.get("/")
async def root():
    """Root endpoint."""
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
