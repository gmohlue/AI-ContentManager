# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-ContentManager (Educational Video Bot) is an automated video production system that transforms documents into educational animated videos featuring customizable characters. The project uses a phased implementation approach:

- **MVP (Phase 1):** Working pipeline with synchronous processing, single tenant, TikTok format
- **Phase 2:** Background workers (Redis/RQ), batch processing, multi-format output
- **Phase 3:** Multi-tenant support, brand templates, cost tracking
- **Phase 4:** Remotion renderer for complex animations, analytics

## Architecture

The codebase follows this structure (see `VIDEO_PIPELINE_IMPLEMENTATION_PLAN.md` for full details):

```
src/contentmanager/
├── core/content/video_pipeline/   # Video pipeline modules
│   ├── script_generator.py        # Claude LLM dialogue generation
│   ├── voiceover_service.py       # Eleven Labs TTS integration
│   ├── ffmpeg_renderer.py         # FFmpeg video composition
│   ├── asset_manager.py           # Character/background/music assets
│   └── pipeline.py                # Orchestrator
├── database/
│   ├── models.py                  # SQLAlchemy models
│   └── repositories/              # Data access layer
├── dashboard/
│   ├── routers/                   # FastAPI endpoints
│   └── templates/                 # Jinja2 UI templates
└── workers/                       # [Phase 2+] Background job workers
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

Required environment variables (add to `.env`):
```
ELEVENLABS_API_KEY=
ELEVENLABS_QUESTIONER_VOICE=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_EXPLAINER_VOICE=EXAVITQu4vr4xnSDxMaL
VIDEO_ASSETS_DIR=data/assets
VIDEO_PROJECTS_DIR=data/projects
```

## Implementation Notes

- All tables include `tenant_id` (nullable) for multi-tenant readiness
- Default video format: 1080x1920 (9:16 portrait for TikTok)
- FFmpeg is used for MVP; Remotion reserved for complex animations in Phase 4
- Cost tracking implemented via `UsageMetrics` table (Phase 3)
