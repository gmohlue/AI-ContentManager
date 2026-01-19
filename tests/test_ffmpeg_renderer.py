"""Tests for FFmpeg Renderer."""

import pytest
from pathlib import Path

from contentmanager.core.content.video_pipeline.ffmpeg_renderer import FFmpegRenderer
from contentmanager.core.content.video_pipeline.models import (
    DialogueScript,
    DialogueLine,
    CharacterRole,
    ContextStyle,
)


@pytest.fixture
def ffmpeg_renderer():
    """Create an FFmpegRenderer instance."""
    return FFmpegRenderer(
        ffmpeg_path="ffmpeg",
        ffprobe_path="ffprobe",
        width=1080,
        height=1920,
        fps=30,
    )


@pytest.fixture
def sample_script():
    """Create a sample dialogue script for testing."""
    return DialogueScript(
        topic="Test Topic",
        context_style=ContextStyle.TECH,
        lines=[
            DialogueLine(
                speaker_role=CharacterRole.QUESTIONER,
                speaker_name="Thabo",
                line="What is machine learning?",
                pose="standing",
                scene_number=1,
            ),
            DialogueLine(
                speaker_role=CharacterRole.EXPLAINER,
                speaker_name="Lerato",
                line="Machine learning is a subset of AI.",
                pose="thinking",
                scene_number=2,
            ),
            DialogueLine(
                speaker_role=CharacterRole.QUESTIONER,
                speaker_name="Thabo",
                line="How does it work?",
                pose="standing",
                scene_number=3,
            ),
        ],
        takeaway="Machine learning is powerful!",
        target_duration_seconds=45,
    )


class TestFFmpegRendererInit:
    """Test FFmpegRenderer initialization."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        renderer = FFmpegRenderer()

        assert renderer.ffmpeg_path == "ffmpeg"
        assert renderer.ffprobe_path == "ffprobe"
        assert renderer.width == 1080
        assert renderer.height == 1920
        assert renderer.fps == 30

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        renderer = FFmpegRenderer(
            ffmpeg_path="/usr/bin/ffmpeg",
            ffprobe_path="/usr/bin/ffprobe",
            width=1920,
            height=1080,
            fps=60,
        )

        assert renderer.ffmpeg_path == "/usr/bin/ffmpeg"
        assert renderer.ffprobe_path == "/usr/bin/ffprobe"
        assert renderer.width == 1920
        assert renderer.height == 1080
        assert renderer.fps == 60

    def test_init_tiktok_dimensions(self):
        """Test initialization with TikTok portrait dimensions."""
        renderer = FFmpegRenderer(width=1080, height=1920)

        assert renderer.width == 1080
        assert renderer.height == 1920
        assert renderer.height > renderer.width  # Portrait orientation


class TestTextEscaping:
    """Test text escaping for FFmpeg drawtext filter."""

    def test_escape_text_simple(self, ffmpeg_renderer):
        """Test escaping simple text without special characters."""
        text = "Hello World"
        escaped = ffmpeg_renderer._escape_text(text)
        assert escaped == "Hello World"

    def test_escape_text_backslash(self, ffmpeg_renderer):
        """Test escaping backslashes."""
        text = "Path\\to\\file"
        escaped = ffmpeg_renderer._escape_text(text)
        assert "\\\\" in escaped
        assert escaped == "Path\\\\to\\\\file"

    def test_escape_text_single_quote(self, ffmpeg_renderer):
        """Test escaping single quotes."""
        text = "It's a test"
        escaped = ffmpeg_renderer._escape_text(text)
        assert "'\\''" in escaped

    def test_escape_text_colon(self, ffmpeg_renderer):
        """Test escaping colons."""
        text = "Time: 10:30"
        escaped = ffmpeg_renderer._escape_text(text)
        assert "\\:" in escaped
        assert escaped == "Time\\: 10\\:30"

    def test_escape_text_percent(self, ffmpeg_renderer):
        """Test escaping percent signs."""
        text = "100% complete"
        escaped = ffmpeg_renderer._escape_text(text)
        assert "\\%" in escaped
        assert escaped == "100\\% complete"

    def test_escape_text_multiple_special_chars(self, ffmpeg_renderer):
        """Test escaping multiple special characters."""
        text = "It's 100%: success\\victory"
        escaped = ffmpeg_renderer._escape_text(text)

        assert "'\\''" in escaped  # Single quote
        assert "\\%" in escaped  # Percent
        assert "\\:" in escaped  # Colon
        assert "\\\\" in escaped  # Backslash

    def test_escape_text_empty_string(self, ffmpeg_renderer):
        """Test escaping empty string."""
        text = ""
        escaped = ffmpeg_renderer._escape_text(text)
        assert escaped == ""

    def test_escape_text_unicode(self, ffmpeg_renderer):
        """Test that unicode characters are preserved."""
        text = "Café résumé"
        escaped = ffmpeg_renderer._escape_text(text)
        assert "Café résumé" in escaped


class TestBuildFilterComplex:
    """Test building FFmpeg filter complex."""

    def test_build_filter_complex_basic(self, ffmpeg_renderer, sample_script):
        """Test building basic filter complex."""
        filter_complex = ffmpeg_renderer._build_filter_complex(sample_script)

        assert filter_complex is not None
        assert isinstance(filter_complex, str)
        assert len(filter_complex) > 0

    def test_build_filter_complex_includes_scaling(self, ffmpeg_renderer, sample_script):
        """Test that filter includes background scaling."""
        filter_complex = ffmpeg_renderer._build_filter_complex(sample_script)

        assert "scale=" in filter_complex
        assert "1080:1920" in filter_complex
        assert "[bg]" in filter_complex

    def test_build_filter_complex_includes_text_overlays(self, ffmpeg_renderer, sample_script):
        """Test that filter includes text overlays for each line."""
        filter_complex = ffmpeg_renderer._build_filter_complex(sample_script)

        assert "drawtext=" in filter_complex
        assert "What is machine learning" in filter_complex
        assert "Machine learning is a subset of AI" in filter_complex
        assert "How does it work" in filter_complex

    def test_build_filter_complex_includes_fade_effect(self, ffmpeg_renderer, sample_script):
        """Test that text includes fade-in effect."""
        filter_complex = ffmpeg_renderer._build_filter_complex(sample_script)

        assert "alpha=" in filter_complex
        assert "enable=" in filter_complex
        assert "between(t," in filter_complex

    def test_build_filter_complex_has_output_label(self, ffmpeg_renderer, sample_script):
        """Test that filter has final output label."""
        filter_complex = ffmpeg_renderer._build_filter_complex(sample_script)

        assert "[outv]" in filter_complex

    def test_build_filter_complex_empty_lines(self, ffmpeg_renderer):
        """Test filter with empty lines list."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.TECH,
            lines=[],
            takeaway="Nothing",
        )

        filter_complex = ffmpeg_renderer._build_filter_complex(script)

        # Should still have scaling and output
        assert "scale=" in filter_complex
        assert "[outv]" in filter_complex

    def test_build_filter_complex_single_line(self, ffmpeg_renderer):
        """Test filter with single dialogue line."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.TECH,
            lines=[
                DialogueLine(
                    speaker_role=CharacterRole.QUESTIONER,
                    speaker_name="Q",
                    line="Single line",
                    scene_number=1,
                ),
            ],
            takeaway="Done",
        )

        filter_complex = ffmpeg_renderer._build_filter_complex(script)

        assert filter_complex.count("drawtext=") == 1

    def test_build_filter_complex_escapes_special_chars(self, ffmpeg_renderer):
        """Test that special characters in dialogue are escaped."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.TECH,
            lines=[
                DialogueLine(
                    speaker_role=CharacterRole.EXPLAINER,
                    speaker_name="E",
                    line="It's 100%: awesome!",
                    scene_number=1,
                ),
            ],
            takeaway="Great",
        )

        filter_complex = ffmpeg_renderer._build_filter_complex(script)

        # Check that text is escaped
        assert "'\\''" in filter_complex or "100\\%" in filter_complex


class TestBuildFFmpegCommand:
    """Test building complete FFmpeg command."""

    def test_build_command_basic_structure(self, ffmpeg_renderer, sample_script):
        """Test basic command structure."""
        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=Path("/tmp/output.mp4"),
            music_path=None,
        )

        assert isinstance(cmd, list)
        assert cmd[0] == "ffmpeg"
        assert "-y" in cmd  # Overwrite flag

    def test_build_command_includes_inputs(self, ffmpeg_renderer, sample_script):
        """Test that command includes input files."""
        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=Path("/tmp/output.mp4"),
            music_path=None,
        )

        assert "-i" in cmd
        assert "/tmp/background.jpg" in cmd
        assert "/tmp/voiceover.mp3" in cmd

    def test_build_command_with_music(self, ffmpeg_renderer, sample_script):
        """Test command with background music."""
        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=Path("/tmp/output.mp4"),
            music_path=Path("/tmp/music.mp3"),
        )

        assert "/tmp/music.mp3" in cmd

    def test_build_command_includes_filter_complex(self, ffmpeg_renderer, sample_script):
        """Test that command includes filter_complex."""
        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=Path("/tmp/output.mp4"),
            music_path=None,
        )

        assert "-filter_complex" in cmd

    def test_build_command_output_settings(self, ffmpeg_renderer, sample_script):
        """Test output encoding settings."""
        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=Path("/tmp/output.mp4"),
            music_path=None,
        )

        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-c:a" in cmd
        assert "aac" in cmd
        assert "-preset" in cmd
        assert "-crf" in cmd

    def test_build_command_includes_output_path(self, ffmpeg_renderer, sample_script):
        """Test that output path is included."""
        output_path = Path("/tmp/output.mp4")

        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=output_path,
            music_path=None,
        )

        assert str(output_path) in cmd

    def test_build_command_audio_mapping(self, ffmpeg_renderer, sample_script):
        """Test that audio is properly mapped from voiceover."""
        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=Path("/tmp/output.mp4"),
            music_path=None,
        )

        assert "-map" in cmd
        assert "[outv]" in cmd
        assert "1:a" in cmd  # Audio from second input (voiceover)

    def test_build_command_pixel_format(self, ffmpeg_renderer, sample_script):
        """Test that pixel format is set for compatibility."""
        cmd = ffmpeg_renderer._build_ffmpeg_command(
            script=sample_script,
            voiceover_path=Path("/tmp/voiceover.mp3"),
            background_path=Path("/tmp/background.jpg"),
            character_assets={},
            output_path=Path("/tmp/output.mp4"),
            music_path=None,
        )

        assert "-pix_fmt" in cmd
        assert "yuv420p" in cmd  # Common compatible format


class TestPositioning:
    """Test character and text positioning logic."""

    def test_questioner_positioning(self, ffmpeg_renderer):
        """Test that questioner text is positioned on the left."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.TECH,
            lines=[
                DialogueLine(
                    speaker_role=CharacterRole.QUESTIONER,
                    speaker_name="Q",
                    line="Question here",
                    scene_number=1,
                ),
            ],
            takeaway="Done",
        )

        filter_complex = ffmpeg_renderer._build_filter_complex(script)

        # Questioner should be positioned at x=50 (left side)
        assert "x=50" in filter_complex

    def test_explainer_positioning(self, ffmpeg_renderer):
        """Test that explainer text is positioned on the right."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.TECH,
            lines=[
                DialogueLine(
                    speaker_role=CharacterRole.EXPLAINER,
                    speaker_name="E",
                    line="Answer here",
                    scene_number=1,
                ),
            ],
            takeaway="Done",
        )

        filter_complex = ffmpeg_renderer._build_filter_complex(script)

        # Explainer should be positioned at x=width-50 (right side)
        # With width=1080, that's x=1030
        assert "x=1030" in filter_complex

    def test_mixed_positioning(self, ffmpeg_renderer):
        """Test positioning with both questioner and explainer."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.TECH,
            lines=[
                DialogueLine(
                    speaker_role=CharacterRole.QUESTIONER,
                    speaker_name="Q",
                    line="Q1",
                    scene_number=1,
                ),
                DialogueLine(
                    speaker_role=CharacterRole.EXPLAINER,
                    speaker_name="E",
                    line="A1",
                    scene_number=2,
                ),
            ],
            takeaway="Done",
        )

        filter_complex = ffmpeg_renderer._build_filter_complex(script)

        # Both positions should be present
        assert "x=50" in filter_complex  # Questioner
        assert "x=1030" in filter_complex  # Explainer


class TestFilterComplexStructure:
    """Test the structure and chain of filters."""

    def test_filter_complex_is_semicolon_separated(self, ffmpeg_renderer, sample_script):
        """Test that filter complex uses semicolon separators."""
        filter_complex = ffmpeg_renderer._build_filter_complex(sample_script)

        assert ";" in filter_complex
        # Should have at least: scale; drawtext1; drawtext2; drawtext3; copy
        assert filter_complex.count(";") >= 4

    def test_filter_complex_stream_labels(self, ffmpeg_renderer, sample_script):
        """Test that intermediate stream labels are created."""
        filter_complex = ffmpeg_renderer._build_filter_complex(sample_script)

        # Should have intermediate labels like [v0], [v1], etc.
        assert "[v0]" in filter_complex
        assert "[v1]" in filter_complex

    def test_filter_complex_proper_chaining(self, ffmpeg_renderer):
        """Test that filters are properly chained."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.TECH,
            lines=[
                DialogueLine(
                    speaker_role=CharacterRole.QUESTIONER,
                    speaker_name="Q",
                    line="Line 1",
                    scene_number=1,
                ),
                DialogueLine(
                    speaker_role=CharacterRole.EXPLAINER,
                    speaker_name="E",
                    line="Line 2",
                    scene_number=2,
                ),
            ],
            takeaway="Done",
        )

        filter_complex = ffmpeg_renderer._build_filter_complex(script)

        # [bg] -> [v0] -> [v1] -> [outv]
        assert "[bg]" in filter_complex
        assert "[v0]" in filter_complex
        assert "[v1]" in filter_complex
        assert "[outv]" in filter_complex
