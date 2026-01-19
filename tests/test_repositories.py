"""Tests for database repositories."""

import pytest
from datetime import datetime

from contentmanager.database.repositories.video_project import (
    VideoProjectRepository,
    CharacterRepository,
    AssetRepository,
)
from contentmanager.database.models import (
    VideoProject,
    Character,
    CharacterAsset,
    BackgroundAsset,
    MusicAsset,
    VideoScene,
)
from contentmanager.core.content.video_pipeline.models import (
    CharacterRole,
    ContextStyle,
    VideoProjectStatus,
)


class TestVideoProjectRepository:
    """Test VideoProjectRepository CRUD operations."""

    def test_create_video_project(self, db_session):
        """Test creating a new video project."""
        repo = VideoProjectRepository(db_session)

        # First create characters
        char_repo = CharacterRepository(db_session)
        questioner = char_repo.create(name="Thabo", role=CharacterRole.QUESTIONER.value)
        explainer = char_repo.create(name="Lerato", role=CharacterRole.EXPLAINER.value)

        project = repo.create(
            title="Test Video",
            topic="Introduction to Testing",
            context_style=ContextStyle.TECH.value,
            questioner_id=questioner.id,
            explainer_id=explainer.id,
        )

        assert project.id is not None
        assert project.title == "Test Video"
        assert project.topic == "Introduction to Testing"
        assert project.context_style == ContextStyle.TECH.value
        assert project.status == VideoProjectStatus.DRAFT
        assert project.questioner_id == questioner.id
        assert project.explainer_id == explainer.id

    def test_create_video_project_with_optional_fields(self, db_session):
        """Test creating video project with optional fields."""
        char_repo = CharacterRepository(db_session)
        asset_repo = AssetRepository(db_session)
        repo = VideoProjectRepository(db_session)

        questioner = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        explainer = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)
        music = asset_repo.create_music(
            name="Test Music", file_path="/tmp/music.mp3", duration_seconds=60.0
        )

        project = repo.create(
            title="Full Project",
            topic="Test",
            context_style=ContextStyle.FINANCE.value,
            questioner_id=questioner.id,
            explainer_id=explainer.id,
            background_music_id=music.id,
            document_id=99,
            tenant_id=1,
        )

        assert project.background_music_id == music.id
        assert project.document_id == 99
        assert project.tenant_id == 1

    def test_get_by_id(self, db_session):
        """Test retrieving project by ID."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        created = repo.create(
            title="Test", topic="Topic", context_style="tech",
            questioner_id=q.id, explainer_id=e.id
        )

        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == "Test"
        # Check relationships are loaded
        assert retrieved.questioner is not None
        assert retrieved.explainer is not None

    def test_get_by_id_not_found(self, db_session):
        """Test get_by_id returns None for non-existent ID."""
        repo = VideoProjectRepository(db_session)
        project = repo.get_by_id(9999)
        assert project is None

    def test_list_projects(self, db_session):
        """Test listing all projects."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        # Create multiple projects
        repo.create("Project 1", "Topic 1", "tech", q.id, e.id)
        repo.create("Project 2", "Topic 2", "finance", q.id, e.id)
        repo.create("Project 3", "Topic 3", "motivation", q.id, e.id)

        projects = repo.list_projects()

        assert len(projects) == 3
        # Should be ordered by created_at desc (newest first)
        assert projects[0].title == "Project 3"

    def test_list_projects_with_status_filter(self, db_session):
        """Test filtering projects by status."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        p1 = repo.create("Draft", "Topic", "tech", q.id, e.id)
        p2 = repo.create("Approved", "Topic", "tech", q.id, e.id)
        repo.update_status(p2.id, VideoProjectStatus.APPROVED)

        draft_projects = repo.list_projects(status=VideoProjectStatus.DRAFT)
        approved_projects = repo.list_projects(status=VideoProjectStatus.APPROVED)

        assert len(draft_projects) == 1
        assert draft_projects[0].id == p1.id
        assert len(approved_projects) == 1
        assert approved_projects[0].id == p2.id

    def test_list_projects_with_tenant_filter(self, db_session):
        """Test filtering projects by tenant_id."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        # Create projects for different tenants
        p1 = repo.create("T1 Project", "Topic", "tech", q.id, e.id, tenant_id=1)
        repo.create("T2 Project", "Topic", "tech", q.id, e.id, tenant_id=2)

        tenant1_projects = repo.list_projects(tenant_id=1)

        assert len(tenant1_projects) == 1
        assert tenant1_projects[0].id == p1.id

    def test_list_projects_pagination(self, db_session):
        """Test pagination with limit and offset."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        # Create 5 projects
        for i in range(5):
            repo.create(f"Project {i}", "Topic", "tech", q.id, e.id)

        page1 = repo.list_projects(limit=2, offset=0)
        page2 = repo.list_projects(limit=2, offset=2)

        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].id != page2[0].id

    def test_update_status(self, db_session):
        """Test updating project status."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)
        assert project.status == VideoProjectStatus.DRAFT

        updated = repo.update_status(project.id, VideoProjectStatus.APPROVED)

        assert updated is not None
        assert updated.status == VideoProjectStatus.APPROVED
        assert updated.error_message is None

    def test_update_status_with_error(self, db_session):
        """Test updating status with error message."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        updated = repo.update_status(
            project.id,
            VideoProjectStatus.FAILED,
            error_message="Generation failed",
        )

        assert updated.status == VideoProjectStatus.FAILED
        assert updated.error_message == "Generation failed"

    def test_update_status_not_found(self, db_session):
        """Test update_status returns None for non-existent project."""
        repo = VideoProjectRepository(db_session)
        result = repo.update_status(9999, VideoProjectStatus.COMPLETED)
        assert result is None

    def test_update_script(self, db_session):
        """Test updating project script."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        script_json = {"lines": [{"speaker": "Q", "line": "Hello"}]}
        updated = repo.update_script(project.id, script_json, "Takeaway message")

        assert updated is not None
        assert updated.script_json == script_json
        assert updated.takeaway == "Takeaway message"

    def test_approve_project(self, db_session):
        """Test approving a project."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        approved = repo.approve_project(project.id, reviewed_by="admin")

        assert approved is not None
        assert approved.status == VideoProjectStatus.APPROVED
        assert approved.reviewed_by == "admin"
        assert approved.reviewed_at is not None

    def test_approve_project_not_in_draft(self, db_session):
        """Test approving non-draft project returns None."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)
        repo.update_status(project.id, VideoProjectStatus.COMPLETED)

        # Try to approve completed project
        result = repo.approve_project(project.id, reviewed_by="admin")
        assert result is None

    def test_set_voiceover_path(self, db_session):
        """Test setting voiceover path."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        updated = repo.set_voiceover_path(project.id, "/tmp/voiceover.mp3")

        assert updated is not None
        assert updated.voiceover_path == "/tmp/voiceover.mp3"

    def test_update_voiceover_alias(self, db_session):
        """Test update_voiceover alias method."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        updated = repo.update_voiceover(project.id, "/tmp/voice.mp3")

        assert updated is not None
        assert updated.voiceover_path == "/tmp/voice.mp3"

    def test_set_output(self, db_session):
        """Test setting output video path and duration."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        updated = repo.set_output(project.id, "/tmp/video.mp4", 45.5)

        assert updated is not None
        assert updated.output_path == "/tmp/video.mp4"
        assert updated.duration_seconds == 45.5

    def test_update_output_alias(self, db_session):
        """Test update_output alias method."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        updated = repo.update_output(project.id, "/tmp/out.mp4", 60.0)

        assert updated is not None
        assert updated.output_path == "/tmp/out.mp4"
        assert updated.duration_seconds == 60.0

    def test_delete_project(self, db_session):
        """Test deleting a project."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)
        project_id = project.id

        deleted = repo.delete(project_id)

        assert deleted is True
        assert repo.get_by_id(project_id) is None

    def test_delete_project_not_found(self, db_session):
        """Test deleting non-existent project returns False."""
        repo = VideoProjectRepository(db_session)
        result = repo.delete(9999)
        assert result is False

    def test_add_scene(self, db_session):
        """Test adding a scene to a project."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)

        scene = repo.add_scene(
            project_id=project.id,
            scene_number=1,
            speaker_role=CharacterRole.QUESTIONER.value,
            line="What is this?",
            pose="standing",
        )

        assert scene.id is not None
        assert scene.project_id == project.id
        assert scene.scene_number == 1
        assert scene.speaker_role == CharacterRole.QUESTIONER.value
        assert scene.line == "What is this?"
        assert scene.pose == "standing"

    def test_update_scene_audio(self, db_session):
        """Test updating scene audio information."""
        char_repo = CharacterRepository(db_session)
        repo = VideoProjectRepository(db_session)

        q = char_repo.create(name="Q", role=CharacterRole.QUESTIONER.value)
        e = char_repo.create(name="E", role=CharacterRole.EXPLAINER.value)

        project = repo.create("Test", "Topic", "tech", q.id, e.id)
        scene = repo.add_scene(
            project.id, 1, CharacterRole.QUESTIONER.value, "Line", "standing"
        )

        updated = repo.update_scene_audio(
            scene_id=scene.id,
            voiceover_path="/tmp/scene1.mp3",
            start_time=0.0,
            duration_seconds=3.5,
        )

        assert updated is not None
        assert updated.voiceover_path == "/tmp/scene1.mp3"
        assert updated.start_time == 0.0
        assert updated.duration_seconds == 3.5


class TestCharacterRepository:
    """Test CharacterRepository CRUD operations."""

    def test_create_character(self, db_session):
        """Test creating a new character."""
        repo = CharacterRepository(db_session)

        character = repo.create(name="Thabo", role=CharacterRole.QUESTIONER.value)

        assert character.id is not None
        assert character.name == "Thabo"
        assert character.role == CharacterRole.QUESTIONER
        assert character.is_active is True
        assert character.tenant_id is None

    def test_create_character_with_tenant(self, db_session):
        """Test creating character with tenant_id."""
        repo = CharacterRepository(db_session)

        character = repo.create(
            name="Lerato",
            role=CharacterRole.EXPLAINER.value,
            tenant_id=5,
        )

        assert character.tenant_id == 5

    def test_get_by_id(self, db_session):
        """Test retrieving character by ID."""
        repo = CharacterRepository(db_session)

        created = repo.create(name="Test", role=CharacterRole.QUESTIONER.value)
        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test"

    def test_get_by_id_not_found(self, db_session):
        """Test get_by_id returns None for non-existent ID."""
        repo = CharacterRepository(db_session)
        character = repo.get_by_id(9999)
        assert character is None

    def test_list_characters(self, db_session):
        """Test listing all active characters."""
        repo = CharacterRepository(db_session)

        repo.create("Char1", CharacterRole.QUESTIONER.value)
        repo.create("Char2", CharacterRole.EXPLAINER.value)
        repo.create("Char3", CharacterRole.QUESTIONER.value)

        characters = repo.list_characters()

        assert len(characters) == 3

    def test_list_characters_by_tenant(self, db_session):
        """Test filtering characters by tenant."""
        repo = CharacterRepository(db_session)

        c1 = repo.create("T1 Char", CharacterRole.QUESTIONER.value, tenant_id=1)
        repo.create("T2 Char", CharacterRole.EXPLAINER.value, tenant_id=2)

        tenant1_chars = repo.list_characters(tenant_id=1)

        assert len(tenant1_chars) == 1
        assert tenant1_chars[0].id == c1.id

    def test_add_asset(self, db_session):
        """Test adding an asset to a character."""
        repo = CharacterRepository(db_session)

        character = repo.create("Test", CharacterRole.QUESTIONER.value)
        asset = repo.add_asset(
            character_id=character.id,
            pose="standing",
            file_path="/tmp/standing.png",
            file_size_bytes=102400,
        )

        assert asset.id is not None
        assert asset.character_id == character.id
        assert asset.pose == "standing"
        assert asset.file_path == "/tmp/standing.png"
        assert asset.file_size_bytes == 102400

    def test_add_multiple_assets(self, db_session):
        """Test adding multiple pose assets to a character."""
        repo = CharacterRepository(db_session)

        character = repo.create("Test", CharacterRole.EXPLAINER.value)

        poses = ["standing", "thinking", "pointing", "excited"]
        for pose in poses:
            repo.add_asset(
                character.id,
                pose,
                f"/tmp/{pose}.png",
                50000,
            )

        # Retrieve character with assets
        retrieved = repo.get_by_id(character.id)
        assert len(retrieved.assets) == 4

    def test_get_asset_by_id(self, db_session):
        """Test getting an asset by ID."""
        repo = CharacterRepository(db_session)

        character = repo.create("Test", CharacterRole.QUESTIONER.value)
        asset = repo.add_asset(character.id, "standing", "/tmp/file.png", 1000)

        retrieved = repo.get_asset_by_id(asset.id)

        assert retrieved is not None
        assert retrieved.id == asset.id

    def test_delete_asset(self, db_session):
        """Test deleting a character asset."""
        repo = CharacterRepository(db_session)

        character = repo.create("Test", CharacterRole.QUESTIONER.value)
        asset = repo.add_asset(character.id, "standing", "/tmp/file.png", 1000)
        asset_id = asset.id

        deleted = repo.delete_asset(asset_id)

        assert deleted is True
        assert repo.get_asset_by_id(asset_id) is None

    def test_delete_asset_not_found(self, db_session):
        """Test deleting non-existent asset returns False."""
        repo = CharacterRepository(db_session)
        result = repo.delete_asset(9999)
        assert result is False


class TestAssetRepository:
    """Test AssetRepository for backgrounds and music."""

    def test_create_background(self, db_session):
        """Test creating a background asset."""
        repo = AssetRepository(db_session)

        background = repo.create_background(
            name="Office Background",
            file_path="/tmp/office.jpg",
            context_style=ContextStyle.TECH.value,
        )

        assert background.id is not None
        assert background.name == "Office Background"
        assert background.file_path == "/tmp/office.jpg"
        assert background.context_style == ContextStyle.TECH.value

    def test_create_background_no_style(self, db_session):
        """Test creating background without context style."""
        repo = AssetRepository(db_session)

        background = repo.create_background(
            name="Generic Background",
            file_path="/tmp/generic.jpg",
        )

        assert background.context_style is None

    def test_create_music(self, db_session):
        """Test creating a music asset."""
        repo = AssetRepository(db_session)

        music = repo.create_music(
            name="Upbeat Track",
            file_path="/tmp/upbeat.mp3",
            duration_seconds=120.5,
            context_style=ContextStyle.MOTIVATION.value,
        )

        assert music.id is not None
        assert music.name == "Upbeat Track"
        assert music.file_path == "/tmp/upbeat.mp3"
        assert music.duration_seconds == 120.5
        assert music.context_style == ContextStyle.MOTIVATION.value

    def test_list_backgrounds(self, db_session):
        """Test listing all backgrounds."""
        repo = AssetRepository(db_session)

        repo.create_background("BG1", "/tmp/bg1.jpg")
        repo.create_background("BG2", "/tmp/bg2.jpg")

        backgrounds = repo.list_backgrounds()

        assert len(backgrounds) == 2

    def test_list_backgrounds_by_style(self, db_session):
        """Test filtering backgrounds by context style."""
        repo = AssetRepository(db_session)

        bg1 = repo.create_background(
            "Tech BG", "/tmp/tech.jpg", context_style=ContextStyle.TECH.value
        )
        repo.create_background(
            "Finance BG", "/tmp/finance.jpg", context_style=ContextStyle.FINANCE.value
        )

        tech_backgrounds = repo.list_backgrounds(context_style=ContextStyle.TECH.value)

        assert len(tech_backgrounds) == 1
        assert tech_backgrounds[0].id == bg1.id

    def test_list_music(self, db_session):
        """Test listing all music assets."""
        repo = AssetRepository(db_session)

        repo.create_music("Track1", "/tmp/t1.mp3", 60.0)
        repo.create_music("Track2", "/tmp/t2.mp3", 120.0)

        music = repo.list_music()

        assert len(music) == 2

    def test_list_music_by_style(self, db_session):
        """Test filtering music by context style."""
        repo = AssetRepository(db_session)

        m1 = repo.create_music(
            "Calm", "/tmp/calm.mp3", 90.0, context_style=ContextStyle.EDUCATIONAL.value
        )
        repo.create_music(
            "Energetic", "/tmp/energy.mp3", 60.0, context_style=ContextStyle.MOTIVATION.value
        )

        edu_music = repo.list_music(context_style=ContextStyle.EDUCATIONAL.value)

        assert len(edu_music) == 1
        assert edu_music[0].id == m1.id

    def test_get_background_by_id(self, db_session):
        """Test retrieving background by ID."""
        repo = AssetRepository(db_session)

        created = repo.create_background("Test", "/tmp/test.jpg")
        retrieved = repo.get_background_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_music_by_id(self, db_session):
        """Test retrieving music by ID."""
        repo = AssetRepository(db_session)

        created = repo.create_music("Test", "/tmp/test.mp3", 45.0)
        retrieved = repo.get_music_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    def test_delete_background(self, db_session):
        """Test deleting a background asset."""
        repo = AssetRepository(db_session)

        background = repo.create_background("Test", "/tmp/test.jpg")
        bg_id = background.id

        deleted = repo.delete_background(bg_id)

        assert deleted is True
        assert repo.get_background_by_id(bg_id) is None

    def test_delete_background_not_found(self, db_session):
        """Test deleting non-existent background returns False."""
        repo = AssetRepository(db_session)
        result = repo.delete_background(9999)
        assert result is False

    def test_delete_music(self, db_session):
        """Test deleting a music asset."""
        repo = AssetRepository(db_session)

        music = repo.create_music("Test", "/tmp/test.mp3", 30.0)
        music_id = music.id

        deleted = repo.delete_music(music_id)

        assert deleted is True
        assert repo.get_music_by_id(music_id) is None

    def test_delete_music_not_found(self, db_session):
        """Test deleting non-existent music returns False."""
        repo = AssetRepository(db_session)
        result = repo.delete_music(9999)
        assert result is False
