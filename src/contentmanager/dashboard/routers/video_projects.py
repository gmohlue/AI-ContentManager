"""FastAPI router for video project endpoints."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ...core.content.video_pipeline.models import (
    ContextStyle,
    VideoProjectCreate,
    VideoProjectResponse,
    VideoProjectStatus,
)
from ...database.repositories.video_project import (
    VideoProjectRepository,
    CharacterRepository,
    AssetRepository,
)

router = APIRouter(prefix="/api/video", tags=["video"])


# Dependency placeholder - replace with actual database session dependency
def get_db() -> Session:
    """Get database session dependency."""
    raise NotImplementedError("Database session dependency not configured")


# =============================================================================
# Character Endpoints
# =============================================================================


@router.post("/characters")
async def create_character(
    name: str,
    role: str,
    db: Session = Depends(get_db),
):
    """Create a new character."""
    repo = CharacterRepository(db)
    character = repo.create(name=name, role=role)
    return {"id": character.id, "name": character.name, "role": character.role}


@router.get("/characters")
async def list_characters(db: Session = Depends(get_db)):
    """List all characters."""
    repo = CharacterRepository(db)
    characters = repo.list_characters()
    return [
        {"id": c.id, "name": c.name, "role": c.role, "is_active": c.is_active}
        for c in characters
    ]


@router.post("/characters/{character_id}/assets")
async def upload_character_asset(
    character_id: int,
    pose: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a pose image for a character."""
    repo = CharacterRepository(db)
    character = repo.get_by_id(character_id)

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    # TODO: Save file using AssetManager and get path
    file_path = f"data/assets/characters/{character_id}/{pose}.png"
    file_size = 0  # TODO: Get actual file size

    asset = repo.add_asset(
        character_id=character_id,
        pose=pose,
        file_path=file_path,
        file_size_bytes=file_size,
    )

    return {"id": asset.id, "pose": asset.pose, "file_path": asset.file_path}


@router.delete("/characters/{character_id}/assets/{asset_id}")
async def delete_character_asset(
    character_id: int,
    asset_id: int,
    db: Session = Depends(get_db),
):
    """Delete a character pose asset."""
    repo = CharacterRepository(db)
    deleted = repo.delete_asset(asset_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")

    return {"status": "deleted"}


# =============================================================================
# Background Endpoints
# =============================================================================


@router.post("/backgrounds")
async def upload_background(
    name: str,
    file: UploadFile = File(...),
    context_style: ContextStyle | None = None,
    db: Session = Depends(get_db),
):
    """Upload a background image."""
    repo = AssetRepository(db)

    # TODO: Save file using AssetManager and get path
    file_path = f"data/assets/backgrounds/{name}.png"

    asset = repo.create_background(
        name=name,
        file_path=file_path,
        context_style=context_style.value if context_style else None,
    )

    return {"id": asset.id, "name": asset.name, "file_path": asset.file_path}


@router.get("/backgrounds")
async def list_backgrounds(
    context_style: ContextStyle | None = None,
    db: Session = Depends(get_db),
):
    """List background assets."""
    repo = AssetRepository(db)
    backgrounds = repo.list_backgrounds(
        context_style=context_style.value if context_style else None
    )
    return [
        {"id": b.id, "name": b.name, "context_style": b.context_style}
        for b in backgrounds
    ]


@router.delete("/backgrounds/{background_id}")
async def delete_background(
    background_id: int,
    db: Session = Depends(get_db),
):
    """Delete a background asset."""
    repo = AssetRepository(db)
    deleted = repo.delete_background(background_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Background not found")

    return {"status": "deleted"}


# =============================================================================
# Music Endpoints
# =============================================================================


@router.post("/music")
async def upload_music(
    name: str,
    file: UploadFile = File(...),
    context_style: ContextStyle | None = None,
    db: Session = Depends(get_db),
):
    """Upload a music track."""
    repo = AssetRepository(db)

    # TODO: Save file using AssetManager and get path/duration
    file_path = f"data/assets/music/{name}.mp3"
    duration_seconds = 0.0  # TODO: Get actual duration

    asset = repo.create_music(
        name=name,
        file_path=file_path,
        duration_seconds=duration_seconds,
        context_style=context_style.value if context_style else None,
    )

    return {"id": asset.id, "name": asset.name, "duration_seconds": asset.duration_seconds}


@router.get("/music")
async def list_music(
    context_style: ContextStyle | None = None,
    db: Session = Depends(get_db),
):
    """List music assets."""
    repo = AssetRepository(db)
    music = repo.list_music(
        context_style=context_style.value if context_style else None
    )
    return [
        {"id": m.id, "name": m.name, "duration_seconds": m.duration_seconds}
        for m in music
    ]


@router.delete("/music/{music_id}")
async def delete_music(
    music_id: int,
    db: Session = Depends(get_db),
):
    """Delete a music asset."""
    repo = AssetRepository(db)
    deleted = repo.delete_music(music_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Music not found")

    return {"status": "deleted"}


# =============================================================================
# Video Project Endpoints
# =============================================================================


@router.post("/projects", response_model=VideoProjectResponse)
async def create_project(
    request: VideoProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new video project and generate script."""
    repo = VideoProjectRepository(db)

    project = repo.create(
        title=request.title,
        topic=request.topic,
        context_style=request.context_style.value,
        questioner_id=request.questioner_id,
        explainer_id=request.explainer_id,
        background_music_id=request.background_music_id,
        document_id=request.document_id,
    )

    # TODO: Generate script using pipeline and update project

    return VideoProjectResponse.model_validate(project)


@router.get("/projects")
async def list_projects(
    status: VideoProjectStatus | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List video projects with optional status filter."""
    repo = VideoProjectRepository(db)
    projects = repo.list_projects(status=status, limit=limit, offset=offset)

    return [VideoProjectResponse.model_validate(p) for p in projects]


@router.get("/projects/{project_id}", response_model=VideoProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Get a video project by ID."""
    repo = VideoProjectRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return VideoProjectResponse.model_validate(project)


@router.patch("/projects/{project_id}")
async def update_project_script(
    project_id: int,
    script_json: dict,
    takeaway: str,
    db: Session = Depends(get_db),
):
    """Update project script content."""
    repo = VideoProjectRepository(db)
    project = repo.update_script(project_id, script_json, takeaway)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return VideoProjectResponse.model_validate(project)


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Delete a video project."""
    repo = VideoProjectRepository(db)
    deleted = repo.delete(project_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"status": "deleted"}


# =============================================================================
# Workflow Action Endpoints
# =============================================================================


@router.post("/projects/{project_id}/approve")
async def approve_project(
    project_id: int,
    reviewed_by: str = "system",
    db: Session = Depends(get_db),
):
    """Approve a project script for voiceover generation."""
    repo = VideoProjectRepository(db)
    project = repo.approve_project(project_id, reviewed_by)

    if not project:
        raise HTTPException(
            status_code=400,
            detail="Project not found or not in DRAFT status",
        )

    # TODO: Trigger voiceover generation via pipeline

    return VideoProjectResponse.model_validate(project)


@router.post("/projects/{project_id}/reject")
async def reject_project(
    project_id: int,
    notes: str,
    db: Session = Depends(get_db),
):
    """Reject a project script and return to draft."""
    repo = VideoProjectRepository(db)
    project = repo.update_status(
        project_id,
        VideoProjectStatus.DRAFT,
        error_message=f"Rejected: {notes}",
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return VideoProjectResponse.model_validate(project)


@router.post("/projects/{project_id}/regenerate")
async def regenerate_script(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Regenerate the script for a project."""
    repo = VideoProjectRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # TODO: Regenerate script using pipeline

    return VideoProjectResponse.model_validate(project)


@router.post("/projects/{project_id}/render")
async def render_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Trigger video rendering for a project."""
    repo = VideoProjectRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != VideoProjectStatus.AUDIO_READY:
        raise HTTPException(
            status_code=400,
            detail="Project must be in AUDIO_READY status to render",
        )

    # TODO: Trigger rendering via pipeline

    repo.update_status(project_id, VideoProjectStatus.RENDERING)

    return VideoProjectResponse.model_validate(project)


@router.get("/projects/{project_id}/download")
async def download_video(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Download the rendered video."""
    repo = VideoProjectRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.output_path:
        raise HTTPException(status_code=404, detail="Video not yet rendered")

    return FileResponse(
        project.output_path,
        media_type="video/mp4",
        filename=f"{project.title}.mp4",
    )


@router.get("/projects/{project_id}/preview-audio")
async def preview_audio(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Stream the voiceover audio for preview."""
    repo = VideoProjectRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.voiceover_path:
        raise HTTPException(status_code=404, detail="Voiceover not yet generated")

    return FileResponse(
        project.voiceover_path,
        media_type="audio/mpeg",
        filename=f"{project.title}_voiceover.mp3",
    )


# =============================================================================
# Settings Endpoints
# =============================================================================


@router.get("/voices")
async def list_voices():
    """List available Eleven Labs voices."""
    # TODO: Fetch from VoiceoverService
    return {"voices": []}


@router.post("/settings")
async def update_settings(
    default_questioner_voice: str | None = None,
    default_explainer_voice: str | None = None,
):
    """Update default voice settings."""
    # TODO: Persist settings
    return {"status": "updated"}
