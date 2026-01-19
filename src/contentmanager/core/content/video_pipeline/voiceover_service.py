"""Voiceover generation using Eleven Labs API."""

import logging
from pathlib import Path
from elevenlabs import ElevenLabs

from .models import (
    AudioSegment,
    CharacterRole,
    DialogueScript,
    VoiceoverResult,
)

logger = logging.getLogger(__name__)


class VoiceoverService:
    """Generates voiceovers using Eleven Labs API."""

    def __init__(
        self,
        api_key: str,
        questioner_voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
        explainer_voice_id: str = "EXAVITQu4vr4xnSDxMaL",
    ):
        self.client = ElevenLabs(api_key=api_key)
        self.voices = {
            CharacterRole.QUESTIONER: questioner_voice_id,
            CharacterRole.EXPLAINER: explainer_voice_id,
        }

    async def generate_voiceover(
        self,
        script: DialogueScript,
        output_dir: Path,
        voice_config: dict | None = None,
    ) -> VoiceoverResult:
        """Generate voiceover audio for each line in the script.

        Args:
            script: The dialogue script to voice
            output_dir: Directory to save audio files
            voice_config: Optional voice ID overrides

        Returns:
            VoiceoverResult with audio segments and combined file
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        voices = self.voices.copy()
        if voice_config:
            voices.update(voice_config)

        segments = []
        current_time = 0.0

        for line in script.lines:
            voice_id = voices[line.speaker_role]
            output_path = output_dir / f"scene_{line.scene_number:03d}.mp3"

            segment = await self.generate_segment(
                text=line.line,
                voice_id=voice_id,
                output_path=output_path,
            )

            segments.append(
                AudioSegment(
                    scene_number=line.scene_number,
                    speaker_role=line.speaker_role,
                    file_path=str(output_path),
                    duration_seconds=segment.duration_seconds,
                    start_time=current_time,
                )
            )

            current_time += segment.duration_seconds

        # Combine all segments into single audio file
        combined_path = output_dir / "combined_voiceover.mp3"
        await self._combine_audio_segments(segments, combined_path)

        return VoiceoverResult(
            segments=segments,
            combined_audio_path=str(combined_path),
            total_duration_seconds=current_time,
        )

    async def generate_segment(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
    ) -> AudioSegment:
        """Generate a single audio segment.

        Args:
            text: The text to convert to speech
            voice_id: Eleven Labs voice ID
            output_path: Path to save the audio file

        Returns:
            AudioSegment with file path and duration
        """
        logger.info(f"Generating voiceover segment: {text[:50]}...")

        audio = self.client.text_to_speech.convert(
            voice_id=voice_id,
            text=text,
            model_id="eleven_multilingual_v2",
        )

        # Write audio to file
        with open(output_path, "wb") as f:
            for chunk in audio:
                f.write(chunk)

        # Get duration using ffprobe
        duration = await self._get_audio_duration(output_path)

        return AudioSegment(
            scene_number=0,  # Set by caller
            speaker_role=CharacterRole.QUESTIONER,  # Set by caller
            file_path=str(output_path),
            duration_seconds=duration,
        )

    async def list_voices(self) -> list[dict]:
        """List available voices from Eleven Labs.

        Returns:
            List of voice dictionaries with id, name, and preview_url
        """
        response = self.client.voices.get_all()
        return [
            {
                "id": voice.voice_id,
                "name": voice.name,
                "preview_url": voice.preview_url,
            }
            for voice in response.voices
        ]

    async def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file using ffprobe."""
        import subprocess

        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
        )
        return float(result.stdout.strip())

    async def _combine_audio_segments(
        self,
        segments: list[AudioSegment],
        output_path: Path,
    ) -> None:
        """Combine multiple audio segments into a single file."""
        import subprocess

        # Create file list for ffmpeg concat
        list_file = output_path.parent / "concat_list.txt"
        with open(list_file, "w") as f:
            for segment in segments:
                f.write(f"file '{segment.file_path}'\n")

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-c",
                "copy",
                str(output_path),
            ],
            check=True,
        )

        # Clean up list file
        list_file.unlink()
