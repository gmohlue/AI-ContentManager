"""Tests for API endpoints using FastAPI TestClient."""

import pytest
from io import BytesIO
from unittest.mock import Mock, patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from contentmanager.dashboard.routers.video_projects import router, get_db
from contentmanager.database.repositories.video_project import (
    VideoProjectRepository,
    CharacterRepository,
    AssetRepository,
)
from contentmanager.core.content.video_pipeline.models import (
    CharacterRole,
    ContextStyle,
    VideoProjectStatus,
)


# Create a test app with the router
app = FastAPI()
app.include_router(router)


@pytest.fixture
def client(db_session_factory):
    """Create a test client with database session override.

    Uses db_session_factory to create sessions that work across threads.
    """
    def override_get_db():
        session = db_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_characters(db_session_factory):
    """Create sample characters for testing.

    Returns a dict with character IDs to avoid detached instance errors.
    """
    session = db_session_factory()
    try:
        char_repo = CharacterRepository(session)

        questioner = char_repo.create(name="Thabo", role=CharacterRole.QUESTIONER)
        explainer = char_repo.create(name="Lerato", role=CharacterRole.EXPLAINER)

        # Return IDs to avoid detached instance errors
        return {
            "questioner_id": questioner.id,
            "explainer_id": explainer.id,
        }
    finally:
        session.close()


class TestCharacterEndpoints:
    """Test character-related endpoints."""

    def test_create_character(self, client):
        """Test POST /characters endpoint."""
        response = client.post(
            "/api/video/characters",
            params={
                "name": "Thabo",
                "role": "questioner",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Thabo"
        assert data["role"] == "questioner"
        assert "id" in data

    def test_create_character_explainer_role(self, client):
        """Test creating character with explainer role."""
        response = client.post(
            "/api/video/characters",
            params={
                "name": "Lerato",
                "role": "explainer",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "explainer"

    def test_list_characters_empty(self, client):
        """Test GET /characters with no characters."""
        response = client.get("/api/video/characters")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_characters(self, client, sample_characters):
        """Test GET /characters returns all characters."""
        response = client.get("/api/video/characters")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        names = {char["name"] for char in data}
        assert "Thabo" in names
        assert "Lerato" in names

    @patch("contentmanager.dashboard.routers.video_projects.asset_manager")
    def test_upload_character_asset(self, mock_asset_manager, client, sample_characters):
        """Test POST /characters/{id}/assets endpoint."""
        # Mock the asset manager save method
        mock_path = Mock()
        mock_path.stat.return_value.st_size = 1024
        mock_asset_manager.save_character_asset = AsyncMock(return_value=mock_path)

        character_id = sample_characters["questioner_id"]

        # Create a fake file
        file_data = BytesIO(b"fake image data")
        files = {"file": ("standing.png", file_data, "image/png")}

        response = client.post(
            f"/api/video/characters/{character_id}/assets",
            params={"pose": "standing"},
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pose"] == "standing"
        assert "file_path" in data

    def test_upload_character_asset_not_found(self, client):
        """Test uploading asset to non-existent character."""
        file_data = BytesIO(b"fake image")
        files = {"file": ("pose.png", file_data, "image/png")}

        response = client.post(
            "/api/video/characters/9999/assets",
            params={"pose": "standing"},
            files=files,
        )

        assert response.status_code == 404
        assert "Character not found" in response.json()["detail"]

    @patch("contentmanager.dashboard.routers.video_projects.asset_manager")
    def test_delete_character_asset(self, mock_asset_manager, client, db_session_factory, sample_characters):
        """Test DELETE /characters/{id}/assets/{asset_id} endpoint."""
        mock_asset_manager.delete_asset = AsyncMock(return_value=True)

        session = db_session_factory()
        char_repo = CharacterRepository(session)
        character_id = sample_characters["questioner_id"]

        # Add an asset first
        asset = char_repo.add_asset(
            character_id, "standing", "/tmp/standing.png", 1024
        )
        session.close()

        response = client.delete(
            f"/api/video/characters/{character_id}/assets/{asset.id}"
        )

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_character_asset_not_found(self, client, sample_characters):
        """Test deleting non-existent asset."""
        character_id = sample_characters["questioner_id"]

        response = client.delete(
            f"/api/video/characters/{character_id}/assets/9999"
        )

        assert response.status_code == 404


class TestBackgroundEndpoints:
    """Test background asset endpoints."""

    @patch("contentmanager.dashboard.routers.video_projects.asset_manager")
    def test_upload_background(self, mock_asset_manager, client):
        """Test POST /backgrounds endpoint."""
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/tmp/background.jpg")
        mock_asset_manager.save_background_asset = AsyncMock(return_value=mock_path)

        file_data = BytesIO(b"background image")
        files = {"file": ("office.jpg", file_data, "image/jpeg")}

        response = client.post(
            "/api/video/backgrounds",
            params={"name": "Office Background", "context_style": "tech"},
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Office Background"

    def test_list_backgrounds_empty(self, client):
        """Test GET /backgrounds with no backgrounds."""
        response = client.get("/api/video/backgrounds")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_backgrounds(self, client, db_session_factory):
        """Test GET /backgrounds returns backgrounds."""
        session = db_session_factory()
        asset_repo = AssetRepository(session)
        asset_repo.create_background("BG1", "/tmp/bg1.jpg", ContextStyle.TECH.value)
        asset_repo.create_background("BG2", "/tmp/bg2.jpg", ContextStyle.FINANCE.value)
        session.close()

        response = client.get("/api/video/backgrounds")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_backgrounds_filter_by_style(self, client, db_session_factory):
        """Test filtering backgrounds by context_style."""
        session = db_session_factory()
        asset_repo = AssetRepository(session)
        asset_repo.create_background("Tech BG", "/tmp/tech.jpg", ContextStyle.TECH.value)
        asset_repo.create_background("Finance BG", "/tmp/fin.jpg", ContextStyle.FINANCE.value)
        session.close()

        response = client.get(
            "/api/video/backgrounds",
            params={"context_style": "tech"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Tech BG"

    @patch("contentmanager.dashboard.routers.video_projects.asset_manager")
    def test_delete_background(self, mock_asset_manager, client, db_session_factory):
        """Test DELETE /backgrounds/{id} endpoint."""
        mock_asset_manager.delete_asset = AsyncMock(return_value=True)

        session = db_session_factory()
        asset_repo = AssetRepository(session)
        bg = asset_repo.create_background("Test BG", "/tmp/bg.jpg")
        session.close()

        response = client.delete(f"/api/video/backgrounds/{bg.id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_background_not_found(self, client):
        """Test deleting non-existent background."""
        response = client.delete("/api/video/backgrounds/9999")

        assert response.status_code == 404


class TestMusicEndpoints:
    """Test music asset endpoints."""

    @patch("contentmanager.dashboard.routers.video_projects.asset_manager")
    @patch("contentmanager.dashboard.routers.video_projects.get_audio_duration")
    def test_upload_music(self, mock_get_duration, mock_asset_manager, client):
        """Test POST /music endpoint."""
        mock_path = Mock()
        mock_path.__str__ = Mock(return_value="/tmp/music.mp3")
        mock_asset_manager.save_music_asset = AsyncMock(return_value=mock_path)
        mock_get_duration.return_value = 120.5

        file_data = BytesIO(b"music data")
        files = {"file": ("track.mp3", file_data, "audio/mpeg")}

        response = client.post(
            "/api/video/music",
            params={"name": "Upbeat Track", "context_style": "motivation"},
            files=files,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Upbeat Track"
        assert data["duration_seconds"] == 120.5

    def test_list_music(self, client, db_session_factory):
        """Test GET /music endpoint."""
        session = db_session_factory()
        asset_repo = AssetRepository(session)
        asset_repo.create_music("Track1", "/tmp/t1.mp3", 60.0)
        asset_repo.create_music("Track2", "/tmp/t2.mp3", 90.0)
        session.close()

        response = client.get("/api/video/music")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @patch("contentmanager.dashboard.routers.video_projects.asset_manager")
    def test_delete_music(self, mock_asset_manager, client, db_session_factory):
        """Test DELETE /music/{id} endpoint."""
        mock_asset_manager.delete_asset = AsyncMock(return_value=True)

        session = db_session_factory()
        asset_repo = AssetRepository(session)
        music = asset_repo.create_music("Test", "/tmp/music.mp3", 45.0)
        session.close()

        response = client.delete(f"/api/video/music/{music.id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"


class TestVideoProjectEndpoints:
    """Test video project CRUD endpoints."""

    @patch("contentmanager.dashboard.routers.video_projects.get_script_generator")
    def test_create_project(self, mock_get_generator, client, sample_characters):
        """Test POST /projects endpoint."""
        # Mock the script generator to avoid API calls
        mock_generator = Mock()
        mock_get_generator.return_value = mock_generator

        project_data = {
            "title": "My First Video",
            "topic": "Introduction to Python",
            "context_style": "tech",
            "questioner_id": sample_characters["questioner_id"],
            "explainer_id": sample_characters["explainer_id"],
        }

        response = client.post(
            "/api/video/projects",
            json=project_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "My First Video"
        assert data["topic"] == "Introduction to Python"
        assert data["status"] == "draft"

    def test_create_project_invalid_character(self, client, sample_characters):
        """Test creating project with non-existent character."""
        project_data = {
            "title": "Test",
            "topic": "Test",
            "context_style": "tech",
            "questioner_id": 9999,  # Non-existent
            "explainer_id": sample_characters["explainer_id"],
        }

        response = client.post("/api/video/projects", json=project_data)

        assert response.status_code == 400
        assert "Questioner character not found" in response.json()["detail"]

    def test_list_projects_empty(self, client):
        """Test GET /projects with no projects."""
        response = client.get("/api/video/projects")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_projects(self, client, db_session_factory, sample_characters):
        """Test GET /projects returns projects."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        repo.create(
            "Project 1", "Topic 1", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        repo.create(
            "Project 2", "Topic 2", ContextStyle.FINANCE.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.get("/api/video/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_projects_filter_by_status(self, client, db_session_factory, sample_characters):
        """Test filtering projects by status."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        p1 = repo.create(
            "Draft", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        p2 = repo.create(
            "Approved", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        repo.update_status(p2.id, VideoProjectStatus.APPROVED)
        session.close()

        response = client.get(
            "/api/video/projects",
            params={"status": "approved"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == p2.id

    def test_get_project(self, client, db_session_factory, sample_characters):
        """Test GET /projects/{id} endpoint."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test Project", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.get(f"/api/video/projects/{project.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project.id
        assert data["title"] == "Test Project"

    def test_get_project_not_found(self, client):
        """Test getting non-existent project."""
        response = client.get("/api/video/projects/9999")

        assert response.status_code == 404

    def test_update_project_script(self, client, db_session_factory, sample_characters):
        """Test PATCH /projects/{id} endpoint."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        project_id = project.id
        session.close()

        # The endpoint expects script_json and takeaway as query params
        # but script_json is a dict which can't be passed as a simple query param
        # So we need to check how the API actually expects the data
        response = client.patch(
            f"/api/video/projects/{project_id}",
            json={
                "script_json": {"lines": [{"text": "Hello"}]},
                "takeaway": "Great lesson!",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["takeaway"] == "Great lesson!"

    def test_delete_project(self, client, db_session_factory, sample_characters):
        """Test DELETE /projects/{id} endpoint."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.delete(f"/api/video/projects/{project.id}")

        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_delete_project_not_found(self, client):
        """Test deleting non-existent project."""
        response = client.delete("/api/video/projects/9999")

        assert response.status_code == 404


class TestWorkflowActionEndpoints:
    """Test workflow action endpoints (approve, reject, regenerate)."""

    @patch("contentmanager.dashboard.routers.video_projects.get_voiceover_service")
    def test_approve_project(self, mock_get_service, client, db_session_factory, sample_characters):
        """Test POST /projects/{id}/approve endpoint."""
        # Mock voiceover service to avoid API calls
        mock_service = Mock()
        mock_get_service.return_value = mock_service

        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.post(
            f"/api/video/projects/{project.id}/approve",
            params={"reviewed_by": "admin"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"

    def test_approve_project_not_in_draft(self, client, db_session_factory, sample_characters):
        """Test approving non-draft project fails."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        repo.update_status(project.id, VideoProjectStatus.COMPLETED)
        session.close()

        response = client.post(f"/api/video/projects/{project.id}/approve")

        assert response.status_code == 400
        assert "not in DRAFT status" in response.json()["detail"]

    def test_reject_project(self, client, db_session_factory, sample_characters):
        """Test POST /projects/{id}/reject endpoint."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.post(
            f"/api/video/projects/{project.id}/reject",
            json={"notes": "Script needs improvement"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draft"
        assert "Script needs improvement" in data["error_message"]

    @patch("contentmanager.dashboard.routers.video_projects.get_script_generator")
    def test_regenerate_script(self, mock_get_generator, client, db_session_factory, sample_characters):
        """Test POST /projects/{id}/regenerate endpoint."""
        mock_generator = Mock()
        mock_get_generator.return_value = mock_generator

        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.post(f"/api/video/projects/{project.id}/regenerate")

        assert response.status_code == 200

    @patch("contentmanager.dashboard.routers.video_projects.ffmpeg_renderer")
    def test_render_project(self, mock_renderer, client, db_session_factory, sample_characters):
        """Test POST /projects/{id}/render endpoint."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )

        # Set status to AUDIO_READY
        repo.update_status(project.id, VideoProjectStatus.AUDIO_READY)
        session.close()

        response = client.post(f"/api/video/projects/{project.id}/render")

        assert response.status_code == 200

    def test_render_project_wrong_status(self, client, db_session_factory, sample_characters):
        """Test rendering project not in AUDIO_READY status."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.post(f"/api/video/projects/{project.id}/render")

        assert response.status_code == 400
        assert "AUDIO_READY status" in response.json()["detail"]


class TestDownloadEndpoints:
    """Test download and preview endpoints."""

    def test_download_video_not_ready(self, client, db_session_factory, sample_characters):
        """Test downloading video that hasn't been rendered."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.get(f"/api/video/projects/{project.id}/download")

        assert response.status_code == 404
        assert "not yet rendered" in response.json()["detail"]

    def test_preview_audio_not_ready(self, client, db_session_factory, sample_characters):
        """Test previewing audio that hasn't been generated."""
        session = db_session_factory()
        repo = VideoProjectRepository(session)

        project = repo.create(
            "Test", "Topic", ContextStyle.TECH.value,
            sample_characters["questioner_id"],
            sample_characters["explainer_id"],
        )
        session.close()

        response = client.get(f"/api/video/projects/{project.id}/preview-audio")

        assert response.status_code == 404
        assert "not yet generated" in response.json()["detail"]


class TestSettingsEndpoints:
    """Test settings-related endpoints."""

    @patch("contentmanager.dashboard.routers.video_projects.get_voiceover_service")
    def test_list_voices_success(self, mock_get_service, client):
        """Test GET /voices endpoint."""
        mock_service = Mock()
        mock_service.list_voices = AsyncMock(return_value=[
            {"voice_id": "123", "name": "Voice 1"},
            {"voice_id": "456", "name": "Voice 2"},
        ])
        mock_get_service.return_value = mock_service

        response = client.get("/api/video/voices")

        assert response.status_code == 200
        data = response.json()
        assert len(data["voices"]) == 2

    def test_update_settings(self, client):
        """Test POST /settings endpoint."""
        response = client.post(
            "/api/video/settings",
            params={
                "default_questioner_voice": "voice_123",
                "default_explainer_voice": "voice_456",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
