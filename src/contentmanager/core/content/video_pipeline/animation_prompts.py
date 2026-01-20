"""AI Animation Prompt Generator for stick figure videos.

Generates AI video animation prompts for each scene that can be used with
AI video generators like Runway, Pika, Kling, etc.
"""

import re
from dataclasses import dataclass
from enum import Enum


class AnimationType(Enum):
    """Types of stick figure animations."""
    TALKING = "talking"
    EXPLAINING = "explaining"
    QUESTIONING = "questioning"
    THINKING = "thinking"
    POINTING = "pointing"
    WAVING = "waving"
    REACTING = "reacting"
    CELEBRATING = "celebrating"
    NODDING = "nodding"
    WALKING = "walking"
    IDLE = "idle"


@dataclass
class ScenePrompt:
    """AI animation prompts for a single scene."""
    scene_number: int
    voiceover_line: str
    duration_seconds: float
    speaker_role: str
    animation_type: AnimationType
    prompt_option_1: str
    prompt_option_2: str


# Base style for all prompts
BASE_STYLE = (
    "minimal clean animation, white background, black outline stick figure, "
    "simple line art style, smooth motion, no colors, no shadows, no extra objects"
)


def detect_animation_type(text: str, speaker_role: str) -> AnimationType:
    """Detect the appropriate animation type based on dialogue content."""
    lower_text = text.lower()

    # Check for questions
    if "?" in text:
        if speaker_role == "questioner":
            return AnimationType.QUESTIONING
        return AnimationType.THINKING

    # Check for excitement/celebration
    if "!" in text and any(word in lower_text for word in ["wow", "amazing", "great", "excellent", "perfect"]):
        return AnimationType.CELEBRATING

    # Check for explanations with pointing/showing
    if any(word in lower_text for word in ["look", "see", "this", "here", "that", "example"]):
        return AnimationType.POINTING

    # Check for agreement/acknowledgment
    if any(word in lower_text for word in ["yes", "exactly", "right", "correct", "i see", "got it"]):
        return AnimationType.NODDING

    # Check for greetings
    if any(word in lower_text for word in ["hello", "hi", "hey", "welcome"]):
        return AnimationType.WAVING

    # Check for surprise/reaction
    if any(word in lower_text for word in ["really", "wow", "oh", "interesting"]):
        return AnimationType.REACTING

    # Default based on role
    if speaker_role == "questioner":
        return AnimationType.QUESTIONING
    return AnimationType.EXPLAINING


def generate_animation_prompts(
    animation_type: AnimationType,
    speaker_role: str,
    line: str,
) -> tuple[str, str]:
    """Generate two AI animation prompt options for a scene."""

    # Character description based on role
    if speaker_role == "questioner":
        char_desc = "curious stick figure character"
    else:
        char_desc = "knowledgeable stick figure character"

    prompts = {
        AnimationType.TALKING: (
            f"A {char_desc} talking and gesturing with hands, head nodding slightly, "
            f"mouth moving, expressive body language, {BASE_STYLE}",

            f"Black outline stick figure speaking animatedly, arms moving to emphasize points, "
            f"slight body sway while talking, {BASE_STYLE}"
        ),

        AnimationType.EXPLAINING: (
            f"A {char_desc} explaining with open hand gestures, confident posture, "
            f"one hand raised making a point, {BASE_STYLE}",

            f"Stick figure teacher pose, arms spread explaining concept, "
            f"head tilting while speaking, professional gesture, {BASE_STYLE}"
        ),

        AnimationType.QUESTIONING: (
            f"A {char_desc} asking a question, head tilted curiously, "
            f"hand raised near chin in thinking pose, {BASE_STYLE}",

            f"Stick figure with curious body language, shoulders slightly raised, "
            f"one hand gesturing questioningly, inquisitive pose, {BASE_STYLE}"
        ),

        AnimationType.THINKING: (
            f"A {char_desc} in deep thought, hand on chin, looking slightly upward, "
            f"contemplative pose, {BASE_STYLE}",

            f"Stick figure pondering, finger tapping chin, thoughtful expression, "
            f"subtle head movement while thinking, {BASE_STYLE}"
        ),

        AnimationType.POINTING: (
            f"A {char_desc} pointing forward with one arm extended, "
            f"directing attention, confident stance, {BASE_STYLE}",

            f"Stick figure gesturing to the side, arm stretched pointing at something, "
            f"body leaning slightly in pointing direction, {BASE_STYLE}"
        ),

        AnimationType.WAVING: (
            f"A {char_desc} waving hello with one hand raised, "
            f"friendly greeting gesture, warm body language, {BASE_STYLE}",

            f"Stick figure waving arm back and forth, cheerful welcoming motion, "
            f"slight bounce in movement, {BASE_STYLE}"
        ),

        AnimationType.REACTING: (
            f"A {char_desc} reacting with surprise, arms slightly raised, "
            f"head pulled back in amazement, expressive pose, {BASE_STYLE}",

            f"Stick figure showing surprised reaction, body language expressing interest, "
            f"engaged listening posture, {BASE_STYLE}"
        ),

        AnimationType.CELEBRATING: (
            f"A {char_desc} celebrating with both arms raised high, "
            f"joyful jumping motion, excited body language, {BASE_STYLE}",

            f"Stick figure in victory pose, arms pumping with excitement, "
            f"happy bouncing movement, enthusiastic celebration, {BASE_STYLE}"
        ),

        AnimationType.NODDING: (
            f"A {char_desc} nodding in agreement, head moving up and down, "
            f"understanding expression, attentive posture, {BASE_STYLE}",

            f"Stick figure showing agreement, gentle head nod, "
            f"positive body language, acknowledging gesture, {BASE_STYLE}"
        ),

        AnimationType.WALKING: (
            f"A {char_desc} walking smoothly, legs moving in stride, "
            f"arms swinging naturally, casual walking motion, {BASE_STYLE}",

            f"Stick figure taking steps forward, balanced walking animation, "
            f"natural gait movement, {BASE_STYLE}"
        ),

        AnimationType.IDLE: (
            f"A {char_desc} standing calmly, subtle breathing motion, "
            f"relaxed posture, slight natural movement, {BASE_STYLE}",

            f"Stick figure in neutral standing pose, minimal idle animation, "
            f"gentle weight shift, calm presence, {BASE_STYLE}"
        ),
    }

    return prompts.get(animation_type, prompts[AnimationType.TALKING])


def generate_scene_prompts(
    lines: list[dict],
    scene_durations: list[float] | None = None,
) -> list[ScenePrompt]:
    """Generate AI animation prompts for all scenes in a script.

    Args:
        lines: List of dialogue lines with speaker_role, speaker_name, line
        scene_durations: Optional list of durations for each scene in seconds

    Returns:
        List of ScenePrompt objects with AI animation prompts
    """
    scene_prompts = []

    for i, line_data in enumerate(lines):
        speaker_role = line_data.get("speaker_role", "explainer")
        voiceover_line = line_data.get("line", "")

        # Get duration (default 4 seconds if not provided)
        duration = scene_durations[i] if scene_durations and i < len(scene_durations) else 4.0

        # Detect animation type
        animation_type = detect_animation_type(voiceover_line, speaker_role)

        # Generate two prompt options
        prompt_1, prompt_2 = generate_animation_prompts(
            animation_type=animation_type,
            speaker_role=speaker_role,
            line=voiceover_line,
        )

        scene_prompt = ScenePrompt(
            scene_number=i + 1,
            voiceover_line=voiceover_line,
            duration_seconds=duration,
            speaker_role=speaker_role,
            animation_type=animation_type,
            prompt_option_1=prompt_1,
            prompt_option_2=prompt_2,
        )

        scene_prompts.append(scene_prompt)

    return scene_prompts


def format_prompts_report(scene_prompts: list[ScenePrompt]) -> str:
    """Format scene prompts as a readable report."""
    lines = []
    lines.append("=" * 80)
    lines.append("AI ANIMATION PROMPTS FOR VIDEO SCENES")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total Scenes: {len(scene_prompts)}")
    lines.append(f"Style: Minimal black outline stick figure on white background")
    lines.append("")

    for prompt in scene_prompts:
        lines.append("-" * 80)
        lines.append(f"SCENE {prompt.scene_number}")
        lines.append("-" * 80)
        lines.append(f"Speaker: {prompt.speaker_role.upper()}")
        lines.append(f"Duration: {prompt.duration_seconds:.1f} seconds")
        lines.append(f"Animation Type: {prompt.animation_type.value}")
        lines.append("")
        lines.append("Voiceover Line:")
        lines.append(f'  "{prompt.voiceover_line}"')
        lines.append("")
        lines.append("AI Animation Prompt - Option 1:")
        lines.append(f"  {prompt.prompt_option_1}")
        lines.append("")
        lines.append("AI Animation Prompt - Option 2:")
        lines.append(f"  {prompt.prompt_option_2}")
        lines.append("")

    lines.append("=" * 80)
    lines.append("END OF PROMPTS")
    lines.append("=" * 80)

    return "\n".join(lines)


def save_prompts_to_file(scene_prompts: list[ScenePrompt], output_path: str) -> None:
    """Save prompts report to a text file."""
    report = format_prompts_report(scene_prompts)
    with open(output_path, "w") as f:
        f.write(report)
