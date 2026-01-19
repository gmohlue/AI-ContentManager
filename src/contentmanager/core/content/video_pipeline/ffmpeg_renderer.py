"""Video rendering using FFmpeg."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .models import DialogueScript, RenderResult

logger = logging.getLogger(__name__)


class FFmpegRenderer:
    """Renders videos using FFmpeg filter complex."""

    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
        width: int = 1080,
        height: int = 1920,
        fps: int = 30,
    ):
        self.ffmpeg_path = ffmpeg_path
        self.ffprobe_path = ffprobe_path
        self.width = width
        self.height = height
        self.fps = fps

    async def render_video(
        self,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        character_assets: dict[str, Path],  # {role_pose: path}
        output_path: Path,
        music_path: Path | None = None,
    ) -> RenderResult:
        """Render the video using FFmpeg.

        Args:
            script: The dialogue script with scene information
            voiceover_path: Path to combined voiceover audio
            background_path: Path to background image
            character_assets: Dict mapping role_pose to image path
            output_path: Path for output video
            music_path: Optional background music path

        Returns:
            RenderResult with output file metadata
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build FFmpeg command
        cmd = self._build_ffmpeg_command(
            script=script,
            voiceover_path=voiceover_path,
            background_path=background_path,
            character_assets=character_assets,
            output_path=output_path,
            music_path=music_path,
        )

        logger.info(f"Rendering video: {output_path}")
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        # Run FFmpeg
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if process.returncode != 0:
            logger.error(f"FFmpeg error: {process.stderr}")
            raise RuntimeError(f"FFmpeg rendering failed: {process.stderr}")

        # Get output file info
        file_size = output_path.stat().st_size
        duration = await self._get_video_duration(output_path)

        return RenderResult(
            output_path=str(output_path),
            duration_seconds=duration,
            width=self.width,
            height=self.height,
            file_size_bytes=file_size,
            rendered_at=datetime.utcnow(),
        )

    def _build_ffmpeg_command(
        self,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        character_assets: dict[str, Path],
        output_path: Path,
        music_path: Path | None,
    ) -> list[str]:
        """Build the FFmpeg command with filter complex."""
        cmd = [self.ffmpeg_path, "-y"]

        # Input 0: background image (looped)
        cmd.extend(["-loop", "1", "-i", str(background_path)])

        # Input 1: voiceover audio
        cmd.extend(["-i", str(voiceover_path)])

        # Input 2+: character assets
        # We expect keys like "questioner" or "explainer"
        input_index = 2
        character_inputs = {}
        for role, path in character_assets.items():
            if path and path.exists():
                cmd.extend(["-loop", "1", "-i", str(path)])
                character_inputs[role] = input_index
                input_index += 1

        # Input: background music (if provided)
        music_input = None
        if music_path:
            cmd.extend(["-i", str(music_path)])
            music_input = input_index

        # Build filter complex with character overlays
        filter_complex = self._build_filter_complex(script, character_inputs)

        cmd.extend(["-filter_complex", filter_complex])

        # Output settings
        cmd.extend(
            [
                "-map",
                "[outv]",
                "-map",
                "1:a",  # Voiceover audio
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "23",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-pix_fmt",
                "yuv420p",
                str(output_path),
            ]
        )

        return cmd

    def _build_filter_complex(
        self, script: DialogueScript, character_inputs: dict[str, int]
    ) -> str:
        """Build FFmpeg filter complex for video composition.

        Creates:
        - Scaled background
        - Character overlays (questioner on left, explainer on right)
        - Text overlays with fade-in animation for each line
        """
        filters = []

        # Scale background to output dimensions
        filters.append(
            f"[0:v]scale={self.width}:{self.height}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2[bg]"
        )

        # Scale and prepare character images
        char_height = 600  # Character height in pixels
        for role, input_idx in character_inputs.items():
            filters.append(
                f"[{input_idx}:v]scale=-1:{char_height}:flags=lanczos,"
                f"format=rgba[char_{role}]"
            )

        # Overlay characters on background
        current_stream = "bg"

        # Position characters: questioner on left, explainer on right
        if "questioner" in character_inputs:
            x_pos = 50  # Left side
            y_pos = self.height - char_height - 300  # Above text area
            filters.append(
                f"[{current_stream}][char_questioner]overlay="
                f"x={x_pos}:y={y_pos}:format=auto[bg_q]"
            )
            current_stream = "bg_q"

        if "explainer" in character_inputs:
            x_pos = self.width - 450  # Right side (accounting for character width)
            y_pos = self.height - char_height - 300
            filters.append(
                f"[{current_stream}][char_explainer]overlay="
                f"x={x_pos}:y={y_pos}:format=auto[bg_chars]"
            )
            current_stream = "bg_chars"

        # Add text overlays for each line with timing
        current_time = 0.0
        estimated_duration_per_line = 3.0  # seconds

        for i, line in enumerate(script.lines):
            next_stream = f"v{i}"

            # Calculate timing
            start_time = current_time
            end_time = start_time + estimated_duration_per_line
            fade_duration = 0.3

            # Wrap text for better display
            wrapped_text = self._wrap_text(line.line, max_chars=40)

            # Speaker name label
            speaker_label = f"{line.speaker_name}:"

            # Position: centered at bottom with speaker name above
            text_filter = (
                f"[{current_stream}]drawtext="
                f"text='{self._escape_text(speaker_label)}':"
                f"fontsize=32:"
                f"fontcolor=yellow:"
                f"x=(w-text_w)/2:"
                f"y=h-280:"
                f"enable='between(t,{start_time},{end_time})':"
                f"alpha='if(lt(t-{start_time},{fade_duration}),(t-{start_time})/{fade_duration},1)',"
                f"drawtext="
                f"text='{self._escape_text(wrapped_text)}':"
                f"fontsize=36:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y=h-220:"
                f"enable='between(t,{start_time},{end_time})':"
                f"alpha='if(lt(t-{start_time},{fade_duration}),(t-{start_time})/{fade_duration},1)'"
                f"[{next_stream}]"
            )

            filters.append(text_filter)
            current_stream = next_stream
            current_time = end_time

        # Final output label
        filters.append(f"[{current_stream}]copy[outv]")

        return ";".join(filters)

    def _wrap_text(self, text: str, max_chars: int = 40) -> str:
        """Wrap text to multiple lines for better display."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(" ".join(current_line))

        return "\\n".join(lines)

    def _escape_text(self, text: str) -> str:
        """Escape text for FFmpeg drawtext filter."""
        return (
            text.replace("\\", "\\\\")
            .replace("'", "'\\''")
            .replace(":", "\\:")
            .replace("%", "\\%")
        )

    async def _get_video_duration(self, video_path: Path) -> float:
        """Get duration of video file using ffprobe."""
        result = subprocess.run(
            [
                self.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())
