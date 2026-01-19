# Educational Video Bot - Production Pipeline

## Overview

A fully automated video production system that transforms documents into educational animated videos featuring customizable characters (default: Thabo & Lerato).

**Project Location:** `/home/localadmin/cursor-projects/content-manager`

---

## MVP vs Full Implementation

This document describes both the **MVP (Minimum Viable Product)** and the **Full Production System**. The MVP is designed to get a working video pipeline quickly, while the full system adds scalability, multi-tenancy, and advanced features.

### Implementation Phases

| Phase | Name | Focus | Timeline |
|-------|------|-------|----------|
| **MVP** | First Video | Working pipeline, single tenant, synchronous | Weeks 1-4 |
| **Phase 2** | Scale | Workers, batch processing, multi-format | Weeks 5-7 |
| **Phase 3** | Multi-tenant | Brand templates, client isolation, billing | Weeks 8-10 |
| **Phase 4** | Advanced | Remotion, analytics, trending topics | Future |

### Feature Comparison

| Feature | MVP | Phase 2 | Phase 3 | Phase 4 |
|---------|-----|---------|---------|---------|
| Script generation (Claude) | ✅ | ✅ | ✅ | ✅ |
| Voiceover (Eleven Labs) | ✅ | ✅ | ✅ | ✅ |
| Video rendering (FFmpeg) | ✅ | ✅ | ✅ | ✅ |
| Human review workflow | ✅ | ✅ | ✅ | ✅ |
| User-uploaded assets | ✅ | ✅ | ✅ | ✅ |
| Single output format (TikTok) | ✅ | - | - | - |
| Multi-format output | - | ✅ | ✅ | ✅ |
| Background workers (Redis) | - | ✅ | ✅ | ✅ |
| Batch processing | - | ✅ | ✅ | ✅ |
| Post-processing pipeline | - | ✅ | ✅ | ✅ |
| Brand templates | - | - | ✅ | ✅ |
| Multi-tenant support | - | - | ✅ | ✅ |
| Cost tracking & billing | - | - | ✅ | ✅ |
| Remotion (complex animations) | - | - | - | ✅ |
| Analytics dashboard | - | - | - | ✅ |
| Trending topics | - | - | - | ✅ |

### Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Initial renderer | FFmpeg only | Simpler, no Node.js dependency, sufficient for MVP |
| Processing model | Synchronous for MVP | Low volume (~10/day), no Redis needed initially |
| Asset source | User uploads | Flexibility, no dependency on pre-made assets |
| Approval workflow | Human review before voiceover | Saves Eleven Labs cost on rejected scripts |
| Multi-tenancy | Single tenant, multi-tenant ready | Design with tenant_id but don't implement yet |

---

## User Stories Supported

### User Story 1 – Content Creator (Creative / Visual Focus)
> As a social media content creator, I want to automatically generate short animated explainer videos from text and trending topics, so that I can post daily content without manually editing videos.

| Requirement | MVP | Phase 2+ |
|------------|-----|----------|
| Animated text and transitions | Basic fade | Rich animations |
| Dynamic content from script | ✅ | ✅ |
| Multi-format output | TikTok only | All formats |
| Consistent visual style | Manual | Brand templates |

### User Story 2 – Platform Engineer (Scalability & Performance Focus)
> As a backend/platform engineer, I want to process and transform thousands of video files automatically, so that the system can scale efficiently without high compute costs.

| Requirement | MVP | Phase 2+ |
|------------|-----|----------|
| Trim, merge, resize, compress | - | ✅ |
| Batch processing | - | ✅ |
| No browser dependency | ✅ (FFmpeg) | ✅ |
| CI/CD compatible | - | ✅ (Docker) |

### User Story 3 – Product Owner (Hybrid / Business Focus)
> As a product owner of an automated content platform, I want a system that can generate branded animated videos and then optimize them for delivery, so that we can support multiple clients at scale with minimal manual intervention.

| Requirement | MVP | Phase 3+ |
|------------|-----|----------|
| Brand templates | - | ✅ |
| Post-processing optimization | - | ✅ |
| Scale to 1000s/day | - | ✅ |
| Cost tracking | Logging only | Full tracking |

---

# PART 1: MVP IMPLEMENTATION

## MVP Pipeline Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Upload    │────▶│  Generate   │────▶│   Human     │────▶│  Generate   │────▶│   Render    │
│   Assets    │     │   Script    │     │   Review    │     │  Voiceover  │     │   Video     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │                   │                   │
                      [Claude LLM]        [Edit/Approve]     [Eleven Labs]        [FFmpeg]
                           │                   │                   │                   │
                      Status: DRAFT      Status: APPROVED   Status: AUDIO_READY  Status: COMPLETED
```

**Key insight:** Human approval happens BEFORE voiceover generation. This saves money on rejected scripts.

## MVP Architecture

```
src/contentmanager/
├── core/content/video_pipeline/
│   ├── __init__.py
│   ├── models.py              # Pydantic models
│   ├── script_generator.py    # Claude integration
│   ├── voiceover_service.py   # Eleven Labs
│   ├── asset_manager.py       # Asset upload/selection
│   ├── ffmpeg_renderer.py     # Video rendering
│   ├── prompts.py             # LLM prompts
│   └── pipeline.py            # Orchestrator (simplified)
├── database/
│   ├── models.py              # Add video tables
│   └── repositories/
│       └── video_project.py   # Repository
├── dashboard/
│   ├── routers/
│   │   └── video_projects.py  # API endpoints
│   └── templates/
│       └── video_projects.html # UI
└── data/
    ├── assets/                # User-uploaded assets
    │   ├── characters/        # Character images by pose
    │   ├── backgrounds/
    │   └── music/
    └── projects/              # Generated content
        ├── voiceovers/
        └── videos/
```

## MVP Database Schema

### Enums (MVP)

```python
class VideoProjectStatus(str, Enum):
    DRAFT = "draft"              # Script generated, awaiting review
    APPROVED = "approved"        # Script approved, ready for voiceover
    AUDIO_READY = "audio_ready"  # Voiceover generated, ready to render
    RENDERING = "rendering"      # Video being rendered
    COMPLETED = "completed"      # Done
    FAILED = "failed"

class ContextStyle(str, Enum):
    MOTIVATION = "motivation"
    FINANCE = "finance"
    TECH = "tech"
    EDUCATIONAL = "educational"

class CharacterRole(str, Enum):
    QUESTIONER = "questioner"
    EXPLAINER = "explainer"
```

### Tables (MVP)

**Character** - User-defined characters (any animated figure type)
```python
class Character(Base):
    __tablename__ = "characters"

    id: int (PK)
    name: str                    # "Thabo", "Lerato", custom
    role: CharacterRole          # questioner or explainer

    # Multi-tenant ready (nullable for now, used in Phase 3)
    tenant_id: int (FK, nullable)

    created_at: datetime
    is_active: bool = True
```

**CharacterAsset** - Character pose images uploaded by user
```python
class CharacterAsset(Base):
    __tablename__ = "character_assets"

    id: int (PK)
    character_id: int (FK)
    pose: str                    # "standing", "thinking", "pointing", etc.
    file_path: str
    file_size_bytes: int

    # Multi-tenant ready
    tenant_id: int (FK, nullable)

    created_at: datetime
```

**BackgroundAsset** - Background images
```python
class BackgroundAsset(Base):
    __tablename__ = "background_assets"

    id: int (PK)
    name: str
    context_style: ContextStyle (nullable)
    file_path: str

    # Multi-tenant ready
    tenant_id: int (FK, nullable)

    created_at: datetime
```

**MusicAsset** - Background music tracks
```python
class MusicAsset(Base):
    __tablename__ = "music_assets"

    id: int (PK)
    name: str
    context_style: ContextStyle (nullable)
    file_path: str
    duration_seconds: float

    # Multi-tenant ready
    tenant_id: int (FK, nullable)

    created_at: datetime
```

**VideoProject** - Main video project entity
```python
class VideoProject(Base):
    __tablename__ = "video_projects"

    id: int (PK)

    # Multi-tenant ready
    tenant_id: int (FK, nullable)

    # Content
    title: str
    topic: str
    context_style: ContextStyle
    document_id: int (FK, nullable)

    # Characters
    questioner_id: int (FK)
    explainer_id: int (FK)

    # Script
    script_json: JSON
    takeaway: str (nullable)

    # Audio
    background_music_id: int (FK, nullable)
    voiceover_path: str (nullable)

    # Output
    output_path: str (nullable)
    duration_seconds: float (nullable)

    # Workflow
    status: VideoProjectStatus = "draft"
    error_message: str (nullable)

    # Review tracking
    reviewed_at: datetime (nullable)
    reviewed_by: str (nullable)

    created_at: datetime
    updated_at: datetime
```

**VideoScene** - Individual scene in a video project
```python
class VideoScene(Base):
    __tablename__ = "video_scenes"

    id: int (PK)
    project_id: int (FK)
    scene_number: int

    # Content
    speaker_role: CharacterRole
    line: str
    pose: str

    # Audio (populated after voiceover generation)
    voiceover_path: str (nullable)
    start_time: float (nullable)
    duration_seconds: float (nullable)

    # Visual
    background_id: int (FK, nullable)

    created_at: datetime
```

## MVP Workflow States

```
                                    ┌──────────────┐
                                    │   REJECTED   │
                                    │  (edit/redo) │
                                    └──────┬───────┘
                                           │ edit + save
                                           ▼
┌─────────┐  generate   ┌─────────┐  approve  ┌──────────┐  auto    ┌─────────────┐  render  ┌───────────┐
│  START  │────────────▶│  DRAFT  │──────────▶│ APPROVED │─────────▶│ AUDIO_READY │─────────▶│ RENDERING │
└─────────┘             └─────────┘           └──────────┘          └─────────────┘          └─────┬─────┘
                             │                                                                      │
                             │ regenerate                                                           │
                             ▼                                                                      ▼
                        [Claude LLM]                                                          ┌───────────┐
                                                                                              │ COMPLETED │
                                                                                              └───────────┘
```

## MVP API Endpoints

```python
# Asset Management
POST   /api/video/characters                    # Create character
GET    /api/video/characters                    # List characters
POST   /api/video/characters/{id}/assets        # Upload pose image
GET    /api/video/characters/{id}/assets        # List character poses
DELETE /api/video/characters/{id}/assets/{aid}  # Delete pose

POST   /api/video/backgrounds                   # Upload background
GET    /api/video/backgrounds                   # List backgrounds
DELETE /api/video/backgrounds/{id}

POST   /api/video/music                         # Upload music
GET    /api/video/music                         # List music
DELETE /api/video/music/{id}

# Video Project Workflow
POST   /api/video/projects                      # Create project + generate script
GET    /api/video/projects                      # List projects (with status filter)
GET    /api/video/projects/{id}                 # Get project details
PATCH  /api/video/projects/{id}                 # Edit script (before approval)
DELETE /api/video/projects/{id}

# Workflow Actions
POST   /api/video/projects/{id}/approve         # Approve script → triggers voiceover
POST   /api/video/projects/{id}/reject          # Reject → back to draft with notes
POST   /api/video/projects/{id}/regenerate      # Regenerate script
POST   /api/video/projects/{id}/render          # Trigger render (after audio ready)
GET    /api/video/projects/{id}/download        # Download final video

# Preview
GET    /api/video/projects/{id}/preview-audio   # Stream voiceover for preview

# Settings
GET    /api/video/voices                        # List available Eleven Labs voices
POST   /api/video/settings                      # Set default voices
```

## MVP Files to Create

```
# Video Pipeline Core (7 files)
src/contentmanager/core/content/video_pipeline/__init__.py
src/contentmanager/core/content/video_pipeline/models.py
src/contentmanager/core/content/video_pipeline/script_generator.py
src/contentmanager/core/content/video_pipeline/voiceover_service.py
src/contentmanager/core/content/video_pipeline/asset_manager.py
src/contentmanager/core/content/video_pipeline/ffmpeg_renderer.py
src/contentmanager/core/content/video_pipeline/pipeline.py
src/contentmanager/core/content/video_pipeline/prompts.py

# Database (1 file to modify, 1 new)
src/contentmanager/database/models.py           # Modify: Add tables
src/contentmanager/database/repositories/video_project.py

# API (1 file)
src/contentmanager/dashboard/routers/video_projects.py

# UI (1 file)
src/contentmanager/dashboard/templates/video_projects.html

# Config (modify)
src/contentmanager/config.py                    # Modify: Add VideoSettings

# Directories to create
data/assets/characters/
data/assets/backgrounds/
data/assets/music/
data/projects/voiceovers/
data/projects/videos/
```

**Total MVP: 10 new files + 2 modifications + directories**

## MVP Configuration

```bash
# .env additions for MVP
# Eleven Labs
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_QUESTIONER_VOICE=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_EXPLAINER_VOICE=EXAVITQu4vr4xnSDxMaL

# Video
VIDEO_ASSETS_DIR=data/assets
VIDEO_PROJECTS_DIR=data/projects
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
VIDEO_FPS=30

# FFmpeg
FFMPEG_PATH=ffmpeg
```

```python
# config.py additions for MVP
class VideoSettings(BaseSettings):
    elevenlabs_api_key: str
    elevenlabs_questioner_voice: str = "JBFqnCBsd6RMkjVDRZzb"
    elevenlabs_explainer_voice: str = "EXAVITQu4vr4xnSDxMaL"

    video_assets_dir: Path = Path("data/assets")
    video_projects_dir: Path = Path("data/projects")
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30

    ffmpeg_path: str = "ffmpeg"
```

## MVP Dependencies

```toml
# pyproject.toml additions for MVP
elevenlabs = ">=1.0.0"
ffmpeg-python = ">=0.2.0"
```

```bash
# System dependencies for MVP
apt-get install ffmpeg
```

## MVP Implementation Schedule

### Week 1: Foundation + Script Generation

**Day 1-2: Database & Models**
- Add tables to models.py (Character, CharacterAsset, BackgroundAsset, MusicAsset, VideoProject, VideoScene)
- Create Alembic migration
- Create VideoProjectRepository with basic CRUD
- Create Pydantic request/response models

**Day 3-4: Script Generator**
- Create prompts.py with dialogue generation prompt
- Implement DialogueScriptGenerator class
- Integrate with existing Claude client
- Test with sample topics, tune prompt for quality

**Day 5: Asset Manager**
- Implement asset upload endpoints (characters, backgrounds, music)
- File storage handling with validation
- Basic image/audio type and size validation

### Week 2: Voiceover + Rendering

**Day 1-2: Voiceover Service**
- Eleven Labs client integration
- Generate per-scene audio segments
- Combine segments into single track
- Calculate scene timings from actual audio duration

**Day 3-4: FFmpeg Renderer**
- Build FFmpeg filter graph for video composition
- Character image positioning (left/right based on speaker)
- Text overlay with fade animation
- Audio synchronization
- Test output quality on various inputs

**Day 5: Pipeline Integration**
- Wire up full pipeline in pipeline.py
- Implement status transitions
- Add error handling and recovery
- Test full flow end-to-end

### Week 3: API + UI

**Day 1-2: API Endpoints**
- All CRUD endpoints for assets
- Project workflow endpoints (create, approve, render)
- File upload handling
- Download endpoint for completed videos

**Day 3-5: Dashboard UI**
- Asset library panel (upload/manage characters, backgrounds, music)
- Create video form (topic, style, character selection)
- Project queue with status filtering
- Script review modal with edit capability
- Preview audio and download buttons

### Week 4: Polish + Testing

**Day 1-2: End-to-end Testing**
- Full workflow test (upload assets → generate → approve → render → download)
- Edge cases (missing assets, long scripts, special characters)
- Error scenarios (API failures, invalid inputs)

**Day 3-4: UX Improvements**
- Loading states for long operations
- Clear error messages
- Progress indicators during rendering

**Day 5: Documentation**
- API documentation
- User guide for asset requirements
- Deployment notes

---

# PART 2: FULL PRODUCTION SYSTEM

The following sections describe the complete production system. Features are tagged with their implementation phase:

- **[MVP]** - Included in MVP
- **[Phase 2]** - Scale & batch processing
- **[Phase 3]** - Multi-tenant & branding
- **[Phase 4]** - Advanced features

---

## Full Architecture [Phase 2+]

```
src/contentmanager/
├── core/content/video_pipeline/      # Video pipeline modules
│   ├── __init__.py                   # [MVP]
│   ├── models.py                     # [MVP] Pydantic models
│   ├── script_generator.py           # [MVP] Dialogue generation
│   ├── voiceover_service.py          # [MVP] Eleven Labs integration
│   ├── asset_manager.py              # [MVP] Asset upload/selection
│   ├── ffmpeg_renderer.py            # [MVP] Simple video renderer
│   ├── remotion_renderer.py          # [Phase 4] Complex animation renderer
│   ├── render_strategy.py            # [Phase 4] Render strategy selector
│   ├── post_processor.py             # [Phase 2] FFmpeg post-processing
│   ├── brand_manager.py              # [Phase 3] Multi-client branding
│   ├── cost_tracker.py               # [Phase 3] Usage & cost tracking
│   ├── prompts.py                    # [MVP] LLM prompt templates
│   ├── pipeline.py                   # [MVP] Simplified orchestrator
│   └── orchestrator.py               # [Phase 2] Full pipeline coordinator
├── workers/                          # [Phase 2] Background job workers
│   ├── __init__.py
│   ├── base_worker.py
│   ├── script_worker.py
│   ├── voiceover_worker.py
│   ├── render_worker.py
│   └── postprocess_worker.py
├── database/
│   ├── models.py                     # [MVP] + extensions per phase
│   └── repositories/
│       ├── video_project.py          # [MVP]
│       └── brand_template.py         # [Phase 3]
├── dashboard/
│   ├── routers/video_projects.py     # [MVP] + extensions per phase
│   └── templates/video_projects.html # [MVP] + extensions per phase
└── remotion/                         # [Phase 4] Remotion video renderer
    ├── package.json
    ├── Dockerfile
    └── src/
        ├── Video.tsx
        ├── Scene.tsx
        ├── Character.tsx
        └── TextOverlay.tsx

data/
├── assets/                           # [MVP] User-uploaded assets
│   ├── characters/                   # Character images by pose
│   ├── backgrounds/
│   ├── icons/                        # [Phase 4] Animated icons
│   ├── transitions/                  # [Phase 4] Transition effects
│   └── music/
├── brands/                           # [Phase 3] Brand template assets
│   ├── default/
│   └── {client_name}/
├── projects/                         # [MVP] Generated content
│   ├── voiceovers/
│   └── videos/
└── videos/                           # [Phase 2] Post-processed outputs
    ├── raw/
    └── final/
```

---

## Worker Architecture [Phase 2]

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────────────────────┐
│    API Layer    │────▶│   Redis Queue   │────▶│           Workers               │
│  (FastAPI)      │     │                 │     │                                 │
└─────────────────┘     │  - script_q     │     │  ┌─────────────────────────┐   │
                        │  - voiceover_q  │     │  │    Script Workers (N)   │   │
                        │  - render_q     │     │  │    (Claude API calls)   │   │
                        │  - postproc_q   │     │  └─────────────────────────┘   │
                        │  - batch_q      │     │  ┌─────────────────────────┐   │
                        └─────────────────┘     │  │   Voiceover Workers (N) │   │
                                                │  │   (Eleven Labs API)     │   │
                                                │  └─────────────────────────┘   │
                                                │  ┌─────────────────────────┐   │
                                                │  │    Render Workers (N)   │   │
                                                │  │  (FFmpeg / Remotion)    │   │
                                                │  └─────────────────────────┘   │
                                                │  ┌─────────────────────────┐   │
                                                │  │  PostProcess Workers(N) │   │
                                                │  │     (FFmpeg only)       │   │
                                                │  └─────────────────────────┘   │
                                                └─────────────────────────────────┘
```

### Queue Priority System [Phase 2]
- **Priority 1 (High):** Single video generation (user waiting)
- **Priority 2 (Medium):** Batch processing jobs
- **Priority 3 (Low):** Re-rendering, format conversion

---

## Hybrid Rendering Strategy [Phase 4]

### Decision Logic
```python
class RenderStrategy(Enum):
    FFMPEG_SIMPLE = "ffmpeg"      # Fast, low resource, no browser
    REMOTION_FULL = "remotion"    # Rich animations, browser-based

def select_strategy(project: VideoProject) -> RenderStrategy:
    """Select rendering strategy based on project complexity."""
    # Use FFmpeg for simple videos (text + static images + audio)
    if all([
        not project.has_complex_transitions,
        not project.has_animated_icons,
        project.text_animation in ["fade_in", "none"],
    ]):
        return RenderStrategy.FFMPEG_SIMPLE

    # Use Remotion for complex animations
    return RenderStrategy.REMOTION_FULL
```

### FFmpeg Simple Renderer [MVP]
- Handles: Static backgrounds, character images, simple text overlays, audio sync
- Resource usage: ~100MB RAM, no GPU required
- Speed: ~5-10x faster than Remotion

### Remotion Full Renderer [Phase 4]
- Handles: Complex animations, transitions, animated icons, dynamic effects
- Resource usage: ~2GB RAM (headless Chrome), optional GPU
- Quality: Higher visual fidelity for complex content

---

## Full Database Schema

### Additional Enums [Phase 2+]

```python
# [Phase 2] Output format support
class OutputFormat(str, Enum):
    TIKTOK = "tiktok"              # 1080x1920 (9:16)
    YOUTUBE_SHORT = "youtube_short" # 1080x1920 (9:16)
    TWITTER_SQUARE = "twitter_square" # 1080x1080 (1:1)
    TWITTER_WIDE = "twitter_wide"   # 1920x1080 (16:9)
    INSTAGRAM_REEL = "instagram_reel" # 1080x1920 (9:16)
    INSTAGRAM_POST = "instagram_post" # 1080x1080 (1:1)

# [Phase 4] Render strategy
class RenderStrategy(str, Enum):
    FFMPEG_SIMPLE = "ffmpeg"
    REMOTION_FULL = "remotion"
    AUTO = "auto"

# [Phase 4] Text animation options
class TextAnimation(str, Enum):
    NONE = "none"
    FADE_IN = "fade_in"
    POP = "pop"
    SLIDE_IN = "slide_in"
    TYPEWRITER = "typewriter"
    HIGHLIGHT_KEYWORDS = "highlight_keywords"

# [Phase 3] Watermark positioning
class WatermarkPosition(str, Enum):
    TOP_LEFT = "top_left"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_RIGHT = "bottom_right"
    CENTER = "center"
```

### Additional Tables

**BrandTemplate [Phase 3]** - Multi-client branding
```python
class BrandTemplate(Base):
    __tablename__ = "brand_templates"

    id: int (PK)
    name: str
    client_id: int (FK, nullable)  # None = default template

    # Colors (hex codes)
    color_primary: str = "#1a1a2e"
    color_secondary: str = "#16213e"
    color_accent: str = "#e94560"
    color_text: str = "#ffffff"
    color_background: str = "#0f0f23"

    # Typography
    font_heading: str = "Poppins"
    font_body: str = "Inter"

    # Assets
    logo_path: str (nullable)
    watermark_path: str (nullable)
    watermark_position: WatermarkPosition = "bottom_right"
    watermark_opacity: float = 0.7
    intro_video_path: str (nullable)
    outro_video_path: str (nullable)

    # Audio
    default_questioner_voice: str (nullable)
    default_explainer_voice: str (nullable)
    default_music_track: str (nullable)

    # Metadata
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
```

**VideoProjectOutput [Phase 2]** - One project → multiple format outputs
```python
class VideoProjectOutput(Base):
    __tablename__ = "video_project_outputs"

    id: int (PK)
    project_id: int (FK)

    output_format: OutputFormat
    file_path: str
    file_size_bytes: int

    width: int
    height: int
    duration_seconds: float
    bitrate_kbps: int

    is_compressed: bool = False
    is_watermarked: bool = False
    compression_ratio: float (nullable)

    created_at: datetime
```

**UsageMetrics [Phase 3]** - Cost tracking
```python
class UsageMetrics(Base):
    __tablename__ = "usage_metrics"

    id: int (PK)
    project_id: int (FK, unique)
    client_id: int (FK, nullable)

    eleven_labs_characters: int = 0
    eleven_labs_cost_usd: float = 0.0

    render_strategy_used: RenderStrategy
    render_seconds: float = 0.0
    render_cost_usd: float = 0.0

    storage_bytes: int = 0
    storage_cost_usd: float = 0.0

    total_cost_usd: float = 0.0

    created_at: datetime
```

**BatchJob [Phase 2]** - Batch processing tracking
```python
class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: int (PK)
    name: str
    client_id: int (FK, nullable)

    document_id: int (FK, nullable)
    topics: JSON
    context_style: ContextStyle
    target_formats: JSON
    brand_template_id: int (FK, nullable)

    total_count: int
    completed_count: int = 0
    failed_count: int = 0
    status: str = "pending"

    project_ids: JSON

    scheduled_at: datetime (nullable)
    started_at: datetime (nullable)
    completed_at: datetime (nullable)

    created_at: datetime
    updated_at: datetime
```

---

## Script Generation Module [MVP]

**File:** `src/contentmanager/core/content/video_pipeline/script_generator.py`

```python
class DialogueScriptGenerator:
    """Generates dialogue scripts for educational videos."""

    def __init__(self, llm_client: ClaudeClient):
        self.llm = llm_client

    async def generate(
        self,
        topic: str,
        context_style: ContextStyle,
        document_context: str | None = None,
        questioner_name: str = "Thabo",
        explainer_name: str = "Lerato",
        target_duration: int = 45,
    ) -> DialogueScript:
        """Generate dialogue script with scene breakdown."""

    # [Phase 4] Additional methods
    async def generate_from_trending(
        self,
        trending_topic: str,
        context_style: ContextStyle,
    ) -> DialogueScript:
        """Generate script from trending topic."""

    async def extract_topics_from_document(
        self,
        document_content: str,
        max_topics: int = 10
    ) -> list[TopicSuggestion]:
        """Extract video-worthy topics from a document."""
```

---

## Voiceover Service [MVP]

**File:** `src/contentmanager/core/content/video_pipeline/voiceover_service.py`

```python
from elevenlabs.client import ElevenLabs

class VoiceoverService:
    """Generates voiceovers using Eleven Labs API."""

    def __init__(self, api_key: str):
        self.client = ElevenLabs(api_key=api_key)
        self.default_voices = {
            "questioner": "JBFqnCBsd6RMkjVDRZzb",
            "explainer": "EXAVITQu4vr4xnSDxMaL",
        }

    async def generate_voiceover(
        self,
        script: DialogueScript,
        output_dir: Path,
        voice_config: dict | None = None
    ) -> VoiceoverResult:
        """Generate voiceover for each scene line."""

    async def generate_segment(
        self,
        text: str,
        voice_id: str,
        output_path: Path
    ) -> AudioSegment:
        """Generate single audio segment."""

    async def list_voices(self) -> list[Voice]:
        """List available voices for selection."""
```

---

## FFmpeg Renderer [MVP]

**File:** `src/contentmanager/core/content/video_pipeline/ffmpeg_renderer.py`

```python
import ffmpeg

class FFmpegRenderer:
    """Video rendering using FFmpeg."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path

    async def render_video(
        self,
        project: VideoProject,
        scenes: list[VideoScene],
        output_path: Path,
    ) -> RenderResult:
        """
        Render video using FFmpeg filter complex.

        Handles:
        - Static background image
        - Character image overlay with positioning
        - Text overlay with basic fade animation
        - Audio track synchronization
        """

    def _build_filter_complex(
        self,
        scenes: list[VideoScene],
    ) -> str:
        """Build FFmpeg filter complex string."""
```

---

## Post-Processing Pipeline [Phase 2]

**File:** `src/contentmanager/core/content/video_pipeline/post_processor.py`

```python
class VideoPostProcessor:
    """Post-processing pipeline using FFmpeg."""

    async def process(
        self,
        input_path: Path,
        output_path: Path,
        config: PostProcessConfig
    ) -> PostProcessResult:
        """Apply full post-processing pipeline."""

    async def resize(self, input_path: Path, target_format: OutputFormat) -> Path:
        """Resize/crop video to target dimensions."""

    async def add_watermark(self, input_path: Path, watermark_path: Path, position: WatermarkPosition) -> Path:
        """Overlay watermark on video."""

    async def compress(self, input_path: Path, target_bitrate: str, crf: int) -> Path:
        """Compress video with quality optimization."""

    async def normalize_audio(self, input_path: Path) -> Path:
        """Normalize audio levels."""

    async def concat_segments(self, intro: Path, main: Path, outro: Path) -> Path:
        """Concatenate intro, main content, and outro."""

    # Utility methods for standalone operations
    async def trim(self, input_path: Path, start: float, end: float, output_path: Path) -> Path:
    async def merge(self, input_paths: list[Path], output_path: Path) -> Path:
    async def extract_audio(self, input_path: Path, output_path: Path) -> Path:
    async def replace_audio(self, video_path: Path, audio_path: Path, output_path: Path) -> Path:
```

---

## Brand Manager [Phase 3]

**File:** `src/contentmanager/core/content/video_pipeline/brand_manager.py`

```python
class BrandManager:
    """Manages brand templates and client-specific configurations."""

    async def get_template(self, template_id: int | None, client_id: int | None) -> BrandTemplate:
        """Get brand template by ID or client, falls back to default."""

    async def create_template(self, name: str, client_id: int | None, config: BrandConfig) -> BrandTemplate:
        """Create new brand template."""

    def generate_post_process_config(self, template: BrandTemplate, target_formats: list[OutputFormat]) -> list[PostProcessConfig]:
        """Generate post-processing configs for each target format."""
```

---

## Cost Tracker [Phase 3]

**File:** `src/contentmanager/core/content/video_pipeline/cost_tracker.py`

```python
class CostTracker:
    """Tracks and estimates costs for video generation."""

    def estimate_cost(self, script: DialogueScript, render_strategy: RenderStrategy, target_formats: list[OutputFormat]) -> CostEstimate:
        """Estimate total cost before processing."""

    async def record_usage(self, project_id: int, metrics: UsageMetricsData) -> UsageMetrics:
        """Record actual usage after processing."""

    async def get_usage_summary(self, client_id: int | None, start_date: datetime, end_date: datetime) -> UsageSummary:
        """Get usage summary for billing/reporting."""
```

---

## Full API Endpoints

```python
# [MVP] Asset Management
POST   /api/video/characters
GET    /api/video/characters
POST   /api/video/characters/{id}/assets
DELETE /api/video/characters/{id}/assets/{aid}
POST   /api/video/backgrounds
GET    /api/video/backgrounds
POST   /api/video/music
GET    /api/video/music

# [MVP] Video Project Workflow
POST   /api/video/projects
GET    /api/video/projects
GET    /api/video/projects/{id}
PATCH  /api/video/projects/{id}
DELETE /api/video/projects/{id}
POST   /api/video/projects/{id}/approve
POST   /api/video/projects/{id}/reject
POST   /api/video/projects/{id}/regenerate
POST   /api/video/projects/{id}/render
GET    /api/video/projects/{id}/download
GET    /api/video/projects/{id}/preview-audio

# [MVP] Settings
GET    /api/video/voices
POST   /api/video/settings

# [Phase 2] Async & Batch
POST   /api/video/generate-async
POST   /api/video/generate-batch
POST   /api/video/analyze-document
GET    /api/video/batches
GET    /api/video/batches/{id}
POST   /api/video/batches/{id}/cancel

# [Phase 2] Multi-format
GET    /api/video/projects/{id}/download/{format}
POST   /api/video/projects/{id}/reformat
GET    /api/video/formats

# [Phase 2] Transform Operations
POST   /api/video/transform/trim
POST   /api/video/transform/merge
POST   /api/video/transform/resize
POST   /api/video/transform/compress
POST   /api/video/transform/watermark

# [Phase 3] Brand Templates
GET    /api/video/brands
POST   /api/video/brands
GET    /api/video/brands/{id}
PATCH  /api/video/brands/{id}
DELETE /api/video/brands/{id}

# [Phase 3] Usage & Costs
GET    /api/video/usage
GET    /api/video/usage/estimate
GET    /api/video/usage/summary

# [Phase 2] System
GET    /api/video/health
GET    /api/video/queues
```

---

## Dashboard UI Sections

### MVP UI
1. **Asset Library** - Upload/manage characters, backgrounds, music
2. **Create Video** - Topic input, style selection, character assignment
3. **Project Queue** - List with status filtering, actions
4. **Script Review Modal** - View/edit script, approve/reject

### Phase 2 Additions
5. **Batch Jobs** - Create and monitor batch processing
6. **Format Selection** - Multi-format output options

### Phase 3 Additions
7. **Brands Tab** - Brand template management
8. **Analytics Tab** - Usage metrics, cost breakdown

### Phase 4 Additions
9. **Advanced Settings** - Render strategy, animation options

---

## Full Configuration [All Phases]

```bash
# .env - All phases
# [MVP] Eleven Labs
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_QUESTIONER_VOICE=JBFqnCBsd6RMkjVDRZzb
ELEVENLABS_EXPLAINER_VOICE=EXAVITQu4vr4xnSDxMaL

# [MVP] Video Settings
VIDEO_ASSETS_DIR=data/assets
VIDEO_PROJECTS_DIR=data/projects
VIDEO_WIDTH=1080
VIDEO_HEIGHT=1920
VIDEO_FPS=30

# [MVP] FFmpeg
FFMPEG_PATH=/usr/bin/ffmpeg
FFPROBE_PATH=/usr/bin/ffprobe
FFMPEG_THREADS=4
DEFAULT_CRF=23
DEFAULT_BITRATE=5M

# [Phase 2] Worker Configuration
REDIS_URL=redis://localhost:6379
WORKER_CONCURRENCY=4
MAX_SCRIPT_WORKERS=2
MAX_VOICEOVER_WORKERS=2
MAX_RENDER_WORKERS=2
MAX_POSTPROCESS_WORKERS=4

# [Phase 4] Remotion
REMOTION_PATH=src/contentmanager/remotion
REMOTION_CONCURRENCY=1

# [Phase 3] Cost Tracking
ELEVENLABS_COST_PER_CHAR=0.00003
REMOTION_COST_PER_MINUTE=0.05
FFMPEG_COST_PER_MINUTE=0.001
STORAGE_COST_PER_MB=0.0001

# [Phase 2] Scaling
MAX_BATCH_SIZE=100
RENDER_TIMEOUT_SECONDS=300
MAX_VIDEO_DURATION_SECONDS=120
```

---

## Dependencies by Phase

### MVP
```toml
# pyproject.toml
elevenlabs = ">=1.0.0"
ffmpeg-python = ">=0.2.0"
```

```bash
# System
apt-get install ffmpeg
```

### Phase 2
```toml
# Additional
redis = ">=5.0.0"
rq = ">=1.15.0"
```

```bash
# Additional system
apt-get install redis-server
```

### Phase 4
```json
// remotion/package.json
{
  "dependencies": {
    "@remotion/cli": "^4.0.0",
    "@remotion/renderer": "^4.0.0",
    "react": "^18.0.0",
    "lottie-react": "^2.4.0"
  }
}
```

```bash
# Additional system
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install nodejs
```

---

## Files by Phase

### MVP Files (10 new + 2 modify)
```
# New
src/contentmanager/core/content/video_pipeline/__init__.py
src/contentmanager/core/content/video_pipeline/models.py
src/contentmanager/core/content/video_pipeline/script_generator.py
src/contentmanager/core/content/video_pipeline/voiceover_service.py
src/contentmanager/core/content/video_pipeline/asset_manager.py
src/contentmanager/core/content/video_pipeline/ffmpeg_renderer.py
src/contentmanager/core/content/video_pipeline/pipeline.py
src/contentmanager/core/content/video_pipeline/prompts.py
src/contentmanager/database/repositories/video_project.py
src/contentmanager/dashboard/routers/video_projects.py
src/contentmanager/dashboard/templates/video_projects.html

# Modify
src/contentmanager/database/models.py
src/contentmanager/config.py
```

### Phase 2 Files (+8 new)
```
src/contentmanager/core/content/video_pipeline/post_processor.py
src/contentmanager/core/content/video_pipeline/orchestrator.py
src/contentmanager/workers/__init__.py
src/contentmanager/workers/base_worker.py
src/contentmanager/workers/script_worker.py
src/contentmanager/workers/voiceover_worker.py
src/contentmanager/workers/render_worker.py
src/contentmanager/workers/postprocess_worker.py
```

### Phase 3 Files (+2 new)
```
src/contentmanager/core/content/video_pipeline/brand_manager.py
src/contentmanager/core/content/video_pipeline/cost_tracker.py
src/contentmanager/database/repositories/brand_template.py
```

### Phase 4 Files (+10 new)
```
src/contentmanager/core/content/video_pipeline/remotion_renderer.py
src/contentmanager/core/content/video_pipeline/render_strategy.py
src/contentmanager/remotion/package.json
src/contentmanager/remotion/tsconfig.json
src/contentmanager/remotion/Dockerfile
src/contentmanager/remotion/src/index.ts
src/contentmanager/remotion/src/Video.tsx
src/contentmanager/remotion/src/Scene.tsx
src/contentmanager/remotion/src/Character.tsx
src/contentmanager/remotion/src/TextOverlay.tsx
```

---

## Migration Guides

### MVP → Phase 2 Migration

**When to migrate:** Daily volume exceeds 20 videos OR users request batch processing

**Steps:**
1. Add Redis dependency and start Redis server
2. Add worker dependencies to pyproject.toml
3. Create worker files (base_worker.py, etc.)
4. Add VideoProjectOutput and BatchJob tables to models.py
5. Run Alembic migration
6. Create post_processor.py and orchestrator.py
7. Update API endpoints to support async operations
8. Add batch processing UI to dashboard
9. Deploy workers alongside main application
10. Test batch processing end-to-end

**Database changes:**
```sql
-- Add new tables
CREATE TABLE video_project_outputs (...);
CREATE TABLE batch_jobs (...);

-- Add columns to video_projects
ALTER TABLE video_projects ADD COLUMN target_formats JSON;
ALTER TABLE video_projects ADD COLUMN priority INTEGER DEFAULT 2;
```

**Configuration changes:**
```bash
# Add to .env
REDIS_URL=redis://localhost:6379
WORKER_CONCURRENCY=4
```

### Phase 2 → Phase 3 Migration

**When to migrate:** Second client onboarded OR need branded outputs

**Steps:**
1. Create BrandTemplate table
2. Create UsageMetrics table
3. Create brand_manager.py and cost_tracker.py
4. Add tenant_id foreign keys to all relevant tables (populate as NULL for existing data)
5. Run Alembic migration
6. Create brand template API endpoints
7. Add Brands tab to dashboard
8. Add Analytics tab to dashboard
9. Implement cost tracking in pipeline
10. Test multi-tenant isolation

**Database changes:**
```sql
-- Add new tables
CREATE TABLE brand_templates (...);
CREATE TABLE usage_metrics (...);

-- Add tenant_id to existing tables (nullable)
ALTER TABLE characters ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE video_projects ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
-- ... etc for all asset tables
```

### Phase 3 → Phase 4 Migration

**When to migrate:** Users request animated icons OR complex text animations

**Steps:**
1. Set up Node.js environment
2. Create Remotion project structure
3. Install Remotion dependencies
4. Create remotion_renderer.py and render_strategy.py
5. Add TextAnimation enum and related fields
6. Update pipeline to support render strategy selection
7. Add animation options to dashboard
8. Test Remotion rendering
9. Monitor resource usage, adjust worker allocation

**System requirements:**
```bash
# Node.js required
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install nodejs

# Additional RAM for Remotion workers
# Recommend: 4GB+ per render worker
```

---

## Example Output Video Structure

```
1. [0.0s - 0.5s]   Title fade in (topic)
2. [0.5s - 5.0s]   Scene 1: Questioner asks
   - Character: Left side (thinking pose)
   - Text: Line with fade animation
   - Audio: Questioner voiceover
3. [5.0s - 11.0s]  Scene 2: Explainer responds
   - Character: Right side (pointing pose)
   - Text: Line with fade animation
   - Audio: Explainer voiceover
4. [11.0s - ...]   Continue alternating...
5. [Last 3s]       Takeaway card with key message
6. [End]           Background music fades out
```

### Multi-Format Output [Phase 2]

Single render (1080x1920) → Post-processing generates:

| Format | Dimensions | Aspect | Use Case |
|--------|------------|--------|----------|
| TikTok | 1080x1920 | 9:16 | TikTok, YouTube Shorts |
| Twitter Square | 1080x1080 | 1:1 | Twitter/X feed |
| Twitter Wide | 1920x1080 | 16:9 | Twitter/X landscape |
| Instagram Reel | 1080x1920 | 9:16 | Instagram Reels |
| Instagram Post | 1080x1080 | 1:1 | Instagram feed |

---

## Verification Plan

### MVP Testing
- [ ] Asset upload (characters, backgrounds, music)
- [ ] Script generation from topic
- [ ] Script editing and approval
- [ ] Voiceover generation
- [ ] Video rendering
- [ ] Download completed video
- [ ] Error handling for each step

### Phase 2 Testing
- [ ] Background job processing
- [ ] Batch job creation and monitoring
- [ ] Multi-format output generation
- [ ] Post-processing operations
- [ ] Worker health and recovery

### Phase 3 Testing
- [ ] Brand template CRUD
- [ ] Branded video output
- [ ] Cost tracking accuracy
- [ ] Multi-tenant data isolation
- [ ] Usage reporting

### Phase 4 Testing
- [ ] Remotion rendering
- [ ] Render strategy selection
- [ ] Animated icons and transitions
- [ ] Performance under load

---

## Monitoring & Observability [Phase 2+]

### Metrics to Track
- Queue depth per queue type
- Average processing time per step
- Error rate by step
- Cost per video
- Videos generated per hour/day
- Worker utilization

### Alerts
- Queue depth > threshold
- Error rate spike
- Worker death
- Cost threshold exceeded
- Storage usage high

### Logging
- Structured JSON logs
- Request ID tracing through pipeline
- Step timing logs
- Error stack traces with context

---

## Sources

- [ElevenLabs Python SDK](https://github.com/elevenlabs/elevenlabs-python)
- [ElevenLabs Developer Docs](https://elevenlabs.io/developers)
- [Remotion Documentation](https://www.remotion.dev/)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)
- [Redis Queue (RQ)](https://python-rq.org/)
- [Lottie Animations](https://lottiefiles.com/)
