"""Application configuration."""

from pathlib import Path
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    url: str = "sqlite:///./data/contentmanager.db"

    class Config:
        env_prefix = "DATABASE_"


class ClaudeSettings(BaseSettings):
    """Claude API configuration."""

    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"

    class Config:
        env_prefix = "CLAUDE_"


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

    class Config:
        env_prefix = "VIDEO_"


class Settings(BaseSettings):
    """Main application settings."""

    app_name: str = "AI Content Manager"
    debug: bool = False

    database: DatabaseSettings = DatabaseSettings()
    claude: ClaudeSettings = ClaudeSettings()
    video: VideoSettings = VideoSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
