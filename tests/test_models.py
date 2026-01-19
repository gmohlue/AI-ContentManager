"""Tests for Pydantic models in video pipeline."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from contentmanager.core.content.video_pipeline.models import (
    ContextStyle,
    CharacterRole,
    VideoProjectStatus,
    DialogueLine,
    DialogueScript,
    AudioSegment,
    VoiceoverResult,
    RenderResult,
    VideoProjectCreate,
    VideoProjectResponse,
)


class TestEnums:
    """Test enum validation and values."""

    def test_context_style_values(self):
        """Test all ContextStyle enum values."""
        assert ContextStyle.MOTIVATION.value == "motivation"
        assert ContextStyle.FINANCE.value == "finance"
        assert ContextStyle.TECH.value == "tech"
        assert ContextStyle.EDUCATIONAL.value == "educational"

    def test_context_style_invalid(self):
        """Test invalid context style raises error."""
        with pytest.raises(ValueError):
            ContextStyle("invalid_style")

    def test_character_role_values(self):
        """Test all CharacterRole enum values."""
        assert CharacterRole.QUESTIONER.value == "questioner"
        assert CharacterRole.EXPLAINER.value == "explainer"

    def test_character_role_invalid(self):
        """Test invalid character role raises error."""
        with pytest.raises(ValueError):
            CharacterRole("narrator")

    def test_video_project_status_values(self):
        """Test all VideoProjectStatus enum values."""
        assert VideoProjectStatus.DRAFT.value == "draft"
        assert VideoProjectStatus.APPROVED.value == "approved"
        assert VideoProjectStatus.AUDIO_READY.value == "audio_ready"
        assert VideoProjectStatus.RENDERING.value == "rendering"
        assert VideoProjectStatus.COMPLETED.value == "completed"
        assert VideoProjectStatus.FAILED.value == "failed"

    def test_video_project_status_workflow_order(self):
        """Test status enum contains all expected workflow states."""
        statuses = [s.value for s in VideoProjectStatus]
        assert "draft" in statuses
        assert "approved" in statuses
        assert "audio_ready" in statuses
        assert "rendering" in statuses
        assert "completed" in statuses
        assert "failed" in statuses


class TestDialogueLine:
    """Test DialogueLine model validation."""

    def test_dialogue_line_valid(self):
        """Test creating a valid dialogue line."""
        line = DialogueLine(
            speaker_role=CharacterRole.QUESTIONER,
            speaker_name="Thabo",
            line="What is machine learning?",
            pose="standing",
            scene_number=1,
        )
        assert line.speaker_role == CharacterRole.QUESTIONER
        assert line.speaker_name == "Thabo"
        assert line.line == "What is machine learning?"
        assert line.pose == "standing"
        assert line.scene_number == 1

    def test_dialogue_line_default_pose(self):
        """Test default pose is 'standing'."""
        line = DialogueLine(
            speaker_role=CharacterRole.EXPLAINER,
            speaker_name="Lerato",
            line="It's a type of AI.",
            scene_number=2,
        )
        assert line.pose == "standing"

    def test_dialogue_line_custom_pose(self):
        """Test custom pose values."""
        line = DialogueLine(
            speaker_role=CharacterRole.EXPLAINER,
            speaker_name="Lerato",
            line="Let me explain...",
            pose="thinking",
            scene_number=1,
        )
        assert line.pose == "thinking"

    def test_dialogue_line_missing_required_fields(self):
        """Test missing required fields raises error."""
        with pytest.raises(ValidationError) as exc_info:
            DialogueLine(
                speaker_role=CharacterRole.QUESTIONER,
                speaker_name="Thabo",
                # Missing 'line' and 'scene_number'
            )
        errors = exc_info.value.errors()
        error_fields = {e["loc"][0] for e in errors}
        assert "line" in error_fields
        assert "scene_number" in error_fields


class TestDialogueScript:
    """Test DialogueScript model validation."""

    def test_dialogue_script_valid(self):
        """Test creating a valid dialogue script."""
        lines = [
            DialogueLine(
                speaker_role=CharacterRole.QUESTIONER,
                speaker_name="Thabo",
                line="What is AI?",
                scene_number=1,
            ),
            DialogueLine(
                speaker_role=CharacterRole.EXPLAINER,
                speaker_name="Lerato",
                line="AI is artificial intelligence.",
                scene_number=2,
            ),
        ]

        script = DialogueScript(
            topic="Introduction to AI",
            context_style=ContextStyle.TECH,
            lines=lines,
            takeaway="AI is a powerful technology.",
            target_duration_seconds=45,
        )

        assert script.topic == "Introduction to AI"
        assert script.context_style == ContextStyle.TECH
        assert len(script.lines) == 2
        assert script.takeaway == "AI is a powerful technology."
        assert script.target_duration_seconds == 45

    def test_dialogue_script_default_duration(self):
        """Test default target duration is 45 seconds."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.EDUCATIONAL,
            lines=[],
            takeaway="Test takeaway",
        )
        assert script.target_duration_seconds == 45

    def test_dialogue_script_empty_lines(self):
        """Test script can have empty lines list."""
        script = DialogueScript(
            topic="Test",
            context_style=ContextStyle.MOTIVATION,
            lines=[],
            takeaway="Keep learning!",
        )
        assert script.lines == []

    def test_dialogue_script_multiple_lines(self):
        """Test script with multiple dialogue lines."""
        lines = [
            DialogueLine(
                speaker_role=CharacterRole.QUESTIONER,
                speaker_name="Thabo",
                line=f"Question {i}",
                scene_number=i * 2 - 1,
            )
            for i in range(1, 6)
        ]

        script = DialogueScript(
            topic="Test Topic",
            context_style=ContextStyle.FINANCE,
            lines=lines,
            takeaway="Financial wisdom",
        )
        assert len(script.lines) == 5


class TestAudioSegment:
    """Test AudioSegment model validation."""

    def test_audio_segment_valid(self):
        """Test creating a valid audio segment."""
        segment = AudioSegment(
            scene_number=1,
            speaker_role=CharacterRole.QUESTIONER,
            file_path="/tmp/audio_1.mp3",
            duration_seconds=3.5,
            start_time=0.0,
        )
        assert segment.scene_number == 1
        assert segment.speaker_role == CharacterRole.QUESTIONER
        assert segment.file_path == "/tmp/audio_1.mp3"
        assert segment.duration_seconds == 3.5
        assert segment.start_time == 0.0

    def test_audio_segment_default_start_time(self):
        """Test default start_time is 0.0."""
        segment = AudioSegment(
            scene_number=1,
            speaker_role=CharacterRole.EXPLAINER,
            file_path="/tmp/audio.mp3",
            duration_seconds=2.0,
        )
        assert segment.start_time == 0.0


class TestVoiceoverResult:
    """Test VoiceoverResult model validation."""

    def test_voiceover_result_valid(self):
        """Test creating a valid voiceover result."""
        segments = [
            AudioSegment(
                scene_number=1,
                speaker_role=CharacterRole.QUESTIONER,
                file_path="/tmp/seg1.mp3",
                duration_seconds=3.0,
                start_time=0.0,
            ),
            AudioSegment(
                scene_number=2,
                speaker_role=CharacterRole.EXPLAINER,
                file_path="/tmp/seg2.mp3",
                duration_seconds=4.0,
                start_time=3.0,
            ),
        ]

        result = VoiceoverResult(
            segments=segments,
            combined_audio_path="/tmp/combined.mp3",
            total_duration_seconds=7.0,
        )

        assert len(result.segments) == 2
        assert result.combined_audio_path == "/tmp/combined.mp3"
        assert result.total_duration_seconds == 7.0

    def test_voiceover_result_empty_segments(self):
        """Test voiceover result with no segments."""
        result = VoiceoverResult(
            segments=[],
            combined_audio_path="/tmp/empty.mp3",
            total_duration_seconds=0.0,
        )
        assert result.segments == []


class TestRenderResult:
    """Test RenderResult model validation."""

    def test_render_result_valid(self):
        """Test creating a valid render result."""
        result = RenderResult(
            output_path="/tmp/video.mp4",
            duration_seconds=45.5,
            width=1080,
            height=1920,
            file_size_bytes=5242880,  # 5MB
        )

        assert result.output_path == "/tmp/video.mp4"
        assert result.duration_seconds == 45.5
        assert result.width == 1080
        assert result.height == 1920
        assert result.file_size_bytes == 5242880
        assert isinstance(result.rendered_at, datetime)

    def test_render_result_default_timestamp(self):
        """Test rendered_at has default timestamp."""
        result = RenderResult(
            output_path="/tmp/video.mp4",
            duration_seconds=30.0,
            width=1920,
            height=1080,
            file_size_bytes=1000000,
        )
        assert result.rendered_at is not None
        assert isinstance(result.rendered_at, datetime)

    def test_render_result_tiktok_format(self):
        """Test render result with TikTok portrait dimensions."""
        result = RenderResult(
            output_path="/tmp/tiktok_video.mp4",
            duration_seconds=60.0,
            width=1080,
            height=1920,  # 9:16 portrait
            file_size_bytes=10000000,
        )
        assert result.height > result.width  # Portrait orientation


class TestVideoProjectCreate:
    """Test VideoProjectCreate request model."""

    def test_video_project_create_valid(self):
        """Test creating a valid video project request."""
        request = VideoProjectCreate(
            title="My First Video",
            topic="Introduction to Python",
            context_style=ContextStyle.TECH,
            questioner_id=1,
            explainer_id=2,
            background_music_id=5,
            document_id=10,
        )

        assert request.title == "My First Video"
        assert request.topic == "Introduction to Python"
        assert request.context_style == ContextStyle.TECH
        assert request.questioner_id == 1
        assert request.explainer_id == 2
        assert request.background_music_id == 5
        assert request.document_id == 10

    def test_video_project_create_optional_fields(self):
        """Test optional fields default to None."""
        request = VideoProjectCreate(
            title="Simple Video",
            topic="Test Topic",
            context_style=ContextStyle.EDUCATIONAL,
            questioner_id=1,
            explainer_id=2,
        )

        assert request.background_music_id is None
        assert request.document_id is None

    def test_video_project_create_missing_required_fields(self):
        """Test missing required fields raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            VideoProjectCreate(
                title="Test",
                topic="Test Topic",
                # Missing context_style, questioner_id, explainer_id
            )
        errors = exc_info.value.errors()
        error_fields = {e["loc"][0] for e in errors}
        assert "context_style" in error_fields
        assert "questioner_id" in error_fields
        assert "explainer_id" in error_fields


class TestVideoProjectResponse:
    """Test VideoProjectResponse model."""

    def test_video_project_response_valid(self):
        """Test creating a valid video project response."""
        now = datetime.utcnow()
        response = VideoProjectResponse(
            id=1,
            title="Test Video",
            topic="Test Topic",
            context_style=ContextStyle.MOTIVATION,
            status=VideoProjectStatus.DRAFT,
            script_json={"lines": []},
            takeaway="Great lesson!",
            voiceover_path="/tmp/voiceover.mp3",
            output_path="/tmp/video.mp4",
            duration_seconds=45.0,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        assert response.id == 1
        assert response.title == "Test Video"
        assert response.status == VideoProjectStatus.DRAFT
        assert response.script_json == {"lines": []}
        assert response.duration_seconds == 45.0

    def test_video_project_response_optional_fields_none(self):
        """Test optional fields can be None."""
        now = datetime.utcnow()
        response = VideoProjectResponse(
            id=1,
            title="Draft Video",
            topic="Test",
            context_style=ContextStyle.TECH,
            status=VideoProjectStatus.DRAFT,
            script_json=None,
            takeaway=None,
            voiceover_path=None,
            output_path=None,
            duration_seconds=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

        assert response.script_json is None
        assert response.takeaway is None
        assert response.voiceover_path is None
        assert response.output_path is None
        assert response.duration_seconds is None

    def test_video_project_response_failed_status(self):
        """Test response with failed status and error message."""
        now = datetime.utcnow()
        response = VideoProjectResponse(
            id=5,
            title="Failed Video",
            topic="Test",
            context_style=ContextStyle.FINANCE,
            status=VideoProjectStatus.FAILED,
            error_message="Script generation failed: API error",
            created_at=now,
            updated_at=now,
        )

        assert response.status == VideoProjectStatus.FAILED
        assert "API error" in response.error_message

    def test_video_project_response_from_attributes(self):
        """Test Config.from_attributes is set."""
        assert VideoProjectResponse.model_config.get("from_attributes") is True
