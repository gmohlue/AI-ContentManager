"""Asset management for video pipeline."""

import logging
import shutil
from pathlib import Path
from typing import BinaryIO

from .models import ContextStyle

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_AUDIO_TYPES = {".mp3", ".wav", ".m4a", ".ogg"}
MAX_FILE_SIZE_MB = 50


class AssetManager:
    """Manages character, background, and music assets."""

    def __init__(self, assets_dir: Path):
        self.assets_dir = assets_dir
        self.characters_dir = assets_dir / "characters"
        self.backgrounds_dir = assets_dir / "backgrounds"
        self.music_dir = assets_dir / "music"

        # Ensure directories exist
        for directory in [
            self.characters_dir,
            self.backgrounds_dir,
            self.music_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    async def save_character_asset(
        self,
        character_id: int,
        pose: str,
        file: BinaryIO,
        filename: str,
    ) -> Path:
        """Save a character pose image.

        Args:
            character_id: ID of the character
            pose: Pose name (e.g., "standing", "thinking")
            file: File-like object containing image data
            filename: Original filename

        Returns:
            Path to saved file
        """
        self._validate_image_file(filename)

        char_dir = self.characters_dir / str(character_id)
        char_dir.mkdir(exist_ok=True)

        ext = Path(filename).suffix.lower()
        dest_path = char_dir / f"{pose}{ext}"

        await self._save_file(file, dest_path)
        logger.info(f"Saved character asset: {dest_path}")

        return dest_path

    async def save_background_asset(
        self,
        name: str,
        file: BinaryIO,
        filename: str,
        context_style: ContextStyle | None = None,
    ) -> Path:
        """Save a background image.

        Args:
            name: Display name for the background
            file: File-like object containing image data
            filename: Original filename
            context_style: Optional style category

        Returns:
            Path to saved file
        """
        self._validate_image_file(filename)

        # Create style subdirectory if specified
        if context_style:
            dest_dir = self.backgrounds_dir / context_style.value
        else:
            dest_dir = self.backgrounds_dir / "general"

        dest_dir.mkdir(exist_ok=True)

        ext = Path(filename).suffix.lower()
        safe_name = self._sanitize_filename(name)
        dest_path = dest_dir / f"{safe_name}{ext}"

        await self._save_file(file, dest_path)
        logger.info(f"Saved background asset: {dest_path}")

        return dest_path

    async def save_music_asset(
        self,
        name: str,
        file: BinaryIO,
        filename: str,
        context_style: ContextStyle | None = None,
    ) -> Path:
        """Save a music track.

        Args:
            name: Display name for the track
            file: File-like object containing audio data
            filename: Original filename
            context_style: Optional style category

        Returns:
            Path to saved file
        """
        self._validate_audio_file(filename)

        if context_style:
            dest_dir = self.music_dir / context_style.value
        else:
            dest_dir = self.music_dir / "general"

        dest_dir.mkdir(exist_ok=True)

        ext = Path(filename).suffix.lower()
        safe_name = self._sanitize_filename(name)
        dest_path = dest_dir / f"{safe_name}{ext}"

        await self._save_file(file, dest_path)
        logger.info(f"Saved music asset: {dest_path}")

        return dest_path

    async def delete_asset(self, file_path: Path) -> bool:
        """Delete an asset file.

        Args:
            file_path: Path to the file to delete

        Returns:
            True if deleted, False if not found
        """
        if not file_path.exists():
            return False

        # Ensure file is within assets directory (security check)
        if not str(file_path.resolve()).startswith(str(self.assets_dir.resolve())):
            raise ValueError("Cannot delete files outside assets directory")

        file_path.unlink()
        logger.info(f"Deleted asset: {file_path}")
        return True

    def get_character_assets(self, character_id: int) -> list[dict]:
        """Get all pose assets for a character.

        Args:
            character_id: ID of the character

        Returns:
            List of dicts with pose name and file path
        """
        char_dir = self.characters_dir / str(character_id)
        if not char_dir.exists():
            return []

        assets = []
        for file_path in char_dir.iterdir():
            if file_path.suffix.lower() in ALLOWED_IMAGE_TYPES:
                assets.append(
                    {
                        "pose": file_path.stem,
                        "file_path": str(file_path),
                        "file_size_bytes": file_path.stat().st_size,
                    }
                )

        return assets

    def _validate_image_file(self, filename: str) -> None:
        """Validate image file type."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_IMAGE_TYPES:
            raise ValueError(
                f"Invalid image type: {ext}. Allowed: {ALLOWED_IMAGE_TYPES}"
            )

    def _validate_audio_file(self, filename: str) -> None:
        """Validate audio file type."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_AUDIO_TYPES:
            raise ValueError(
                f"Invalid audio type: {ext}. Allowed: {ALLOWED_AUDIO_TYPES}"
            )

    def _sanitize_filename(self, name: str) -> str:
        """Create a safe filename from display name."""
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return safe[:50]  # Limit length

    async def _save_file(self, file: BinaryIO, dest_path: Path) -> None:
        """Save uploaded file to destination."""
        with open(dest_path, "wb") as dest:
            shutil.copyfileobj(file, dest)
