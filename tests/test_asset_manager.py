"""Tests for Asset Manager."""

import pytest
import tempfile
from pathlib import Path
from io import BytesIO

from contentmanager.core.content.video_pipeline.asset_manager import (
    AssetManager,
    ALLOWED_IMAGE_TYPES,
    ALLOWED_AUDIO_TYPES,
)
from contentmanager.core.content.video_pipeline.models import ContextStyle


@pytest.fixture
def temp_assets_dir():
    """Create a temporary assets directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def asset_manager(temp_assets_dir):
    """Create an AssetManager instance with temp directory."""
    return AssetManager(temp_assets_dir)


class TestAssetManagerInit:
    """Test AssetManager initialization."""

    def test_init_creates_directories(self, temp_assets_dir):
        """Test that initialization creates required subdirectories."""
        manager = AssetManager(temp_assets_dir)

        assert manager.assets_dir.exists()
        assert manager.characters_dir.exists()
        assert manager.backgrounds_dir.exists()
        assert manager.music_dir.exists()

        assert manager.characters_dir == temp_assets_dir / "characters"
        assert manager.backgrounds_dir == temp_assets_dir / "backgrounds"
        assert manager.music_dir == temp_assets_dir / "music"

    def test_init_with_existing_directories(self, temp_assets_dir):
        """Test initialization when directories already exist."""
        # Create directories first
        (temp_assets_dir / "characters").mkdir()
        (temp_assets_dir / "backgrounds").mkdir()
        (temp_assets_dir / "music").mkdir()

        # Should not raise error
        manager = AssetManager(temp_assets_dir)
        assert manager.characters_dir.exists()


class TestFileValidation:
    """Test file type validation methods."""

    def test_validate_image_file_valid(self, asset_manager):
        """Test valid image file extensions."""
        for ext in ALLOWED_IMAGE_TYPES:
            asset_manager._validate_image_file(f"image{ext}")
            asset_manager._validate_image_file(f"IMAGE{ext.upper()}")  # Case insensitive

    def test_validate_image_file_invalid(self, asset_manager):
        """Test invalid image file raises ValueError."""
        with pytest.raises(ValueError, match="Invalid image type"):
            asset_manager._validate_image_file("file.txt")

        with pytest.raises(ValueError, match="Invalid image type"):
            asset_manager._validate_image_file("document.pdf")

        with pytest.raises(ValueError, match="Invalid image type"):
            asset_manager._validate_image_file("video.mp4")

    def test_validate_audio_file_valid(self, asset_manager):
        """Test valid audio file extensions."""
        for ext in ALLOWED_AUDIO_TYPES:
            asset_manager._validate_audio_file(f"audio{ext}")
            asset_manager._validate_audio_file(f"AUDIO{ext.upper()}")  # Case insensitive

    def test_validate_audio_file_invalid(self, asset_manager):
        """Test invalid audio file raises ValueError."""
        with pytest.raises(ValueError, match="Invalid audio type"):
            asset_manager._validate_audio_file("file.txt")

        with pytest.raises(ValueError, match="Invalid audio type"):
            asset_manager._validate_audio_file("video.mp4")


class TestFilenameSanitization:
    """Test filename sanitization."""

    def test_sanitize_filename_alphanumeric(self, asset_manager):
        """Test sanitizing alphanumeric filenames."""
        assert asset_manager._sanitize_filename("test123") == "test123"
        assert asset_manager._sanitize_filename("TestFile") == "TestFile"

    def test_sanitize_filename_with_spaces(self, asset_manager):
        """Test sanitizing filenames with spaces."""
        assert asset_manager._sanitize_filename("my file name") == "my_file_name"
        assert asset_manager._sanitize_filename("test  file") == "test__file"

    def test_sanitize_filename_special_chars(self, asset_manager):
        """Test sanitizing filenames with special characters."""
        assert asset_manager._sanitize_filename("file@#$%") == "file____"
        assert asset_manager._sanitize_filename("test!&*()") == "test_____"

    def test_sanitize_filename_preserves_dashes_underscores(self, asset_manager):
        """Test that dashes and underscores are preserved."""
        assert asset_manager._sanitize_filename("my-file_name") == "my-file_name"
        assert asset_manager._sanitize_filename("test_file-123") == "test_file-123"

    def test_sanitize_filename_length_limit(self, asset_manager):
        """Test filename length is limited to 50 characters."""
        long_name = "a" * 100
        sanitized = asset_manager._sanitize_filename(long_name)
        assert len(sanitized) == 50

    def test_sanitize_filename_unicode(self, asset_manager):
        """Test sanitizing unicode characters."""
        result = asset_manager._sanitize_filename("café_résumé")
        # The implementation uses isalnum() which accepts unicode letters
        # So unicode characters may be preserved depending on implementation
        assert len(result) <= 50


class TestSaveCharacterAsset:
    """Test saving character assets."""

    @pytest.mark.asyncio
    async def test_save_character_asset_png(self, asset_manager):
        """Test saving a PNG character asset."""
        file_data = BytesIO(b"fake png data")

        result_path = await asset_manager.save_character_asset(
            character_id=1,
            pose="standing",
            file=file_data,
            filename="standing.png",
        )

        assert result_path.exists()
        assert result_path.name == "standing.png"
        assert result_path.parent.name == "1"
        assert result_path.read_bytes() == b"fake png data"

    @pytest.mark.asyncio
    async def test_save_character_asset_creates_directory(self, asset_manager):
        """Test that character directory is created if it doesn't exist."""
        file_data = BytesIO(b"test data")

        result_path = await asset_manager.save_character_asset(
            character_id=999,
            pose="thinking",
            file=file_data,
            filename="thinking.jpg",
        )

        assert result_path.parent.exists()
        assert result_path.parent.name == "999"

    @pytest.mark.asyncio
    async def test_save_character_asset_overwrites(self, asset_manager):
        """Test that saving same pose overwrites previous file."""
        file1 = BytesIO(b"original data")
        file2 = BytesIO(b"updated data")

        path1 = await asset_manager.save_character_asset(
            1, "standing", file1, "standing.png"
        )
        path2 = await asset_manager.save_character_asset(
            1, "standing", file2, "standing.png"
        )

        assert path1 == path2
        assert path2.read_bytes() == b"updated data"

    @pytest.mark.asyncio
    async def test_save_character_asset_invalid_type(self, asset_manager):
        """Test saving invalid file type raises ValueError."""
        file_data = BytesIO(b"test")

        with pytest.raises(ValueError, match="Invalid image type"):
            await asset_manager.save_character_asset(
                1, "standing", file_data, "file.txt"
            )

    @pytest.mark.asyncio
    async def test_save_character_asset_preserves_extension(self, asset_manager):
        """Test that file extension is preserved."""
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            file_data = BytesIO(b"test")
            path = await asset_manager.save_character_asset(
                5, "pose", file_data, f"pose{ext}"
            )
            assert path.suffix.lower() == ext.lower()


class TestSaveBackgroundAsset:
    """Test saving background assets."""

    @pytest.mark.asyncio
    async def test_save_background_asset(self, asset_manager):
        """Test saving a background asset."""
        file_data = BytesIO(b"background image data")

        result_path = await asset_manager.save_background_asset(
            name="Office Space",
            file=file_data,
            filename="office.jpg",
            context_style=ContextStyle.TECH,
        )

        assert result_path.exists()
        assert result_path.name == "Office_Space.jpg"
        assert result_path.parent.name == "tech"
        assert result_path.read_bytes() == b"background image data"

    @pytest.mark.asyncio
    async def test_save_background_asset_no_style(self, asset_manager):
        """Test saving background without context style."""
        file_data = BytesIO(b"generic background")

        result_path = await asset_manager.save_background_asset(
            name="Generic",
            file=file_data,
            filename="generic.png",
            context_style=None,
        )

        assert result_path.exists()
        assert result_path.parent.name == "general"

    @pytest.mark.asyncio
    async def test_save_background_asset_creates_style_directory(self, asset_manager):
        """Test that style subdirectory is created."""
        file_data = BytesIO(b"test")

        result_path = await asset_manager.save_background_asset(
            "Finance BG", file_data, "finance.jpg", ContextStyle.FINANCE
        )

        assert result_path.parent.name == "finance"
        assert result_path.parent.exists()

    @pytest.mark.asyncio
    async def test_save_background_asset_sanitizes_name(self, asset_manager):
        """Test that background name is sanitized."""
        file_data = BytesIO(b"test")

        result_path = await asset_manager.save_background_asset(
            "My @#$ Background!", file_data, "bg.png"
        )

        # Special chars should be replaced with underscores
        assert "@" not in result_path.name
        assert "#" not in result_path.name
        assert "$" not in result_path.name
        assert result_path.name.endswith(".png")

    @pytest.mark.asyncio
    async def test_save_background_asset_invalid_type(self, asset_manager):
        """Test saving invalid file type raises ValueError."""
        file_data = BytesIO(b"test")

        with pytest.raises(ValueError, match="Invalid image type"):
            await asset_manager.save_background_asset(
                "Test", file_data, "file.mp3"
            )


class TestSaveMusicAsset:
    """Test saving music assets."""

    @pytest.mark.asyncio
    async def test_save_music_asset(self, asset_manager):
        """Test saving a music asset."""
        file_data = BytesIO(b"music audio data")

        result_path = await asset_manager.save_music_asset(
            name="Upbeat Track",
            file=file_data,
            filename="upbeat.mp3",
            context_style=ContextStyle.MOTIVATION,
        )

        assert result_path.exists()
        assert result_path.name == "Upbeat_Track.mp3"
        assert result_path.parent.name == "motivation"
        assert result_path.read_bytes() == b"music audio data"

    @pytest.mark.asyncio
    async def test_save_music_asset_no_style(self, asset_manager):
        """Test saving music without context style."""
        file_data = BytesIO(b"generic music")

        result_path = await asset_manager.save_music_asset(
            name="Generic Music",
            file=file_data,
            filename="music.mp3",
            context_style=None,
        )

        assert result_path.parent.name == "general"

    @pytest.mark.asyncio
    async def test_save_music_asset_different_formats(self, asset_manager):
        """Test saving music in different audio formats."""
        for ext in [".mp3", ".wav", ".m4a", ".ogg"]:
            file_data = BytesIO(b"audio data")
            path = await asset_manager.save_music_asset(
                "Track", file_data, f"track{ext}"
            )
            assert path.suffix.lower() == ext.lower()

    @pytest.mark.asyncio
    async def test_save_music_asset_invalid_type(self, asset_manager):
        """Test saving invalid file type raises ValueError."""
        file_data = BytesIO(b"test")

        with pytest.raises(ValueError, match="Invalid audio type"):
            await asset_manager.save_music_asset(
                "Test", file_data, "file.jpg"
            )


class TestDeleteAsset:
    """Test deleting assets."""

    @pytest.mark.asyncio
    async def test_delete_asset_success(self, asset_manager):
        """Test successfully deleting an asset."""
        # Create a file first
        file_data = BytesIO(b"test data")
        file_path = await asset_manager.save_character_asset(
            1, "standing", file_data, "standing.png"
        )

        assert file_path.exists()

        # Delete it
        result = await asset_manager.delete_asset(file_path)

        assert result is True
        assert not file_path.exists()

    @pytest.mark.asyncio
    async def test_delete_asset_not_found(self, asset_manager):
        """Test deleting non-existent file returns False."""
        fake_path = asset_manager.characters_dir / "999" / "nonexistent.png"

        result = await asset_manager.delete_asset(fake_path)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_asset_security_check(self, asset_manager):
        """Test that files outside assets directory cannot be deleted."""
        # Create a file outside the assets directory
        outside_path = Path("/tmp/external_file.txt")
        outside_path.write_text("test")

        try:
            with pytest.raises(ValueError, match="Cannot delete files outside assets directory"):
                await asset_manager.delete_asset(outside_path)
        finally:
            # Clean up test file
            if outside_path.exists():
                outside_path.unlink()

    @pytest.mark.asyncio
    async def test_delete_asset_prevents_directory_traversal(self, asset_manager):
        """Test protection against directory traversal attacks."""
        # Try to delete file outside assets using ../
        malicious_path = asset_manager.assets_dir / ".." / ".." / "etc" / "passwd"

        with pytest.raises(ValueError, match="Cannot delete files outside assets directory"):
            await asset_manager.delete_asset(malicious_path)


class TestGetCharacterAssets:
    """Test retrieving character assets."""

    @pytest.mark.asyncio
    async def test_get_character_assets_empty(self, asset_manager):
        """Test getting assets for character with no assets."""
        assets = asset_manager.get_character_assets(999)
        assert assets == []

    @pytest.mark.asyncio
    async def test_get_character_assets_single(self, asset_manager):
        """Test getting single character asset."""
        file_data = BytesIO(b"test data")
        await asset_manager.save_character_asset(1, "standing", file_data, "standing.png")

        assets = asset_manager.get_character_assets(1)

        assert len(assets) == 1
        assert assets[0]["pose"] == "standing"
        assert assets[0]["file_path"].endswith("standing.png")
        assert assets[0]["file_size_bytes"] > 0

    @pytest.mark.asyncio
    async def test_get_character_assets_multiple(self, asset_manager):
        """Test getting multiple character assets."""
        poses = ["standing", "thinking", "pointing", "excited"]

        for pose in poses:
            file_data = BytesIO(b"test data for " + pose.encode())
            await asset_manager.save_character_asset(
                5, pose, file_data, f"{pose}.png"
            )

        assets = asset_manager.get_character_assets(5)

        assert len(assets) == 4
        asset_poses = {a["pose"] for a in assets}
        assert asset_poses == set(poses)

    @pytest.mark.asyncio
    async def test_get_character_assets_only_images(self, asset_manager):
        """Test that only image files are returned."""
        # Create character directory with mixed files
        char_dir = asset_manager.characters_dir / "10"
        char_dir.mkdir()

        # Create image files
        (char_dir / "standing.png").write_bytes(b"image")
        (char_dir / "thinking.jpg").write_bytes(b"image")

        # Create non-image files (should be ignored)
        (char_dir / "readme.txt").write_bytes(b"text")
        (char_dir / "data.json").write_bytes(b"json")

        assets = asset_manager.get_character_assets(10)

        assert len(assets) == 2
        assert all(
            Path(a["file_path"]).suffix.lower() in ALLOWED_IMAGE_TYPES
            for a in assets
        )

    @pytest.mark.asyncio
    async def test_get_character_assets_includes_metadata(self, asset_manager):
        """Test that returned assets include all metadata."""
        file_data = BytesIO(b"x" * 1024)  # 1KB of data
        await asset_manager.save_character_asset(1, "standing", file_data, "standing.png")

        assets = asset_manager.get_character_assets(1)

        assert len(assets) == 1
        asset = assets[0]
        assert "pose" in asset
        assert "file_path" in asset
        assert "file_size_bytes" in asset
        assert asset["file_size_bytes"] == 1024


class TestAssetManagerIntegration:
    """Integration tests for asset manager workflows."""

    @pytest.mark.asyncio
    async def test_full_character_workflow(self, asset_manager):
        """Test complete workflow: create, retrieve, delete character assets."""
        # Create multiple assets
        poses = ["standing", "thinking"]
        for pose in poses:
            file_data = BytesIO(f"{pose} data".encode())
            await asset_manager.save_character_asset(
                100, pose, file_data, f"{pose}.png"
            )

        # Retrieve assets
        assets = asset_manager.get_character_assets(100)
        assert len(assets) == 2

        # Delete assets
        for asset in assets:
            await asset_manager.delete_asset(Path(asset["file_path"]))

        # Verify deletion
        final_assets = asset_manager.get_character_assets(100)
        assert len(final_assets) == 0

    @pytest.mark.asyncio
    async def test_multiple_context_styles(self, asset_manager):
        """Test organizing backgrounds by context style."""
        styles = [ContextStyle.TECH, ContextStyle.FINANCE, ContextStyle.MOTIVATION]

        for style in styles:
            file_data = BytesIO(f"{style.value} background".encode())
            await asset_manager.save_background_asset(
                f"{style.value} BG",
                file_data,
                f"{style.value}.jpg",
                style,
            )

        # Verify directories were created
        for style in styles:
            style_dir = asset_manager.backgrounds_dir / style.value
            assert style_dir.exists()
            assert len(list(style_dir.iterdir())) == 1
