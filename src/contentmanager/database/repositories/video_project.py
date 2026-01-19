"""Repository for video project data access."""

from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import (
    VideoProject,
    VideoScene,
    Character,
    CharacterAsset,
    BackgroundAsset,
    MusicAsset,
)
from ...core.content.video_pipeline.models import VideoProjectStatus


class VideoProjectRepository:
    """Data access layer for video projects."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        title: str,
        topic: str,
        context_style: str,
        questioner_id: int,
        explainer_id: int,
        background_music_id: int | None = None,
        document_id: int | None = None,
        tenant_id: int | None = None,
    ) -> VideoProject:
        """Create a new video project."""
        project = VideoProject(
            title=title,
            topic=topic,
            context_style=context_style,
            questioner_id=questioner_id,
            explainer_id=explainer_id,
            background_music_id=background_music_id,
            document_id=document_id,
            tenant_id=tenant_id,
            status=VideoProjectStatus.DRAFT,
        )
        self.session.add(project)
        self.session.commit()
        self.session.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> VideoProject | None:
        """Get a video project by ID with relationships loaded."""
        stmt = (
            select(VideoProject)
            .where(VideoProject.id == project_id)
            .options(
                selectinload(VideoProject.questioner),
                selectinload(VideoProject.explainer),
                selectinload(VideoProject.scenes),
                selectinload(VideoProject.background_music),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_projects(
        self,
        status: VideoProjectStatus | None = None,
        tenant_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VideoProject]:
        """List video projects with optional filtering."""
        stmt = select(VideoProject).order_by(VideoProject.created_at.desc())

        if status:
            stmt = stmt.where(VideoProject.status == status)

        if tenant_id is not None:
            stmt = stmt.where(VideoProject.tenant_id == tenant_id)

        stmt = stmt.limit(limit).offset(offset)
        return list(self.session.execute(stmt).scalars().all())

    def update_status(
        self,
        project_id: int,
        status: VideoProjectStatus,
        error_message: str | None = None,
    ) -> VideoProject | None:
        """Update project status."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        project.status = status
        project.error_message = error_message
        project.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(project)
        return project

    def update_script(
        self,
        project_id: int,
        script_json: dict,
        takeaway: str,
    ) -> VideoProject | None:
        """Update project script content."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        project.script_json = script_json
        project.takeaway = takeaway
        project.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(project)
        return project

    def approve_project(
        self,
        project_id: int,
        reviewed_by: str,
    ) -> VideoProject | None:
        """Approve a project for voiceover generation."""
        project = self.get_by_id(project_id)
        if not project or project.status != VideoProjectStatus.DRAFT:
            return None

        project.status = VideoProjectStatus.APPROVED
        project.reviewed_at = datetime.utcnow()
        project.reviewed_by = reviewed_by
        project.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(project)
        return project

    def set_voiceover_path(
        self,
        project_id: int,
        voiceover_path: str,
    ) -> VideoProject | None:
        """Set voiceover path after generation."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        project.voiceover_path = voiceover_path
        project.status = VideoProjectStatus.AUDIO_READY
        project.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(project)
        return project

    def set_output(
        self,
        project_id: int,
        output_path: str,
        duration_seconds: float,
    ) -> VideoProject | None:
        """Set output video path after rendering."""
        project = self.get_by_id(project_id)
        if not project:
            return None

        project.output_path = output_path
        project.duration_seconds = duration_seconds
        project.status = VideoProjectStatus.COMPLETED
        project.updated_at = datetime.utcnow()

        self.session.commit()
        self.session.refresh(project)
        return project

    def delete(self, project_id: int) -> bool:
        """Delete a video project."""
        project = self.get_by_id(project_id)
        if not project:
            return False

        self.session.delete(project)
        self.session.commit()
        return True

    def add_scene(
        self,
        project_id: int,
        scene_number: int,
        speaker_role: str,
        line: str,
        pose: str,
        background_id: int | None = None,
    ) -> VideoScene:
        """Add a scene to a project."""
        scene = VideoScene(
            project_id=project_id,
            scene_number=scene_number,
            speaker_role=speaker_role,
            line=line,
            pose=pose,
            background_id=background_id,
        )
        self.session.add(scene)
        self.session.commit()
        self.session.refresh(scene)
        return scene

    def update_scene_audio(
        self,
        scene_id: int,
        voiceover_path: str,
        start_time: float,
        duration_seconds: float,
    ) -> VideoScene | None:
        """Update scene with audio timing information."""
        scene = self.session.get(VideoScene, scene_id)
        if not scene:
            return None

        scene.voiceover_path = voiceover_path
        scene.start_time = start_time
        scene.duration_seconds = duration_seconds

        self.session.commit()
        self.session.refresh(scene)
        return scene


class CharacterRepository:
    """Data access layer for characters."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        name: str,
        role: str,
        tenant_id: int | None = None,
    ) -> Character:
        """Create a new character."""
        character = Character(
            name=name,
            role=role,
            tenant_id=tenant_id,
        )
        self.session.add(character)
        self.session.commit()
        self.session.refresh(character)
        return character

    def get_by_id(self, character_id: int) -> Character | None:
        """Get a character by ID with assets loaded."""
        stmt = (
            select(Character)
            .where(Character.id == character_id)
            .options(selectinload(Character.assets))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_characters(
        self,
        tenant_id: int | None = None,
        is_active: bool = True,
    ) -> list[Character]:
        """List all characters."""
        stmt = select(Character).where(Character.is_active == is_active)

        if tenant_id is not None:
            stmt = stmt.where(Character.tenant_id == tenant_id)

        return list(self.session.execute(stmt).scalars().all())

    def add_asset(
        self,
        character_id: int,
        pose: str,
        file_path: str,
        file_size_bytes: int,
        tenant_id: int | None = None,
    ) -> CharacterAsset:
        """Add a pose asset to a character."""
        asset = CharacterAsset(
            character_id=character_id,
            pose=pose,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            tenant_id=tenant_id,
        )
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def delete_asset(self, asset_id: int) -> bool:
        """Delete a character asset."""
        asset = self.session.get(CharacterAsset, asset_id)
        if not asset:
            return False

        self.session.delete(asset)
        self.session.commit()
        return True


class AssetRepository:
    """Data access layer for background and music assets."""

    def __init__(self, session: Session):
        self.session = session

    def create_background(
        self,
        name: str,
        file_path: str,
        context_style: str | None = None,
        tenant_id: int | None = None,
    ) -> BackgroundAsset:
        """Create a background asset."""
        asset = BackgroundAsset(
            name=name,
            file_path=file_path,
            context_style=context_style,
            tenant_id=tenant_id,
        )
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def create_music(
        self,
        name: str,
        file_path: str,
        duration_seconds: float,
        context_style: str | None = None,
        tenant_id: int | None = None,
    ) -> MusicAsset:
        """Create a music asset."""
        asset = MusicAsset(
            name=name,
            file_path=file_path,
            duration_seconds=duration_seconds,
            context_style=context_style,
            tenant_id=tenant_id,
        )
        self.session.add(asset)
        self.session.commit()
        self.session.refresh(asset)
        return asset

    def list_backgrounds(
        self,
        context_style: str | None = None,
        tenant_id: int | None = None,
    ) -> list[BackgroundAsset]:
        """List background assets."""
        stmt = select(BackgroundAsset)

        if context_style:
            stmt = stmt.where(BackgroundAsset.context_style == context_style)

        if tenant_id is not None:
            stmt = stmt.where(BackgroundAsset.tenant_id == tenant_id)

        return list(self.session.execute(stmt).scalars().all())

    def list_music(
        self,
        context_style: str | None = None,
        tenant_id: int | None = None,
    ) -> list[MusicAsset]:
        """List music assets."""
        stmt = select(MusicAsset)

        if context_style:
            stmt = stmt.where(MusicAsset.context_style == context_style)

        if tenant_id is not None:
            stmt = stmt.where(MusicAsset.tenant_id == tenant_id)

        return list(self.session.execute(stmt).scalars().all())

    def delete_background(self, asset_id: int) -> bool:
        """Delete a background asset."""
        asset = self.session.get(BackgroundAsset, asset_id)
        if not asset:
            return False

        self.session.delete(asset)
        self.session.commit()
        return True

    def delete_music(self, asset_id: int) -> bool:
        """Delete a music asset."""
        asset = self.session.get(MusicAsset, asset_id)
        if not asset:
            return False

        self.session.delete(asset)
        self.session.commit()
        return True
