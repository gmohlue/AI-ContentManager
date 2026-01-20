"""Video pipeline for generating educational animated videos."""

from .models import (
    DialogueScript,
    DialogueLine,
    VoiceoverResult,
    RenderResult,
)
from .script_generator import DialogueScriptGenerator
from .voiceover_service import VoiceoverService
from .ffmpeg_renderer import FFmpegRenderer
from .asset_manager import AssetManager
from .pipeline import VideoPipeline
from .animation_prompts import (
    generate_scene_prompts,
    format_prompts_report,
    save_prompts_to_file,
    ScenePrompt,
    AnimationType,
)

__all__ = [
    "DialogueScript",
    "DialogueLine",
    "VoiceoverResult",
    "RenderResult",
    "DialogueScriptGenerator",
    "VoiceoverService",
    "FFmpegRenderer",
    "AssetManager",
    "VideoPipeline",
    "generate_scene_prompts",
    "format_prompts_report",
    "save_prompts_to_file",
    "ScenePrompt",
    "AnimationType",
]
