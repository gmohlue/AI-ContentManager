"""SQLAlchemy database models."""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

from ..core.content.video_pipeline.models import (
    CharacterRole,
    ContextStyle,
    VideoProjectStatus,
)

Base = declarative_base()


class Character(Base):
    """User-defined character for videos."""

    __tablename__ = "characters"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    role = Column(Enum(CharacterRole), nullable=False)
    tenant_id = Column(Integer, nullable=True)  # Multi-tenant ready
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    assets = relationship("CharacterAsset", back_populates="character")


class CharacterAsset(Base):
    """Character pose image uploaded by user."""

    __tablename__ = "character_assets"

    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    pose = Column(String(50), nullable=False)  # "standing", "thinking", "pointing"
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    tenant_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    character = relationship("Character", back_populates="assets")


class BackgroundAsset(Base):
    """Background image for videos."""

    __tablename__ = "background_assets"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    context_style = Column(Enum(ContextStyle), nullable=True)
    file_path = Column(String(500), nullable=False)
    tenant_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MusicAsset(Base):
    """Background music track."""

    __tablename__ = "music_assets"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    context_style = Column(Enum(ContextStyle), nullable=True)
    file_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, nullable=False)
    tenant_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoProject(Base):
    """Main video project entity."""

    __tablename__ = "video_projects"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, nullable=True)

    # Content
    title = Column(String(200), nullable=False)
    topic = Column(String(500), nullable=False)
    context_style = Column(Enum(ContextStyle), nullable=False)
    document_id = Column(Integer, nullable=True)

    # Characters
    questioner_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    explainer_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    # Script
    script_json = Column(JSON, nullable=True)
    takeaway = Column(Text, nullable=True)

    # Audio
    background_music_id = Column(Integer, ForeignKey("music_assets.id"), nullable=True)
    voiceover_path = Column(String(500), nullable=True)

    # Output
    output_path = Column(String(500), nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Workflow
    status = Column(Enum(VideoProjectStatus), default=VideoProjectStatus.DRAFT)
    error_message = Column(Text, nullable=True)

    # Review tracking
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    questioner = relationship("Character", foreign_keys=[questioner_id])
    explainer = relationship("Character", foreign_keys=[explainer_id])
    background_music = relationship("MusicAsset")
    scenes = relationship("VideoScene", back_populates="project")


class VideoScene(Base):
    """Individual scene in a video project."""

    __tablename__ = "video_scenes"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("video_projects.id"), nullable=False)
    scene_number = Column(Integer, nullable=False)

    # Content
    speaker_role = Column(Enum(CharacterRole), nullable=False)
    line = Column(Text, nullable=False)
    pose = Column(String(50), nullable=False)

    # Audio (populated after voiceover generation)
    voiceover_path = Column(String(500), nullable=True)
    start_time = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Visual
    background_id = Column(Integer, ForeignKey("background_assets.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("VideoProject", back_populates="scenes")
    background = relationship("BackgroundAsset")
