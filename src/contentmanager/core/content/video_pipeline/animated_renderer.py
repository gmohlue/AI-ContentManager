"""Animated video rendering using FFmpeg with character motion."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .models import DialogueScript, RenderResult

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
        character_assets: dict[str, dict[str, Path]],
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
        cmd = self._build_command(
            script=script,
            voiceover_path=voiceover_path,
            background_path=background_path,
            character_assets=character_assets,
            output_path=output_path,
            line_timings=line_timings,
            total_duration=total_duration,
        )

        logger.info(f"Rendering animated video: {output_path}")

        # Log the filter for debugging
        filter_idx = cmd.index("-filter_complex") + 1
        logger.debug(f"Filter complex: {cmd[filter_idx][:500]}...")

        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            logger.error(f"FFmpeg error: {process.stderr}")
            raise RuntimeError(f"FFmpeg rendering failed: {process.stderr}")

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
        result = subprocess.run(
            [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(file_path)],
            capture_output=True, text=True,
        )
        return float(result.stdout.strip())

    def _calculate_line_timings(
        self, script: DialogueScript, total_duration: float
    ) -> list[tuple[float, float, str]]:
        total_chars = sum(len(line.line) for line in script.lines)
        timings = []
        current = 0.0
        for line in script.lines:
            dur = (len(line.line) / total_chars) * total_duration
            timings.append((current, current + dur, line.speaker_role.value))
            current += dur
        return timings

    def _build_command(
        self,
        script: DialogueScript,
        voiceover_path: Path,
        background_path: Path,
        character_assets: dict[str, dict[str, Path]],
        output_path: Path,
        line_timings: list[tuple[float, float, str]],
        total_duration: float,
    ) -> list[str]:
        cmd = [self.ffmpeg_path, "-y"]

        # Input 0: background
        cmd.extend(["-loop", "1", "-i", str(background_path)])

        # Input 1: voiceover
        cmd.extend(["-i", str(voiceover_path)])

        # Input 2+: character images
        input_idx = 2
        char_inputs = {}
        for role, poses in character_assets.items():
            char_inputs[role] = {}
            for pose, path in poses.items():
                if path and path.exists():
                    cmd.extend(["-loop", "1", "-i", str(path)])
                    char_inputs[role][pose] = input_idx
                    input_idx += 1

        # Build filter
        filter_complex = self._build_filter(script, char_inputs, line_timings)
        cmd.extend(["-filter_complex", filter_complex])

        cmd.extend([
            "-map", "[outv]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(total_duration),
            "-pix_fmt", "yuv420p",
            str(output_path),
        ])

        return cmd

    def _build_filter(
        self,
        script: DialogueScript,
        char_inputs: dict[str, dict[str, int]],
        line_timings: list[tuple[float, float, str]],
    ) -> str:
        filters = []
        char_height = 600

        # Character positions
        q_x, q_y = 100, self.height - char_height - 350
        e_x, e_y = self.width - 500, self.height - char_height - 350

        # Build speaking time conditions for each role
        q_windows = [(s, e) for s, e, r in line_timings if r == "questioner"]
        e_windows = [(s, e) for s, e, r in line_timings if r == "explainer"]

        # Scale background
        filters.append(
            f"[0:v]scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,"
            f"pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2[bg]"
        )

        current = "bg"

        # Process questioner
        if "questioner" in char_inputs and char_inputs["questioner"]:
            pose = next(iter(char_inputs["questioner"].keys()))
            idx = char_inputs["questioner"][pose]

            # Scale character
            filters.append(
                f"[{idx}:v]scale=-1:{char_height}:flags=lanczos,format=rgba[q_scaled]"
            )

            # Build talking condition
            if q_windows:
                talk_cond = "+".join([f"between(t\\,{s:.2f}\\,{e:.2f})" for s, e in q_windows])
            else:
                talk_cond = "0"

            # Animated overlay: bob when idle, bounce+shake when talking
            # Using simpler expressions with escaped commas
            x_expr = f"{q_x}+({talk_cond})*10*sin(t*20)"
            y_expr = f"{q_y}+10*sin(t*3)+({talk_cond})*20*sin(t*15)"

            filters.append(
                f"[{current}][q_scaled]overlay=x='{x_expr}':y='{y_expr}'[v_q]"
            )
            current = "v_q"

        # Process explainer
        if "explainer" in char_inputs and char_inputs["explainer"]:
            pose = next(iter(char_inputs["explainer"].keys()))
            idx = char_inputs["explainer"][pose]

            filters.append(
                f"[{idx}:v]scale=-1:{char_height}:flags=lanczos,format=rgba[e_scaled]"
            )

            if e_windows:
                talk_cond = "+".join([f"between(t\\,{s:.2f}\\,{e:.2f})" for s, e in e_windows])
            else:
                talk_cond = "0"

            x_expr = f"{e_x}+({talk_cond})*10*sin(t*20)"
            y_expr = f"{e_y}+10*sin(t*3)+({talk_cond})*20*sin(t*15)"

            filters.append(
                f"[{current}][e_scaled]overlay=x='{x_expr}':y='{y_expr}'[v_e]"
            )
            current = "v_e"

        # Text overlays
        for i, (line, (start, end, _)) in enumerate(zip(script.lines, line_timings)):
            nxt = f"txt{i}"
            wrapped = self._wrap_text(line.line, 38)
            speaker = f"{line.speaker_name}:"

            txt_filter = (
                f"[{current}]"
                f"drawbox=x=0:y={self.height-320}:w={self.width}:h=320:color=black@0.7:t=fill:"
                f"enable='between(t\\,{start:.2f}\\,{end:.2f})',"
                f"drawtext=text='{self._escape(speaker)}':"
                f"fontsize=36:fontcolor=yellow:x=(w-text_w)/2:y={self.height-290}:"
                f"enable='between(t\\,{start:.2f}\\,{end:.2f})',"
                f"drawtext=text='{self._escape(wrapped)}':"
                f"fontsize=40:fontcolor=white:x=(w-text_w)/2:y={self.height-230}:"
                f"enable='between(t\\,{start:.2f}\\,{end:.2f})'"
                f"[{nxt}]"
            )
            filters.append(txt_filter)
            current = nxt

        filters.append(f"[{current}]null[outv]")
        return ";".join(filters)

    def _wrap_text(self, text: str, max_chars: int = 38) -> str:
        words = text.split()
        lines, cur = [], []
        length = 0
        for word in words:
            if length + len(word) + 1 <= max_chars:
                cur.append(word)
                length += len(word) + 1
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [word]
                length = len(word)
        if cur:
            lines.append(" ".join(cur))
        return "\\n".join(lines)

    def _escape(self, text: str) -> str:
        return (
            text.replace("\\", "\\\\")
            .replace("'", "'\\''")
            .replace(":", "\\:")
            .replace("%", "\\%")
        )
