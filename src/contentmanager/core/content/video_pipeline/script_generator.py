"""Script generation using Claude LLM."""

import json
import logging
from anthropic import Anthropic

from .models import (
    ContextStyle,
    DialogueLine,
    DialogueScript,
    CharacterRole,
)
from .prompts import DIALOGUE_SCRIPT_PROMPT, TOPIC_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)


class DialogueScriptGenerator:
    """Generates dialogue scripts for educational videos using Claude."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def generate(
        self,
        topic: str,
        context_style: ContextStyle,
        document_context: str | None = None,
        questioner_name: str = "Thabo",
        explainer_name: str = "Lerato",
        target_duration: int = 45,
    ) -> DialogueScript:
        """Generate a dialogue script for the given topic.

        Args:
            topic: The subject matter for the video
            context_style: The style/theme of the content
            document_context: Optional source document content
            questioner_name: Name of the questioning character
            explainer_name: Name of the explaining character
            target_duration: Target video duration in seconds

        Returns:
            DialogueScript with generated dialogue lines
        """
        # Estimate line count (roughly 3 seconds per exchange)
        line_count = target_duration // 3

        context_section = ""
        if document_context:
            context_section = f"\nSOURCE DOCUMENT:\n{document_context[:2000]}\n"

        prompt = DIALOGUE_SCRIPT_PROMPT.format(
            questioner_name=questioner_name,
            explainer_name=explainer_name,
            topic=topic,
            context_style=context_style.value,
            target_duration=target_duration,
            line_count=line_count,
            document_context=context_section,
        )

        logger.info(f"Generating script for topic: {topic}")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        script_data = self._parse_response(response_text)

        lines = []
        for i, line_data in enumerate(script_data.get("lines", [])):
            lines.append(
                DialogueLine(
                    speaker_role=CharacterRole(line_data["speaker_role"]),
                    speaker_name=line_data["speaker_name"],
                    line=line_data["line"],
                    pose=line_data.get("pose", "standing"),
                    scene_number=i + 1,
                )
            )

        return DialogueScript(
            topic=topic,
            context_style=context_style,
            lines=lines,
            takeaway=script_data.get("takeaway", ""),
            target_duration_seconds=target_duration,
        )

    async def extract_topics_from_document(
        self,
        document_content: str,
        max_topics: int = 10,
    ) -> list[dict]:
        """Extract video-worthy topics from a document.

        Args:
            document_content: The document text to analyze
            max_topics: Maximum number of topics to extract

        Returns:
            List of topic suggestions with title, description, and style
        """
        prompt = TOPIC_EXTRACTION_PROMPT.format(
            document_content=document_content[:5000],
            max_topics=max_topics,
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text
        data = self._parse_response(response_text)

        return data.get("topics", [])

    def _parse_response(self, response_text: str) -> dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        text = response_text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json) and last line (```)
            text = "\n".join(lines[1:-1])

        return json.loads(text)
