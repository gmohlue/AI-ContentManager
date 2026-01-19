"""FastAPI router for video project endpoints."""

import logging
import subprocess
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...config import settings
from ...core.content.video_pipeline.models import (
    ContextStyle,
    DialogueScript,
    DialogueLine,
    CharacterRole,
    VideoProjectCreate,
    VideoProjectResponse,
    VideoProjectStatus,
)
from ...core.content.video_pipeline.asset_manager import AssetManager
from ...core.content.video_pipeline.script_generator import DialogueScriptGenerator
from ...core.content.video_pipeline.voiceover_service import VoiceoverService
from ...core.content.video_pipeline.lipsync_renderer import LipSyncRenderer
from ...core.content.video_pipeline.pipeline import VideoPipeline
from ...database.repositories.video_project import (
    VideoProjectRepository,
    CharacterRepository,
    AssetRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["video"])


# =============================================================================
# Service Initialization
# =============================================================================

# Asset Manager
asset_manager = AssetManager(settings.video.assets_dir)

# Script Generator (lazy init - requires API key)
_script_generator: DialogueScriptGenerator | None = None

def get_script_generator() -> DialogueScriptGenerator:
    global _script_generator
    if _script_generator is None:
        if not settings.claude.api_key:
            raise HTTPException(
                status_code=503,
                detail="Claude API key not configured. Set CLAUDE_API_KEY environment variable."
            )
        _script_generator = DialogueScriptGenerator(
            api_key=settings.claude.api_key,
            model=settings.claude.model,
        )
    return _script_generator

# Voiceover Service (lazy init - requires API key)
_voiceover_service: VoiceoverService | None = None

def get_voiceover_service() -> VoiceoverService:
    global _voiceover_service
    if _voiceover_service is None:
        if not settings.video.elevenlabs_api_key:
            raise HTTPException(
                status_code=503,
                detail="Eleven Labs API key not configured. Set VIDEO_ELEVENLABS_API_KEY environment variable."
            )
        _voiceover_service = VoiceoverService(
            api_key=settings.video.elevenlabs_api_key,
            questioner_voice_id=settings.video.elevenlabs_questioner_voice,
            explainer_voice_id=settings.video.elevenlabs_explainer_voice,
        )
    return _voiceover_service

# Lip-Sync Renderer
lipsync_renderer = LipSyncRenderer(
    ffmpeg_path=settings.video.ffmpeg_path,
    ffprobe_path=settings.video.ffprobe_path,
    width=settings.video.width,
    height=settings.video.height,
    fps=settings.video.fps,
)

def get_pipeline() -> VideoPipeline:
    """Get configured video pipeline."""
    return VideoPipeline(
        script_generator=get_script_generator(),
        voiceover_service=get_voiceover_service(),
        renderer=lipsync_renderer,
        asset_manager=asset_manager,
        projects_dir=settings.video.projects_dir,
    )


# Dependency placeholder - replace with actual database session dependency
def get_db() -> Session:
    """Get database session dependency."""
    raise NotImplementedError("Database session dependency not configured")


def get_audio_duration(file_path: Path) -> float:
    """Get duration of audio file using ffprobe."""
    try:
        result = subprocess.run(
            [
                settings.video.ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
    except (ValueError, subprocess.CalledProcessError):
        return 0.0


# =============================================================================
# Character Endpoints
# =============================================================================


@router.post("/characters")
async def create_character(
    name: str,
    role: CharacterRole,
    db: Session = Depends(get_db),
):
    """Create a new character."""
    repo = CharacterRepository(db)
    character = repo.create(name=name, role=role)
    return {"id": character.id, "name": character.name, "role": character.role.value}


@router.get("/characters")
async def list_characters(db: Session = Depends(get_db)):
    """List all characters."""
    repo = CharacterRepository(db)
    characters = repo.list_characters()
    return [
        {"id": c.id, "name": c.name, "role": c.role.value, "is_active": c.is_active}
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

    # Save file using AssetManager
    try:
        file_path = await asset_manager.save_character_asset(
            character_id=character_id,
            pose=pose,
            file=file.file,
            filename=file.filename or f"{pose}.png",
        )
        file_size = file_path.stat().st_size
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    asset = repo.add_asset(
        character_id=character_id,
        pose=pose,
        file_path=str(file_path),
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
    asset = repo.get_asset_by_id(asset_id)

    if asset:
        # Delete file from disk
        await asset_manager.delete_asset(Path(asset.file_path))

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

    # Save file using AssetManager
    try:
        file_path = await asset_manager.save_background_asset(
            name=name,
            file=file.file,
            filename=file.filename or f"{name}.png",
            context_style=context_style,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    asset = repo.create_background(
        name=name,
        file_path=str(file_path),
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
    background = repo.get_background_by_id(background_id)

    if background:
        # Delete file from disk
        await asset_manager.delete_asset(Path(background.file_path))

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

    # Save file using AssetManager
    try:
        file_path = await asset_manager.save_music_asset(
            name=name,
            file=file.file,
            filename=file.filename or f"{name}.mp3",
            context_style=context_style,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Get actual duration using ffprobe
    duration_seconds = get_audio_duration(file_path)

    asset = repo.create_music(
        name=name,
        file_path=str(file_path),
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
    music = repo.get_music_by_id(music_id)

    if music:
        # Delete file from disk
        await asset_manager.delete_asset(Path(music.file_path))

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new video project and generate script."""
    repo = VideoProjectRepository(db)
    char_repo = CharacterRepository(db)

    # Validate characters exist
    questioner = char_repo.get_by_id(request.questioner_id)
    explainer = char_repo.get_by_id(request.explainer_id)

    if not questioner:
        raise HTTPException(status_code=400, detail="Questioner character not found")
    if not explainer:
        raise HTTPException(status_code=400, detail="Explainer character not found")

    project = repo.create(
        title=request.title,
        topic=request.topic,
        context_style=request.context_style.value,
        questioner_id=request.questioner_id,
        explainer_id=request.explainer_id,
        background_music_id=request.background_music_id,
        document_id=request.document_id,
    )

    # Generate script in background
    background_tasks.add_task(
        generate_script_task,
        project_id=project.id,
        topic=request.topic,
        context_style=request.context_style,
        questioner_name=questioner.name,
        explainer_name=explainer.name,
    )

    return VideoProjectResponse.model_validate(project)


async def generate_script_task(
    project_id: int,
    topic: str,
    context_style: ContextStyle,
    questioner_name: str,
    explainer_name: str,
):
    """Background task to generate script."""
    from ...main import SessionLocal

    db = SessionLocal()
    try:
        repo = VideoProjectRepository(db)

        try:
            script_gen = get_script_generator()
            script = await script_gen.generate(
                topic=topic,
                context_style=context_style,
                questioner_name=questioner_name,
                explainer_name=explainer_name,
            )

            # Update project with script
            repo.update_script(
                project_id=project_id,
                script_json=script.model_dump(),
                takeaway=script.takeaway,
            )
            logger.info(f"Script generated for project {project_id}")

        except Exception as e:
            logger.error(f"Script generation failed for project {project_id}: {e}")
            repo.update_status(
                project_id=project_id,
                status=VideoProjectStatus.FAILED,
                error_message=f"Script generation failed: {str(e)}",
            )
    finally:
        db.close()


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


class UpdateScriptRequest(BaseModel):
    """Request model for updating project script."""
    script_json: dict
    takeaway: str


@router.patch("/projects/{project_id}")
async def update_project_script(
    project_id: int,
    request: UpdateScriptRequest,
    db: Session = Depends(get_db),
):
    """Update project script content."""
    repo = VideoProjectRepository(db)
    project = repo.update_script(project_id, request.script_json, request.takeaway)

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
    background_tasks: BackgroundTasks,
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

    # Trigger voiceover generation in background
    background_tasks.add_task(
        generate_voiceover_task,
        project_id=project_id,
    )

    return VideoProjectResponse.model_validate(project)


async def generate_voiceover_task(project_id: int):
    """Background task to generate voiceover."""
    from ...main import SessionLocal

    db = SessionLocal()
    try:
        repo = VideoProjectRepository(db)
        project = repo.get_by_id(project_id)

        if not project or not project.script_json:
            logger.error(f"Project {project_id} not found or has no script")
            return

        try:
            # Reconstruct script from JSON
            script_data = project.script_json
            lines = [
                DialogueLine(
                    speaker_role=CharacterRole(line["speaker_role"]),
                    speaker_name=line["speaker_name"],
                    line=line["line"],
                    pose=line.get("pose", "standing"),
                    scene_number=line["scene_number"],
                )
                for line in script_data.get("lines", [])
            ]

            script = DialogueScript(
                topic=script_data["topic"],
                context_style=ContextStyle(script_data["context_style"]),
                lines=lines,
                takeaway=script_data.get("takeaway", ""),
            )

            voiceover_service = get_voiceover_service()
            output_dir = settings.video.projects_dir / "voiceovers" / str(project_id)

            result = await voiceover_service.generate_voiceover(
                script=script,
                output_dir=output_dir,
            )

            # Update project with voiceover path
            repo.update_voiceover(
                project_id=project_id,
                voiceover_path=result.combined_audio_path,
            )
            repo.update_status(project_id, VideoProjectStatus.AUDIO_READY)

            logger.info(f"Voiceover generated for project {project_id}")

        except Exception as e:
            logger.error(f"Voiceover generation failed for project {project_id}: {e}")
            repo.update_status(
                project_id=project_id,
                status=VideoProjectStatus.FAILED,
                error_message=f"Voiceover generation failed: {str(e)}",
            )
    finally:
        db.close()


class RejectRequest(BaseModel):
    """Request model for rejecting a project."""
    notes: str


@router.post("/projects/{project_id}/reject")
async def reject_project(
    project_id: int,
    request: RejectRequest,
    db: Session = Depends(get_db),
):
    """Reject a project script and return to draft."""
    repo = VideoProjectRepository(db)
    project = repo.update_status(
        project_id,
        VideoProjectStatus.DRAFT,
        error_message=f"Rejected: {request.notes}",
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return VideoProjectResponse.model_validate(project)


@router.post("/projects/{project_id}/regenerate")
async def regenerate_script(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Regenerate the script for a project."""
    repo = VideoProjectRepository(db)
    char_repo = CharacterRepository(db)
    project = repo.get_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get character names
    questioner = char_repo.get_by_id(project.questioner_id)
    explainer = char_repo.get_by_id(project.explainer_id)

    questioner_name = questioner.name if questioner else "Thabo"
    explainer_name = explainer.name if explainer else "Lerato"

    # Reset status to draft
    repo.update_status(project_id, VideoProjectStatus.DRAFT)

    # Regenerate script in background
    background_tasks.add_task(
        generate_script_task,
        project_id=project_id,
        topic=project.topic,
        context_style=ContextStyle(project.context_style),
        questioner_name=questioner_name,
        explainer_name=explainer_name,
    )

    return VideoProjectResponse.model_validate(project)


@router.post("/projects/{project_id}/render")
async def render_project(
    project_id: int,
    background_id: int | None = None,
    background_tasks: BackgroundTasks = None,
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

    repo.update_status(project_id, VideoProjectStatus.RENDERING)

    # Trigger rendering in background
    background_tasks.add_task(
        render_video_task,
        project_id=project_id,
        background_id=background_id,
    )

    return VideoProjectResponse.model_validate(project)


async def render_video_task(project_id: int, background_id: int | None = None):
    """Background task to render video."""
    from ...main import SessionLocal

    db = SessionLocal()
    try:
        repo = VideoProjectRepository(db)
        char_repo = CharacterRepository(db)
        asset_repo = AssetRepository(db)

        project = repo.get_by_id(project_id)

        if not project or not project.script_json or not project.voiceover_path:
            logger.error(f"Project {project_id} not ready for rendering")
            return

        try:
            # Reconstruct script from JSON
            script_data = project.script_json
            lines = [
                DialogueLine(
                    speaker_role=CharacterRole(line["speaker_role"]),
                    speaker_name=line["speaker_name"],
                    line=line["line"],
                    pose=line.get("pose", "standing"),
                    scene_number=line["scene_number"],
                )
                for line in script_data.get("lines", [])
            ]

            script = DialogueScript(
                topic=script_data["topic"],
                context_style=ContextStyle(script_data["context_style"]),
                lines=lines,
                takeaway=script_data.get("takeaway", ""),
            )

            # Get background
            if background_id:
                background = asset_repo.get_background_by_id(background_id)
                background_path = Path(background.file_path) if background else None
            else:
                # Use first available background
                backgrounds = asset_repo.list_backgrounds()
                background_path = Path(backgrounds[0].file_path) if backgrounds else None

            if not background_path or not background_path.exists():
                raise ValueError("No background image available")

            # Get character assets (use first available pose for each role)
            questioner = char_repo.get_by_id(project.questioner_id)
            explainer = char_repo.get_by_id(project.explainer_id)

            character_assets = {}

            if questioner:
                q_assets = asset_manager.get_character_assets(questioner.id)
                # Build dict of poses: {pose_name: path}
                q_poses = {}
                for asset in q_assets:
                    q_poses[asset["pose"]] = Path(asset["file_path"])
                if q_poses:
                    character_assets["questioner"] = q_poses

            if explainer:
                e_assets = asset_manager.get_character_assets(explainer.id)
                # Build dict of poses: {pose_name: path}
                e_poses = {}
                for asset in e_assets:
                    e_poses[asset["pose"]] = Path(asset["file_path"])
                if e_poses:
                    character_assets["explainer"] = e_poses

            # Get music if specified
            music_path = None
            if project.background_music_id:
                music = asset_repo.get_music_by_id(project.background_music_id)
                if music:
                    music_path = Path(music.file_path)

            # Render video
            output_dir = settings.video.projects_dir / "videos"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"project_{project_id}.mp4"

            result = await lipsync_renderer.render_video(
                script=script,
                voiceover_path=Path(project.voiceover_path),
                background_path=background_path,
                character_assets=character_assets,
                output_path=output_path,
                music_path=music_path,
            )

            # Update project with output
            repo.update_output(
                project_id=project_id,
                output_path=str(result.output_path),
                duration_seconds=result.duration_seconds,
            )
            repo.update_status(project_id, VideoProjectStatus.COMPLETED)

            logger.info(f"Video rendered for project {project_id}")

        except Exception as e:
            logger.error(f"Video rendering failed for project {project_id}: {e}")
            repo.update_status(
                project_id=project_id,
                status=VideoProjectStatus.FAILED,
                error_message=f"Video rendering failed: {str(e)}",
            )
    finally:
        db.close()


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
    try:
        voiceover_service = get_voiceover_service()
        voices = await voiceover_service.list_voices()
        return {"voices": voices}
    except HTTPException:
        # API key not configured
        return {"voices": [], "error": "Eleven Labs API not configured"}
    except Exception as e:
        logger.error(f"Failed to fetch voices: {e}")
        return {"voices": [], "error": str(e)}


@router.post("/settings")
async def update_settings(
    default_questioner_voice: str | None = None,
    default_explainer_voice: str | None = None,
):
    """Update default voice settings."""
    # For now, these would need to be persisted to a config store
    # This is a placeholder that could be extended
    return {
        "status": "updated",
        "note": "Voice settings are currently managed via environment variables"
    }
