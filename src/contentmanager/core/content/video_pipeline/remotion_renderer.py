"""Remotion-based video rendering with animated characters."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import DialogueScript, RenderResult
from .animation_prompts import generate_scene_prompts, save_prompts_to_file

logger = logging.getLogger(__name__)

# Path to Remotion project
REMOTION_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "remotion-video"


class RemotionRenderer:
    """Renders videos using Remotion for smooth character animations."""

    def __init__(
        self,
        remotion_dir: Path = REMOTION_DIR,
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ):
        self.remotion_dir = remotion_dir
        self.width = width
        self.height = height
        self.fps = fps

    async def render_video(
        self,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        character_assets: dict[str, dict[str, Path]],
        output_path: Path,
        music_path: Path | None = None,
    ) -> RenderResult:
        """Render video with Remotion animated characters."""
        # Ensure all paths are absolute
        voiceover_path = voiceover_path.absolute()
        background_path = background_path.absolute()
        output_path = output_path.absolute()

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get audio duration
        total_duration = self._get_audio_duration(voiceover_path)

        # Get individual scene durations for accurate sync
        scene_durations = self._get_scene_durations(voiceover_path.parent, len(script.lines))

        # Calculate frame timings from actual scene audio durations
        line_timings = self._calculate_frame_timings_from_scenes(script, scene_durations)

        # Build Remotion config
        config = self._build_config(
            script=script,
            voiceover_path=voiceover_path,
            background_path=background_path,
            output_path=output_path,
            line_timings=line_timings,
            character_assets=character_assets,
        )

        # Write config file (use absolute path)
        config_path = (output_path.parent / f"remotion_config_{output_path.stem}.json").absolute()
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Rendering Remotion video: {output_path}")
        logger.info(f"Config file: {config_path}")

        # Run Remotion render (use absolute path for config)
        result = subprocess.run(
            ["npx", "ts-node", "render.ts", str(config_path)],
            cwd=str(self.remotion_dir),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Remotion error: {result.stderr}")
            raise RuntimeError(f"Remotion rendering failed: {result.stderr}")

        # Clean up config
        config_path.unlink(missing_ok=True)

        # Generate AI animation prompts for each scene
        self._generate_animation_prompts(script, scene_durations, output_path)

        return RenderResult(
            output_path=str(output_path),
            duration_seconds=total_duration,
            width=self.width,
            height=self.height,
            file_size_bytes=output_path.stat().st_size,
            rendered_at=datetime.utcnow(),
        )

    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file using ffprobe."""
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())

    def _get_scene_durations(self, voiceover_dir: Path, num_scenes: int) -> list[float]:
        """Get actual duration of each scene audio file."""
        durations = []
        for i in range(1, num_scenes + 1):
            scene_file = voiceover_dir / f"scene_{i:03d}.mp3"
            if scene_file.exists():
                duration = self._get_audio_duration(scene_file)
                durations.append(duration)
                logger.debug(f"Scene {i}: {duration:.2f}s")
            else:
                # Fallback: estimate 3 seconds per scene
                durations.append(3.0)
                logger.warning(f"Scene file not found: {scene_file}, using 3s estimate")
        return durations

    def _calculate_frame_timings_from_scenes(
        self, script: DialogueScript, scene_durations: list[float]
    ) -> list[dict[str, Any]]:
        """Calculate frame timing using actual scene audio durations."""
        timings = []
        current_time = 0.0

        # Add intro buffer (2 seconds for title)
        intro_duration = 2.0
        intro_frames = int(self.fps * intro_duration)

        for i, line in enumerate(script.lines):
            # Use actual scene duration if available
            if i < len(scene_durations):
                line_duration = scene_durations[i]
            else:
                line_duration = 3.0  # Fallback

            start_frame = intro_frames + int(current_time * self.fps)
            end_frame = intro_frames + int((current_time + line_duration) * self.fps)

            timings.append({
                "speaker_role": line.speaker_role.value,
                "speaker_name": line.speaker_name,
                "line": line.line,
                "start_frame": start_frame,
                "end_frame": end_frame,
            })

            current_time += line_duration
            logger.debug(f"Line {i+1}: frames {start_frame}-{end_frame} ({line_duration:.2f}s)")

        return timings

    def _build_config(
        self,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        output_path: Path,
        line_timings: list[dict[str, Any]],
        character_assets: dict[str, dict[str, Path]] | None = None,
        character_type: str = "lottie",
    ) -> dict[str, Any]:
        """Build Remotion render configuration."""
        # Get character names from script
        questioner_name = "Alex the Curious"
        explainer_name = "Dr. Knowledge"

        for line in script.lines:
            if line.speaker_role.value == "questioner":
                questioner_name = line.speaker_name
            elif line.speaker_role.value == "explainer":
                explainer_name = line.speaker_name

        config = {
            "dialogueLines": line_timings,
            "backgroundImage": str(background_path.absolute()),
            "audioFile": str(voiceover_path.absolute()),
            "questionerName": questioner_name,
            "explainerName": explainer_name,
            "title": script.topic,
            "takeaway": script.takeaway or "Thanks for watching!",
            "outputPath": str(output_path.absolute()),
            "characterType": character_type,  # 'svg' or 'lottie'
        }

        # Add character images if available
        if character_assets:
            if "questioner" in character_assets:
                q_assets = character_assets["questioner"]
                if "neutral" in q_assets and "talking" in q_assets:
                    config["questionerImages"] = {
                        "neutral": str(q_assets["neutral"].absolute()),
                        "talking": str(q_assets["talking"].absolute()),
                    }
            if "explainer" in character_assets:
                e_assets = character_assets["explainer"]
                if "neutral" in e_assets and "talking" in e_assets:
                    config["explainerImages"] = {
                        "neutral": str(e_assets["neutral"].absolute()),
                        "talking": str(e_assets["talking"].absolute()),
                    }

        return config

    def _generate_animation_prompts(
        self,
        script: DialogueScript,
        scene_durations: list[float],
        output_path: Path,
    ) -> None:
        """Generate AI animation prompts for each scene and save to file."""
        # Convert script lines to dict format for prompt generator
        lines_data = [
            {
                "speaker_role": line.speaker_role.value,
                "speaker_name": line.speaker_name,
                "line": line.line,
            }
            for line in script.lines
        ]

        # Generate prompts
        scene_prompts = generate_scene_prompts(lines_data, scene_durations)

        # Save prompts to file next to the video
        prompts_path = output_path.parent / f"{output_path.stem}_animation_prompts.txt"
        save_prompts_to_file(scene_prompts, str(prompts_path))

        logger.info(f"AI animation prompts saved to: {prompts_path}")
