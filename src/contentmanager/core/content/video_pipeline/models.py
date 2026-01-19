"""Pydantic models for the video pipeline."""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ContextStyle(str, Enum):
    """Content style/theme for videos."""

    MOTIVATION = "motivation"
    FINANCE = "finance"
    TECH = "tech"
    EDUCATIONAL = "educational"


class CharacterRole(str, Enum):
    """Role a character plays in the dialogue."""

    QUESTIONER = "questioner"
    EXPLAINER = "explainer"


class VideoProjectStatus(str, Enum):
    """Status of a video project through the pipeline."""

    DRAFT = "draft"
    APPROVED = "approved"
    AUDIO_READY = "audio_ready"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class DialogueLine(BaseModel):
    """A single line of dialogue in the script."""

    speaker_role: CharacterRole
    speaker_name: str
    line: str
    pose: str = "standing"
    scene_number: int


class DialogueScript(BaseModel):
    """Complete dialogue script for a video."""

    topic: str
    context_style: ContextStyle
    lines: list[DialogueLine]
    takeaway: str
    target_duration_seconds: int = 45


class AudioSegment(BaseModel):
    """Audio segment metadata."""

    scene_number: int
    speaker_role: CharacterRole
    file_path: str
    duration_seconds: float
    start_time: float = 0.0


class VoiceoverResult(BaseModel):
    """Result of voiceover generation."""

    segments: list[AudioSegment]
    combined_audio_path: str
    total_duration_seconds: float


class RenderResult(BaseModel):
    """Result of video rendering."""

    output_path: str
    duration_seconds: float
    width: int
    height: int
    file_size_bytes: int
    rendered_at: datetime = Field(default_factory=datetime.utcnow)


class VideoProjectCreate(BaseModel):
    """Request model for creating a video project."""

    title: str
    topic: str
    context_style: ContextStyle
    questioner_id: int
    explainer_id: int
    background_music_id: int | None = None
    document_id: int | None = None


class VideoProjectResponse(BaseModel):
    """Response model for a video project."""

    id: int
    title: str
    topic: str
    context_style: ContextStyle
    status: VideoProjectStatus
    script_json: dict | None = None
    takeaway: str | None = None
    voiceover_path: str | None = None
    output_path: str | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
