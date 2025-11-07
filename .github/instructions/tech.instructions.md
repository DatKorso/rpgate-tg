---
applyTo: '**'
---
# Tech Stack & Build System

## Package Manager
**UV** - Fast Python package manager (10-100x faster than pip)

## Core Dependencies

### Bot Framework
- **Aiogram 3.13.0** - Telegram bot framework with FSM support
- Async/await throughout
- FSM (Finite State Machine) for conversation state management
- MemoryStorage for MVP (Redis planned for production)

### Web Framework
- **FastAPI** - Reserved for Sprint 4 webhooks (currently using polling)

### LLM Integration
- **OpenRouter** - LLM API gateway providing access to multiple models
- **OpenAI client library** - For API calls
- Primary model: `x-ai/grok-4-fast` (fast, cost-effective)
- Alternative models: `x-ai/grok-2` (higher quality narrative)

### Configuration
- **Pydantic Settings** - Type-safe configuration management
- **python-dotenv** - Environment variable loading
- Configuration centralized in `app/config.py`

### Future (Sprint 3+)
- **PostgreSQL + pgvector** - Database with vector search (via Supabase)
- **CrewAI** - Agent orchestration framework

## Development Dependencies
- **pytest** - Testing framework
- **pytest-asyncio** - Async test support
- **black** - Code formatting
- **ruff** - Fast Python linter

## Common Commands

### Setup
```bash
# Install dependencies
uv sync

# Create .env file
cp .env.example .env
# Then edit .env with your API keys

# Check setup (optional but recommended)
uv run python check_setup.py
```

### Running
```bash
# Start the bot
uv run python -m app.main

# Or use the shortcut
uv run start
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_character.py

# Run with verbose output
uv run pytest -v
```

### Development
```bash
# Format code
uv run black app/ tests/

# Lint code
uv run ruff check app/ tests/

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev package-name
```

## Environment Variables
Required in `.env` file:
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `OPENROUTER_API_KEY` - From openrouter.ai
- `SITE_URL` - Default: http://localhost:8000
- `LLM_MODEL` - Default: x-ai/grok-4-fast

## Python Version
Requires Python >= 3.11 (specified in `pyproject.toml`)

## Project Configuration
All project metadata in `pyproject.toml`:
- Package name: `rpgate-tg`
- Build system: hatchling
- Entry point: `app.main:main` (accessible via `uv run start`)
