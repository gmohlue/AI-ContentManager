"""LLM prompt templates for script generation."""

DIALOGUE_SCRIPT_PROMPT = """You are a scriptwriter for short educational videos. Create an engaging dialogue between two characters discussing the given topic.

CHARACTERS:
- {questioner_name} (Questioner): Asks thoughtful questions, expresses curiosity
- {explainer_name} (Explainer): Provides clear, concise explanations

TOPIC: {topic}
STYLE: {context_style}
TARGET DURATION: {target_duration} seconds (approximately {line_count} exchanges)

{document_context}

REQUIREMENTS:
1. Start with {questioner_name} asking an engaging opening question
2. Alternate between questioner and explainer
3. Keep each line under 20 words for readability
4. Use conversational, accessible language
5. End with a memorable takeaway or call-to-action
6. Include pose suggestions for visual variety (standing, thinking, pointing, excited)

OUTPUT FORMAT (JSON):
{{
    "lines": [
        {{
            "speaker_role": "questioner",
            "speaker_name": "{questioner_name}",
            "line": "The dialogue line here",
            "pose": "thinking"
        }},
        {{
            "speaker_role": "explainer",
            "speaker_name": "{explainer_name}",
            "line": "The response here",
            "pose": "pointing"
        }}
    ],
    "takeaway": "A brief memorable takeaway message"
}}

Generate the dialogue script now:"""


TOPIC_EXTRACTION_PROMPT = """Analyze the following document and extract topics suitable for short educational videos.

DOCUMENT:
{document_content}

Extract up to {max_topics} distinct topics that would work well as 30-60 second explainer videos.

For each topic, provide:
1. A clear, specific title
2. A brief description of what the video would cover
3. Suggested context style (motivation, finance, tech, educational)

OUTPUT FORMAT (JSON):
{{
    "topics": [
        {{
            "title": "Topic title",
            "description": "What the video would explain",
            "context_style": "educational"
        }}
    ]
}}

Extract the topics now:"""
