"""Animated video rendering using FFmpeg with character motion."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .models import CharacterRole, DialogueScript, RenderResult

logger = logging.getLogger(__name__)


class AnimatedRenderer:
    """Renders videos with animated characters using FFmpeg."""

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
        """Render video with animated characters."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get voiceover duration
        total_duration = self._get_duration(voiceover_path)

        # Calculate line timings
        line_timings = self._calculate_line_timings(script, total_duration)

        # Build FFmpeg command
        cmd = self._build_animated_command(
            script=script,
            voiceover_path=voiceover_path,
            background_path=background_path,
            character_assets=character_assets,
            output_path=output_path,
            music_path=music_path,
            line_timings=line_timings,
            total_duration=total_duration,
        )

        logger.info(f"Rendering animated video: {output_path}")
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
        duration = self._get_duration(output_path)

        return RenderResult(
            output_path=str(output_path),
            duration_seconds=duration,
            width=self.width,
            height=self.height,
            file_size_bytes=file_size,
            rendered_at=datetime.utcnow(),
        )

    def _get_duration(self, file_path: Path) -> float:
        """Get duration of audio/video file."""
        result = subprocess.run(
            [
                self.ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(file_path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())

    def _calculate_line_timings(
        self, script: DialogueScript, total_duration: float
    ) -> list[tuple[float, float, str]]:
        """Calculate timing for each line."""
        total_chars = sum(len(line.line) for line in script.lines)
        timings = []
        current_time = 0.0

        for line in script.lines:
            line_duration = (len(line.line) / total_chars) * total_duration
            timings.append((current_time, current_time + line_duration, line.speaker_role.value))
            current_time += line_duration

        return timings

    def _build_animated_command(
        self,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        character_assets: dict[str, dict[str, Path]],
        output_path: Path,
        music_path: Path | None,
        line_timings: list[tuple[float, float, str]],
        total_duration: float,
    ) -> list[str]:
        """Build FFmpeg command with animated overlays."""
        cmd = [self.ffmpeg_path, "-y"]

        # Input 0: background
        cmd.extend(["-loop", "1", "-i", str(background_path)])

        # Input 1: voiceover
        cmd.extend(["-i", str(voiceover_path)])

        # Input 2+: character images
        input_index = 2
        char_inputs = {}

        for role, poses in character_assets.items():
            char_inputs[role] = {}
            for pose, path in poses.items():
                if path and path.exists():
                    cmd.extend(["-loop", "1", "-i", str(path)])
                    char_inputs[role][pose] = input_index
                    input_index += 1

        # Build filter complex
        filter_complex = self._build_animated_filter(
            script, char_inputs, line_timings, total_duration
        )

        cmd.extend(["-filter_complex", filter_complex])

        # Output settings
        cmd.extend([
            "-map", "[outv]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", str(total_duration),
            "-pix_fmt", "yuv420p",
            str(output_path),
        ])

        return cmd

    def _build_animated_filter(
        self,
        script: DialogueScript,
        char_inputs: dict[str, dict[str, int]],
        line_timings: list[tuple[float, float, str]],
        total_duration: float,
    ) -> str:
        """Build filter complex with character animations."""
        filters = []

        # Character settings
        char_height = 600
        positions = {
            "questioner": (100, self.height - char_height - 350),
            "explainer": (self.width - 500, self.height - char_height - 350),
        }

        # Build speaking windows for each role
        speaking_windows = {"questioner": [], "explainer": []}
        for start, end, role in line_timings:
            if role in speaking_windows:
                speaking_windows[role].append((start, end))

        # Scale background
        filters.append(
            f"[0:v]scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2[bg]"
        )

        current_stream = "bg"

        # Process each character with animation
        for role in ["questioner", "explainer"]:
            if role not in char_inputs or not char_inputs[role]:
                continue

            poses = char_inputs[role]
            base_x, base_y = positions[role]
            windows = speaking_windows[role]

            # Build talking time expression
            if windows:
                talk_expr = "+".join([
                    f"between(t,{s:.2f},{e:.2f})" for s, e in windows
                ])
            else:
                talk_expr = "0"

            # Get first available pose
            first_pose = next(iter(poses.keys()))
            input_idx = poses[first_pose]

            # Scale character with transparency
            filters.append(
                f"[{input_idx}:v]scale=-1:{char_height}:flags=lanczos,format=rgba[char_{role}_scaled]"
            )

            # Animation expressions:
            # - Idle: gentle bobbing (sine wave on Y, small amplitude)
            # - Talking: faster bobbing + slight horizontal shake

            # Idle bob: 5 pixel amplitude, 0.5 Hz frequency
            idle_bob = "5*sin(t*PI)"

            # Talking bob: 15 pixel amplitude, 3 Hz frequency + horizontal shake
            talk_bob = "15*sin(t*6*PI)"
            talk_shake = "3*sin(t*12*PI)"

            # Combined Y offset: idle when not talking, talk_bob when talking
            y_expr = f"{base_y}+({talk_expr})*({talk_bob})+((1-({talk_expr}))*({idle_bob}))"

            # X offset: only shake when talking
            x_expr = f"{base_x}+({talk_expr})*({talk_shake})"

            # Overlay with animated position
            next_stream = f"v_{role}"
            filters.append(
                f"[{current_stream}][char_{role}_scaled]overlay="
                f"x='{x_expr}':y='{y_expr}':format=auto[{next_stream}]"
            )
            current_stream = next_stream

        # Add text overlays
        for i, (line, (start_time, end_time, _)) in enumerate(
            zip(script.lines, line_timings)
        ):
            next_stream = f"txt{i}"
            fade_dur = 0.3

            # Text styling
            wrapped = self._wrap_text(line.line, 38)
            speaker = f"{line.speaker_name}:"

            # Text with background box for readability
            text_filter = (
                f"[{current_stream}]"
                f"drawbox=x=0:y=h-320:w=w:h=320:color=black@0.6:t=fill:"
                f"enable='between(t,{start_time:.2f},{end_time:.2f})',"
                f"drawtext=text='{self._escape(speaker)}':"
                f"fontsize=36:fontcolor=yellow:x=(w-text_w)/2:y=h-290:"
                f"enable='between(t,{start_time:.2f},{end_time:.2f})':"
                f"alpha='min((t-{start_time:.2f})/{fade_dur},1)',"
                f"drawtext=text='{self._escape(wrapped)}':"
                f"fontsize=40:fontcolor=white:x=(w-text_w)/2:y=h-240:"
                f"enable='between(t,{start_time:.2f},{end_time:.2f})':"
                f"alpha='min((t-{start_time:.2f})/{fade_dur},1)'"
                f"[{next_stream}]"
            )
            filters.append(text_filter)
            current_stream = next_stream

        # Final output
        filters.append(f"[{current_stream}]copy[outv]")

        return ";".join(filters)

    def _wrap_text(self, text: str, max_chars: int = 38) -> str:
        """Wrap text for display."""
        words = text.split()
        lines, current = [], []
        length = 0

        for word in words:
            if length + len(word) + 1 <= max_chars:
                current.append(word)
                length += len(word) + 1
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
                length = len(word)

        if current:
            lines.append(" ".join(current))

        return "\\n".join(lines)

    def _escape(self, text: str) -> str:
        """Escape text for FFmpeg drawtext."""
        return (
            text.replace("\\", "\\\\")
            .replace("'", "'\\''")
            .replace(":", "\\:")
            .replace("%", "\\%")
        )
