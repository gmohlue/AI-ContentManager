# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run the development server
uvicorn contentmanager.main:app --reload

# Or using the entry point
contentmanager

# Run tests
pytest

# Run single test file
pytest tests/test_file.py

# Run with coverage
pytest --cov=src/contentmanager --cov-report=html

# Linting
ruff check src tests
ruff format src tests

# Type checking
mypy src
```

## System Dependencies

```bash
# FFmpeg (required for video rendering)
sudo apt-get install ffmpeg
```

## Project Overview

AI-ContentManager (Educational Video Bot) is an automated video production system that transforms documents into educational animated videos featuring customizable characters. The project uses a phased implementation approach:

- **MVP (Phase 1):** Working pipeline with synchronous processing, single tenant, TikTok format
- **Phase 2:** Background workers (Redis/RQ), batch processing, multi-format output
- **Phase 3:** Multi-tenant support, brand templates, cost tracking
- **Phase 4:** Remotion renderer for complex animations, analytics

## Architecture

```
src/contentmanager/
├── main.py                        # FastAPI application entry point
├── config.py                      # Pydantic settings configuration
├── core/content/video_pipeline/   # Video pipeline modules
│   ├── models.py                  # Pydantic request/response models
│   ├── prompts.py                 # LLM prompt templates
│   ├── script_generator.py        # Claude LLM dialogue generation
│   ├── voiceover_service.py       # Eleven Labs TTS integration
│   ├── ffmpeg_renderer.py         # FFmpeg video composition
│   ├── asset_manager.py           # Character/background/music assets
│   └── pipeline.py                # Pipeline orchestrator
├── database/
│   ├── models.py                  # SQLAlchemy ORM models
│   └── repositories/              # Data access layer (repository pattern)
└── dashboard/
    └── routers/                   # FastAPI endpoint routers
```

## Pipeline Flow

```
Upload Assets → Generate Script (Claude) → Human Review → Generate Voiceover (Eleven Labs) → Render Video (FFmpeg)
```

Human approval happens BEFORE voiceover generation to save costs on rejected scripts.

## Key External Dependencies

- **Claude API:** Script/dialogue generation
- **Eleven Labs API:** Text-to-speech voiceover
- **FFmpeg:** Video rendering and post-processing
- **Redis/RQ:** Background job processing (Phase 2+)
- **Remotion:** Complex animations (Phase 4)

## Database Models

Core entities: `Character`, `CharacterAsset`, `BackgroundAsset`, `MusicAsset`, `VideoProject`, `VideoScene`

VideoProject status flow: `DRAFT → APPROVED → AUDIO_READY → RENDERING → COMPLETED`

## Configuration

Copy `.env.example` to `.env` and configure:
- `CLAUDE_API_KEY` - Anthropic API key for script generation
- `VIDEO_ELEVENLABS_API_KEY` - Eleven Labs API key for voiceover
- `DATABASE_URL` - SQLAlchemy database URL (default: SQLite)

## Implementation Notes

- All tables include `tenant_id` (nullable) for multi-tenant readiness
- Default video format: 1080x1920 (9:16 portrait for TikTok)
- FFmpeg is used for MVP; Remotion reserved for complex animations in Phase 4
- Repository pattern used for data access (`database/repositories/`)
- See `VIDEO_PIPELINE_IMPLEMENTATION_PLAN.md` for full architecture specification
