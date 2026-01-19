"""Video rendering using FFmpeg."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .models import CharacterRole, DialogueScript, RenderResult

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
        character_assets: dict[str, dict[str, Path]],  # {role: {pose: path}}
        output_path: Path,
        music_path: Path | None = None,
    ) -> RenderResult:
        """Render the video using FFmpeg.

        Args:
            script: The dialogue script with scene information
            voiceover_path: Path to combined voiceover audio
            background_path: Path to background image
            character_assets: Dict mapping role to {pose: path} dict
            output_path: Path for output video
            music_path: Optional background music path

        Returns:
            RenderResult with output file metadata
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate line timings from voiceover segments
        line_timings = self._calculate_line_timings(script, voiceover_path)

        # Build FFmpeg command
        cmd = self._build_ffmpeg_command(
            script=script,
            voiceover_path=voiceover_path,
            background_path=background_path,
            character_assets=character_assets,
            output_path=output_path,
            music_path=music_path,
            line_timings=line_timings,
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

    def _calculate_line_timings(
        self, script: DialogueScript, voiceover_path: Path
    ) -> list[tuple[float, float, str]]:
        """Calculate timing for each line based on voiceover duration.

        Returns list of (start_time, end_time, speaker_role) tuples.
        """
        # Get total voiceover duration
        result = subprocess.run(
            [
                self.ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(voiceover_path),
            ],
            capture_output=True,
            text=True,
        )
        total_duration = float(result.stdout.strip())

        # Distribute time proportionally based on text length
        total_chars = sum(len(line.line) for line in script.lines)
        timings = []
        current_time = 0.0

        for line in script.lines:
            # Proportional duration based on text length
            line_duration = (len(line.line) / total_chars) * total_duration
            start_time = current_time
            end_time = current_time + line_duration
            timings.append((start_time, end_time, line.speaker_role.value))
            current_time = end_time

        return timings

    def _build_ffmpeg_command(
        self,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        character_assets: dict[str, dict[str, Path]],
        output_path: Path,
        music_path: Path | None,
        line_timings: list[tuple[float, float, str]],
    ) -> list[str]:
        """Build the FFmpeg command with filter complex."""
        cmd = [self.ffmpeg_path, "-y"]

        # Input 0: background image (looped)
        cmd.extend(["-loop", "1", "-i", str(background_path)])

        # Input 1: voiceover audio
        cmd.extend(["-i", str(voiceover_path)])

        # Input 2+: character pose assets
        # Structure: {role: {pose: path}}
        input_index = 2
        character_inputs = {}  # {role: {pose: input_index}}

        for role, poses in character_assets.items():
            character_inputs[role] = {}
            for pose, path in poses.items():
                if path and path.exists():
                    cmd.extend(["-loop", "1", "-i", str(path)])
                    character_inputs[role][pose] = input_index
                    input_index += 1

        # Input: background music (if provided)
        music_input = None
        if music_path:
            cmd.extend(["-i", str(music_path)])
            music_input = input_index

        # Build filter complex with animated character overlays
        filter_complex = self._build_filter_complex(
            script, character_inputs, line_timings
        )

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
        self,
        script: DialogueScript,
        character_inputs: dict[str, dict[str, int]],
        line_timings: list[tuple[float, float, str]],
    ) -> str:
        """Build FFmpeg filter complex for video composition.

        Creates:
        - Scaled background
        - Animated character overlays (switch between neutral/talking poses)
        - Text overlays with fade-in animation for each line
        """
        filters = []

        # Scale background to output dimensions
        filters.append(
            f"[0:v]scale={self.width}:{self.height}:"
            f"force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2[bg]"
        )

        # Character dimensions and positions
        char_height = 600
        positions = {
            "questioner": (50, self.height - char_height - 300),  # Left side
            "explainer": (self.width - 450, self.height - char_height - 300),  # Right
        }

        # Build speaking time windows for each role
        speaking_windows = {"questioner": [], "explainer": []}
        for start, end, role in line_timings:
            if role in speaking_windows:
                speaking_windows[role].append((start, end))

        # Scale and prepare all character pose images
        for role, poses in character_inputs.items():
            for pose, input_idx in poses.items():
                filters.append(
                    f"[{input_idx}:v]scale=-1:{char_height}:flags=lanczos,"
                    f"format=rgba[char_{role}_{pose}]"
                )

        # Overlay characters with pose switching
        current_stream = "bg"

        for role in ["questioner", "explainer"]:
            if role not in character_inputs:
                continue

            poses = character_inputs[role]
            x_pos, y_pos = positions[role]
            windows = speaking_windows[role]

            # Build the enable condition for "talking" state
            if windows:
                talking_conditions = [
                    f"between(t,{start:.2f},{end:.2f})" for start, end in windows
                ]
                talking_enable = "+".join(talking_conditions)
                neutral_enable = f"1-({talking_enable})"
            else:
                talking_enable = "0"
                neutral_enable = "1"

            # Determine which poses are available
            has_talking = "talking" in poses
            has_neutral = "neutral" in poses

            if has_neutral and has_talking:
                # Overlay neutral pose (when not speaking)
                next_stream = f"{current_stream}_{role}_n"
                filters.append(
                    f"[{current_stream}][char_{role}_neutral]overlay="
                    f"x={x_pos}:y={y_pos}:format=auto:"
                    f"enable='{neutral_enable}'[{next_stream}]"
                )
                current_stream = next_stream

                # Overlay talking pose (when speaking)
                next_stream = f"{current_stream}_t"
                filters.append(
                    f"[{current_stream}][char_{role}_talking]overlay="
                    f"x={x_pos}:y={y_pos}:format=auto:"
                    f"enable='{talking_enable}'[{next_stream}]"
                )
                current_stream = next_stream
            elif has_talking:
                # Only talking pose available - use it always
                next_stream = f"{current_stream}_{role}"
                filters.append(
                    f"[{current_stream}][char_{role}_talking]overlay="
                    f"x={x_pos}:y={y_pos}:format=auto[{next_stream}]"
                )
                current_stream = next_stream
            elif has_neutral:
                # Only neutral pose available - use it always
                next_stream = f"{current_stream}_{role}"
                filters.append(
                    f"[{current_stream}][char_{role}_neutral]overlay="
                    f"x={x_pos}:y={y_pos}:format=auto[{next_stream}]"
                )
                current_stream = next_stream
            else:
                # Use first available pose
                first_pose = next(iter(poses.keys()))
                next_stream = f"{current_stream}_{role}"
                filters.append(
                    f"[{current_stream}][char_{role}_{first_pose}]overlay="
                    f"x={x_pos}:y={y_pos}:format=auto[{next_stream}]"
                )
                current_stream = next_stream

        # Add text overlays for each line with timing
        for i, (line, (start_time, end_time, _)) in enumerate(
            zip(script.lines, line_timings)
        ):
            next_stream = f"v{i}"
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
                f"enable='between(t,{start_time:.2f},{end_time:.2f})':"
                f"alpha='if(lt(t-{start_time:.2f},{fade_duration}),(t-{start_time:.2f})/{fade_duration},1)',"
                f"drawtext="
                f"text='{self._escape_text(wrapped_text)}':"
                f"fontsize=36:"
                f"fontcolor=white:"
                f"x=(w-text_w)/2:"
                f"y=h-220:"
                f"enable='between(t,{start_time:.2f},{end_time:.2f})':"
                f"alpha='if(lt(t-{start_time:.2f},{fade_duration}),(t-{start_time:.2f})/{fade_duration},1)'"
                f"[{next_stream}]"
            )

            filters.append(text_filter)
            current_stream = next_stream

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
