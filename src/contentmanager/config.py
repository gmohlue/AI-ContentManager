"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = "sqlite:///./data/contentmanager.db"

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class ClaudeSettings(BaseSettings):
    """Claude API configuration."""

    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"

    model_config = SettingsConfigDict(
        env_prefix="CLAUDE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class VideoSettings(BaseSettings):
    """Video pipeline configuration."""

    # Eleven Labs
    elevenlabs_api_key: str = ""
    elevenlabs_questioner_voice: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_explainer_voice: str = "EXAVITQu4vr4xnSDxMaL"

    # Directories
    assets_dir: Path = Path("data/assets")
    projects_dir: Path = Path("data/projects")

    # Video output settings
    width: int = 1080
    height: int = 1920
    fps: int = 30

    # FFmpeg
    ffmpeg_path: str = "ffmpeg"
    ffprobe_path: str = "ffprobe"

    model_config = SettingsConfigDict(
        env_prefix="VIDEO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = "AI Content Manager"
    debug: bool = False

    database: DatabaseSettings = DatabaseSettings()
    claude: ClaudeSettings = ClaudeSettings()
    video: VideoSettings = VideoSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
