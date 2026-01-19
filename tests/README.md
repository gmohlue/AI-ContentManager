# AI-ContentManager Test Suite

Comprehensive test suite for the AI-ContentManager MVP application.

## Test Coverage Summary

**Total Tests:** 144 passing tests across 4 test modules
**Coverage:** 49% overall code coverage (core tested modules at 78-100%)

### Test Modules

1. **test_models.py** - Pydantic model validation (28 tests)
2. **test_repositories.py** - Database repository operations (46 tests)
3. **test_asset_manager.py** - Asset management (37 tests)
4. **test_ffmpeg_renderer.py** - Video rendering logic (33 tests)
5. **test_api_endpoints.py** - FastAPI endpoints (37 tests - pending fixture fixes)

## Running Tests

### Run All Core Tests
```bash
# Run all core tests (models, repositories, asset_manager, ffmpeg_renderer)
pytest tests/test_models.py tests/test_repositories.py tests/test_asset_manager.py tests/test_ffmpeg_renderer.py -v

# Run with coverage report
pytest tests/test_models.py tests/test_repositories.py tests/test_asset_manager.py tests/test_ffmpeg_renderer.py --cov=src/contentmanager --cov-report=html
```

### Run Individual Test Modules
```bash
# Test Pydantic models
pytest tests/test_models.py -v

# Test database repositories
pytest tests/test_repositories.py -v

# Test asset manager
pytest tests/test_asset_manager.py -v

# Test FFmpeg renderer
pytest tests/test_ffmpeg_renderer.py -v
```

### Run Specific Test Classes
```bash
# Test only enum validation
pytest tests/test_models.py::TestEnums -v

# Test only VideoProjectRepository
pytest tests/test_repositories.py::TestVideoProjectRepository -v

# Test only file validation
pytest tests/test_asset_manager.py::TestFileValidation -v
```

## Test Structure

### 1. test_models.py (28 tests)

Tests for Pydantic models in `src/contentmanager/core/content/video_pipeline/models.py`

#### Coverage:
- **Enum Validation** (6 tests)
  - `ContextStyle` enum (MOTIVATION, FINANCE, TECH, EDUCATIONAL)
  - `CharacterRole` enum (QUESTIONER, EXPLAINER)
  - `VideoProjectStatus` enum (DRAFT, APPROVED, AUDIO_READY, RENDERING, COMPLETED, FAILED)
  - Invalid enum value handling

- **DialogueLine Model** (4 tests)
  - Valid dialogue line creation
  - Default pose value
  - Custom pose values
  - Missing required field validation

- **DialogueScript Model** (4 tests)
  - Valid script with lines
  - Default target duration (45 seconds)
  - Empty lines list handling
  - Multiple dialogue lines

- **AudioSegment Model** (2 tests)
  - Valid audio segment
  - Default start_time value

- **VoiceoverResult Model** (2 tests)
  - Valid voiceover result with segments
  - Empty segments handling

- **RenderResult Model** (3 tests)
  - Valid render result
  - Default timestamp generation
  - TikTok portrait format validation

- **VideoProjectCreate Model** (3 tests)
  - Valid project creation request
  - Optional fields (background_music_id, document_id)
  - Missing required fields validation

- **VideoProjectResponse Model** (4 tests)
  - Valid response model
  - Optional fields as None
  - Failed status with error message
  - from_attributes configuration

### 2. test_repositories.py (46 tests)

Tests for database repositories in `src/contentmanager/database/repositories/video_project.py`

#### VideoProjectRepository (22 tests)
- **CRUD Operations:**
  - Create project with required fields
  - Create with optional fields (music, document, tenant)
  - Get by ID with relationships loaded
  - Get by ID not found
  - List all projects
  - List with status filter
  - List with tenant filter
  - List with pagination (limit, offset)
  - Delete project
  - Delete not found

- **Status Management:**
  - Update status
  - Update status with error message
  - Update status not found
  - Approve project (status transition)
  - Approve non-draft project (returns None)

- **Script & Media:**
  - Update script JSON and takeaway
  - Set voiceover path
  - Update voiceover alias
  - Set output path and duration
  - Update output alias

- **Scenes:**
  - Add scene to project
  - Update scene audio timing

#### CharacterRepository (11 tests)
- Create character
- Create with tenant_id
- Get by ID with assets loaded
- Get by ID not found
- List all characters
- List by tenant
- Add asset to character
- Add multiple assets
- Get asset by ID
- Delete asset
- Delete asset not found

#### AssetRepository (13 tests)
- **Background Assets:**
  - Create background with style
  - Create without style
  - List all backgrounds
  - List by context_style
  - Get by ID
  - Delete background
  - Delete not found

- **Music Assets:**
  - Create music with duration
  - List all music
  - List by context_style
  - Get by ID
  - Delete music
  - Delete not found

### 3. test_asset_manager.py (37 tests)

Tests for `src/contentmanager/core/content/video_pipeline/asset_manager.py`

#### Initialization (2 tests)
- Creates required subdirectories
- Handles existing directories

#### File Validation (4 tests)
- Valid image file extensions (.png, .jpg, .jpeg, .webp)
- Invalid image file types raise ValueError
- Valid audio file extensions (.mp3, .wav, .m4a, .ogg)
- Invalid audio file types raise ValueError

#### Filename Sanitization (6 tests)
- Alphanumeric characters preserved
- Spaces replaced with underscores
- Special characters replaced
- Dashes and underscores preserved
- Length limited to 50 characters
- Unicode handling

#### Character Assets (5 tests)
- Save PNG character asset
- Create character directory if needed
- Overwrite existing pose
- Invalid file type raises error
- Preserve file extension

#### Background Assets (5 tests)
- Save with context_style (creates subdirectory)
- Save without style (uses "general" directory)
- Create style subdirectory
- Sanitize background name
- Invalid file type raises error

#### Music Assets (4 tests)
- Save with context_style
- Save without style
- Different audio formats (.mp3, .wav, .m4a, .ogg)
- Invalid file type raises error

#### Delete Operations (4 tests)
- Delete existing asset
- Delete non-existent file (returns False)
- Security check (prevents deletion outside assets dir)
- Directory traversal protection

#### Character Asset Retrieval (5 tests)
- Get assets for character with no assets
- Get single asset
- Get multiple assets
- Only return image files
- Include metadata (pose, file_path, file_size_bytes)

#### Integration (2 tests)
- Full character workflow (create, retrieve, delete)
- Multiple context styles organization

### 4. test_ffmpeg_renderer.py (33 tests)

Tests for `src/contentmanager/core/content/video_pipeline/ffmpeg_renderer.py`

#### Initialization (3 tests)
- Default values
- Custom values
- TikTok portrait dimensions (1080x1920)

#### Text Escaping (8 tests)
- Simple text without special characters
- Backslash escaping
- Single quote escaping
- Colon escaping
- Percent sign escaping
- Multiple special characters
- Empty string
- Unicode preservation

#### Filter Complex Building (7 tests)
- Basic filter complex structure
- Background scaling to output dimensions
- Text overlays for each dialogue line
- Fade-in animation effects
- Output label [outv]
- Empty lines handling
- Single line script
- Special character escaping in dialogue

#### FFmpeg Command Building (8 tests)
- Basic command structure (ffmpeg -y)
- Input files (background, voiceover)
- Background music input
- Filter_complex inclusion
- Output encoding settings (libx264, aac)
- Output path in command
- Audio mapping from voiceover
- Pixel format (yuv420p)

#### Character Positioning (3 tests)
- Questioner positioned left (x=50)
- Explainer positioned right (x=width-50)
- Mixed positioning in single script

#### Filter Structure (3 tests)
- Semicolon-separated filters
- Intermediate stream labels [v0], [v1]
- Proper filter chaining [bg] → [v0] → [v1] → [outv]

## Test Coverage by Module

### Core Tested Modules (High Coverage)

| Module | Statements | Covered | Coverage | Missing Lines |
|--------|-----------|---------|----------|---------------|
| `models.py` | 71 | 71 | **100%** | - |
| `asset_manager.py` | 81 | 81 | **100%** | - |
| `database/models.py` | 82 | 82 | **100%** | - |
| `repositories/video_project.py` | 181 | 175 | **97%** | 6 lines (edge cases) |
| `ffmpeg_renderer.py` | 58 | 45 | **78%** | Actual rendering execution |

### Modules Not Requiring API Keys (Mocked)

The following modules require external API keys and are tested via mocking:
- `script_generator.py` - Claude API (31% coverage - structure tested, API calls mocked)
- `voiceover_service.py` - Eleven Labs API (25% coverage - structure tested, API calls mocked)
- `pipeline.py` - Orchestration (37% coverage - individual components fully tested)

### API Endpoints (Pending)

API endpoint tests in `test_api_endpoints.py` are scaffolded but require additional fixture configuration for full integration testing. Core business logic is covered by repository tests.

## Test Fixtures

### Database Fixtures (conftest.py)

```python
@pytest.fixture
def db_engine():
    """In-memory SQLite database for testing."""

@pytest.fixture
def db_session(db_engine):
    """Database session with automatic rollback."""
```

### Asset Manager Fixtures (test_asset_manager.py)

```python
@pytest.fixture
def temp_assets_dir():
    """Temporary directory for asset tests."""

@pytest.fixture
def asset_manager(temp_assets_dir):
    """AssetManager instance with temp directory."""
```

### FFmpeg Renderer Fixtures (test_ffmpeg_renderer.py)

```python
@pytest.fixture
def ffmpeg_renderer():
    """FFmpegRenderer instance with default config."""

@pytest.fixture
def sample_script():
    """Sample DialogueScript for testing."""
```

## Key Test Patterns

### 1. Pydantic Model Validation
```python
# Test valid model creation
def test_model_valid():
    model = Model(field1="value", field2=123)
    assert model.field1 == "value"

# Test validation errors
def test_model_invalid():
    with pytest.raises(ValidationError):
        Model(invalid_field="value")
```

### 2. Database Repository Testing
```python
# Test CRUD with in-memory database
def test_create(db_session):
    repo = Repository(db_session)
    entity = repo.create(name="Test")
    assert entity.id is not None
    assert entity.name == "Test"
```

### 3. Async Testing
```python
@pytest.mark.asyncio
async def test_async_operation(asset_manager):
    result = await asset_manager.save_asset(...)
    assert result.exists()
```

### 4. Mock External APIs
```python
@patch("module.get_external_service")
def test_with_mock(mock_service):
    mock_service.return_value = Mock()
    # Test logic without actual API calls
```

## Edge Cases Covered

### Validation
- Missing required fields
- Invalid enum values
- Type mismatches
- Empty collections
- None values where applicable

### Security
- Path traversal attacks (../)
- Files outside allowed directories
- File type validation
- Filename sanitization

### Data Integrity
- Foreign key constraints (character IDs)
- Status workflow transitions
- Tenant isolation
- Cascade deletes

### Business Logic
- Approval only in DRAFT status
- Rendering only in AUDIO_READY status
- Pagination boundaries
- Filter combinations

## Known Limitations

1. **API Endpoint Tests:** Require additional FastAPI TestClient configuration
2. **External Services:** Claude and Eleven Labs APIs tested via mocks only
3. **Video Rendering:** FFmpeg execution not tested (command building fully tested)
4. **File I/O:** Uses temporary directories and in-memory databases

## Next Steps

To achieve higher coverage:

1. **Fix API endpoint test fixtures** - Configure TestClient with proper dependency injection
2. **Add integration tests** - Test full pipeline with mocked external services
3. **Add performance tests** - Test pagination, bulk operations
4. **Add error recovery tests** - Test failure scenarios and rollbacks

## Test Best Practices

This test suite follows:
- **Arrange-Act-Assert** pattern
- **Descriptive test names** that explain what is being tested
- **Isolated tests** with proper setup and teardown
- **Edge case coverage** for validation and security
- **Mock external dependencies** to avoid API costs
- **Database transactions** that rollback after each test
