"""Video pipeline orchestrator."""

import logging
from pathlib import Path

from .models import (
    ContextStyle,
    DialogueScript,
    RenderResult,
    VideoProjectStatus,
    VoiceoverResult,
)
from .script_generator import DialogueScriptGenerator
from .voiceover_service import VoiceoverService
from .ffmpeg_renderer import FFmpegRenderer
from .asset_manager import AssetManager

logger = logging.getLogger(__name__)


class VideoPipeline:
    """Orchestrates the video generation pipeline.

    Pipeline flow:
    1. Generate script (Claude) -> Status: DRAFT
    2. Human review/approval -> Status: APPROVED
    3. Generate voiceover (Eleven Labs) -> Status: AUDIO_READY
    4. Render video (FFmpeg) -> Status: COMPLETED
    """

    def __init__(
        self,
        script_generator: DialogueScriptGenerator,
        voiceover_service: VoiceoverService,
        renderer: FFmpegRenderer,
        asset_manager: AssetManager,
        projects_dir: Path,
    ):
        self.script_generator = script_generator
        self.voiceover_service = voiceover_service
        self.renderer = renderer
        self.asset_manager = asset_manager
        self.projects_dir = projects_dir

    async def generate_script(
        self,
        project_id: int,
        topic: str,
        context_style: ContextStyle,
        questioner_name: str = "Thabo",
        explainer_name: str = "Lerato",
        document_context: str | None = None,
        target_duration: int = 45,
    ) -> DialogueScript:
        """Generate a dialogue script for a video project.

        Args:
            project_id: ID of the video project
            topic: Subject matter for the video
            context_style: Style/theme of the content
            questioner_name: Name of questioner character
            explainer_name: Name of explainer character
            document_context: Optional source document
            target_duration: Target duration in seconds

        Returns:
            Generated DialogueScript
        """
        logger.info(f"Generating script for project {project_id}: {topic}")

        script = await self.script_generator.generate(
            topic=topic,
            context_style=context_style,
            questioner_name=questioner_name,
            explainer_name=explainer_name,
            document_context=document_context,
            target_duration=target_duration,
        )

        logger.info(
            f"Script generated with {len(script.lines)} lines for project {project_id}"
        )
        return script

    async def generate_voiceover(
        self,
        project_id: int,
        script: DialogueScript,
        voice_config: dict | None = None,
    ) -> VoiceoverResult:
        """Generate voiceover audio for a script.

        Args:
            project_id: ID of the video project
            script: The approved dialogue script
            voice_config: Optional voice ID overrides

        Returns:
            VoiceoverResult with audio paths and timing
        """
        logger.info(f"Generating voiceover for project {project_id}")

        output_dir = self.projects_dir / "voiceovers" / str(project_id)

        result = await self.voiceover_service.generate_voiceover(
            script=script,
            output_dir=output_dir,
            voice_config=voice_config,
        )

        logger.info(
            f"Voiceover generated: {result.total_duration_seconds:.1f}s for project {project_id}"
        )
        return result

    async def render_video(
        self,
        project_id: int,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        character_assets: dict[str, Path],
        music_path: Path | None = None,
    ) -> RenderResult:
        """Render the final video.

        Args:
            project_id: ID of the video project
            script: The dialogue script
            voiceover_path: Path to combined voiceover audio
            background_path: Path to background image
            character_assets: Dict mapping role_pose to image path
            music_path: Optional background music path

        Returns:
            RenderResult with output video metadata
        """
        logger.info(f"Rendering video for project {project_id}")

        output_dir = self.projects_dir / "videos"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"project_{project_id}.mp4"

        result = await self.renderer.render_video(
            script=script,
            voiceover_path=voiceover_path,
            background_path=background_path,
            character_assets=character_assets,
            output_path=output_path,
            music_path=music_path,
        )

        logger.info(
            f"Video rendered: {result.duration_seconds:.1f}s, "
            f"{result.file_size_bytes / 1024 / 1024:.1f}MB for project {project_id}"
        )
        return result

    async def process_approved_project(
        self,
        project_id: int,
        script: DialogueScript,
        background_path: Path,
        character_assets: dict[str, Path],
        music_path: Path | None = None,
        voice_config: dict | None = None,
    ) -> RenderResult:
        """Process an approved project through voiceover and rendering.

        This is the main entry point after human approval.

        Args:
            project_id: ID of the video project
            script: The approved dialogue script
            background_path: Path to background image
            character_assets: Dict mapping role_pose to image path
            music_path: Optional background music path
            voice_config: Optional voice ID overrides

        Returns:
            RenderResult with final video metadata
        """
        # Step 1: Generate voiceover
        voiceover_result = await self.generate_voiceover(
            project_id=project_id,
            script=script,
            voice_config=voice_config,
        )

        # Step 2: Render video
        render_result = await self.render_video(
            project_id=project_id,
            script=script,
            voiceover_path=Path(voiceover_result.combined_audio_path),
            background_path=background_path,
            character_assets=character_assets,
            music_path=music_path,
        )

        return render_result
