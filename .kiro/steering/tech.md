---
inclusion: always
---

# Tech Stack & Build System

## Package Manager & Python
- **UV** - Fast Python package manager (use `uv sync`, `uv add`, `uv run`)
- **Python >= 3.11** required
- Entry point: `uv run start` or `uv run python -m app.main`

## Core Stack
- **Aiogram 3.13.0** - Telegram bot with FSM (async/await throughout)
- **OpenRouter + OpenAI client** - LLM API gateway
  - Primary: `x-ai/grok-4-fast` (, cost-effective)
  - Secondary: `mistralai/mistral-nemo` (smart, for creative tasks, higher in price)
- **Pydantic Settings** - Type-safe config in `app/config.py`
- **Supabase (PostgreSQL + pgvector)** - Database with vector search (Sprint 3+)

## Required Environment Variables
```bash
TELEGRAM_BOT_TOKEN    # From @BotFather
OPENROUTER_API_KEY    # From openrouter.ai
SUPABASE_URL          # Supabase project URL
SUPABASE_KEY          # Supabase anon/service key
LLM_MODEL             # Default: x-ai/grok-4-fast
```

## Common Commands
```bash
# Setup
uv sync                              # Install dependencies
cp .env.example .env                 # Create config (then edit)

# Run
uv run start                         # Start bot

# Test
uv run pytest                        # All tests
uv run pytest tests/test_file.py     # Specific test
uv run pytest -v                     # Verbose

# Code quality
uv run black app/ tests/             # Format
uv run ruff check app/ tests/        # Lint

# Dependencies
uv add package-name                  # Add runtime dep
uv add --dev package-name            # Add dev dep
```

## Key Conventions
- All async (handlers, agents, DB calls)
- Type hints required on all functions
- Use `logging` module, never `print()`
- Pydantic models for structured data validation
- Configuration centralized in `app/config/` modules
