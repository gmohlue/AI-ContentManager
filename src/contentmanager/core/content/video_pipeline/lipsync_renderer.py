"""Lip-sync video rendering with animated mouth movement."""

import logging
import subprocess
from datetime import datetime
from pathlib import Path

from .models import DialogueScript, RenderResult

logger = logging.getLogger(__name__)


class LipSyncRenderer:
    """Renders videos with lip-synced character animation."""

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
        """Render video with lip-synced characters."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        total_duration = self._get_duration(voiceover_path)
        line_timings = self._calculate_line_timings(script, total_duration)

        cmd = self._build_command(
            script, voiceover_path, background_path,
            character_assets, output_path, line_timings, total_duration
        )

        logger.info(f"Rendering lip-sync video: {output_path}")

        process = subprocess.run(cmd, capture_output=True, text=True)

        if process.returncode != 0:
            logger.error(f"FFmpeg error: {process.stderr}")
            raise RuntimeError(f"FFmpeg rendering failed: {process.stderr}")

        return RenderResult(
            output_path=str(output_path),
            duration_seconds=self._get_duration(output_path),
            width=self.width,
            height=self.height,
            file_size_bytes=output_path.stat().st_size,
            rendered_at=datetime.utcnow(),
        )

    def _get_duration(self, path: Path) -> float:
        result = subprocess.run(
            [self.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True,
        )
        return float(result.stdout.strip())

    def _calculate_line_timings(self, script: DialogueScript, total: float):
        total_chars = sum(len(l.line) for l in script.lines)
        timings, current = [], 0.0
        for line in script.lines:
            dur = (len(line.line) / total_chars) * total
            timings.append((current, current + dur, line.speaker_role.value))
            current += dur
        return timings

    def _build_command(
        self, script, voiceover_path, background_path,
        character_assets, output_path, line_timings, total_duration
    ):
        cmd = [self.ffmpeg_path, "-y"]

        # Input 0: background
        cmd.extend(["-loop", "1", "-i", str(background_path)])

        # Input 1: voiceover
        cmd.extend(["-i", str(voiceover_path)])

        # Inputs 2+: character mouth frames
        # We need mouth_closed and mouth_open for each character
        input_map = {}  # {role: {'closed': idx, 'open': idx}}
        idx = 2

        for role in ["questioner", "explainer"]:
            if role not in character_assets:
                continue
            poses = character_assets[role]
            input_map[role] = {}

            # Prefer mouth_closed/mouth_open, fallback to neutral/talking
            closed_key = "mouth_closed" if "mouth_closed" in poses else "neutral"
            open_key = "mouth_open" if "mouth_open" in poses else "talking"

            if closed_key in poses and poses[closed_key].exists():
                cmd.extend(["-loop", "1", "-i", str(poses[closed_key])])
                input_map[role]['closed'] = idx
                idx += 1

            if open_key in poses and poses[open_key].exists():
                cmd.extend(["-loop", "1", "-i", str(poses[open_key])])
                input_map[role]['open'] = idx
                idx += 1

        filter_complex = self._build_filter(script, input_map, line_timings)
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

    def _build_filter(self, script, input_map, line_timings):
        filters = []
        h = self.height
        w = self.width
        char_h = 550

        # Positions
        pos = {
            "questioner": (80, h - char_h - 380),
            "explainer": (w - 480, h - char_h - 380),
        }

        # Build speaking windows
        windows = {"questioner": [], "explainer": []}
        for s, e, r in line_timings:
            if r in windows:
                windows[r].append((s, e))

        # Scale background
        filters.append(
            f"[0:v]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2[bg]"
        )

        current = "bg"

        # Process each character with lip sync
        for role in ["questioner", "explainer"]:
            if role not in input_map:
                continue

            mapping = input_map[role]
            if 'closed' not in mapping or 'open' not in mapping:
                continue

            x, y = pos[role]
            ws = windows[role]

            # Build speaking condition
            if ws:
                speak_cond = "+".join([f"between(t\\,{s:.2f}\\,{e:.2f})" for s, e in ws])
            else:
                speak_cond = "0"

            # Scale both mouth frames
            filters.append(f"[{mapping['closed']}:v]scale=-1:{char_h}:flags=lanczos,format=rgba[{role}_closed]")
            filters.append(f"[{mapping['open']}:v]scale=-1:{char_h}:flags=lanczos,format=rgba[{role}_open]")

            # Lip sync: alternate mouth open/closed at ~8Hz when speaking
            # Use mod(t*8,1)<0.5 to create 8Hz oscillation
            # When speaking: show open mouth 50% of time (rapid switching)
            # When not speaking: always show closed mouth

            # Mouth closed overlay (show when NOT speaking OR when speaking but in "closed" phase)
            # closed_show = not_speaking OR (speaking AND mod phase < 0.5)
            closed_enable = f"(1-({speak_cond}))+({speak_cond})*(1-lt(mod(t*8\\,1)\\,0.5))"

            next_stream = f"{current}_{role}_c"
            filters.append(
                f"[{current}][{role}_closed]overlay="
                f"x={x}+8*sin(t*4):y={y}+6*sin(t*3):"
                f"enable='{closed_enable}'[{next_stream}]"
            )
            current = next_stream

            # Mouth open overlay (show when speaking AND in "open" phase)
            open_enable = f"({speak_cond})*lt(mod(t*8\\,1)\\,0.5)"

            next_stream = f"{current}_o"
            filters.append(
                f"[{current}][{role}_open]overlay="
                f"x={x}+8*sin(t*4):y={y}+6*sin(t*3)+({speak_cond})*4*sin(t*12):"
                f"enable='{open_enable}'[{next_stream}]"
            )
            current = next_stream

        # Text overlays with background
        for i, (line, (start, end, _)) in enumerate(zip(script.lines, line_timings)):
            nxt = f"txt{i}"
            text = self._wrap(line.line, 36)
            speaker = f"{line.speaker_name}:"

            filters.append(
                f"[{current}]"
                f"drawbox=x=0:y={h-340}:w={w}:h=340:color=black@0.75:t=fill:"
                f"enable='between(t\\,{start:.2f}\\,{end:.2f})',"
                f"drawtext=text='{self._esc(speaker)}':"
                f"fontsize=38:fontcolor=#FFD700:x=(w-text_w)/2:y={h-310}:"
                f"enable='between(t\\,{start:.2f}\\,{end:.2f})',"
                f"drawtext=text='{self._esc(text)}':"
                f"fontsize=42:fontcolor=white:x=(w-text_w)/2:y={h-260}:"
                f"enable='between(t\\,{start:.2f}\\,{end:.2f})'"
                f"[{nxt}]"
            )
            current = nxt

        filters.append(f"[{current}]null[outv]")
        return ";".join(filters)

    def _wrap(self, text, max_chars=36):
        words, lines, cur, length = text.split(), [], [], 0
        for word in words:
            if length + len(word) + 1 <= max_chars:
                cur.append(word)
                length += len(word) + 1
            else:
                if cur: lines.append(" ".join(cur))
                cur, length = [word], len(word)
        if cur: lines.append(" ".join(cur))
        return "\\n".join(lines)

    def _esc(self, text):
        return text.replace("\\", "\\\\").replace("'", "'\\''").replace(":", "\\:").replace("%", "\\%")
