# Project Structure & Organization

## Directory Layout

```
rpgate-tg/
├── app/                      # Main application code
│   ├── agents/              # Multi-agent system
│   ├── bot/                 # Telegram bot layer
│   ├── config/              # Configuration & prompts
│   ├── game/                # Game mechanics
│   ├── llm/                 # LLM client
│   ├── config.py            # Settings loader
│   └── main.py              # Entry point
├── tests/                   # Test suite
├── docs/                    # Documentation
├── .env                     # Environment variables (not in git)
└── pyproject.toml          # Project configuration
```

## Module Organization

### `app/agents/` - Multi-Agent System
Core agents that work together to create the GM experience:
- `base.py` - BaseAgent abstract class for all agents
- `orchestrator.py` - Coordinates agent workflow
- `rules_arbiter.py` - Handles game mechanics and dice rolls
- `narrative_director.py` - Generates story descriptions
- `response_synthesizer.py` - Assembles final formatted responses

**Agent workflow:** Rules Arbiter → Narrative Director → Response Synthesizer

### `app/bot/` - Telegram Bot Layer
Handles Telegram-specific logic:
- `handlers.py` - Command and message handlers
- `states.py` - FSM state definitions (idle, in_conversation, character_creation)

### `app/config/` - Configuration System
Centralized configuration for maintainability:
- `models.py` - Per-agent LLM model configurations (temperature, max_tokens)
- `prompts.py` - All prompts in Russian (UI text, system prompts, templates)
- `schemas.py` - Pydantic schemas for structured data

### `app/game/` - Game Mechanics
D&D-inspired game systems:
- `character.py` - CharacterSheet model with stats, HP, inventory
- `dice.py` - DiceRoller for d4, d6, d8, d10, d12, d20, d100
- `rules.py` - RulesEngine for attack resolution, skill checks

### `app/llm/` - LLM Integration
- `client.py` - OpenRouter API client wrapper

### `app/config.py` - Settings
Loads environment variables using Pydantic Settings

### `app/main.py` - Entry Point
Initializes bot, dispatcher, and starts polling

## Code Conventions

### Language Usage
- **Code & comments:** English
- **User-facing text:** Russian (in `app/config/prompts.py`)
- **Documentation:** English (with Russian for PM-facing strategic docs)

### Type Hints
Use type hints throughout for better IDE support and AI code generation:
```python
def resolve_attack(attacker: CharacterSheet, target_ac: int) -> dict:
    ...
```

### Async/Await
All bot handlers and agent methods are async:
```python
async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
    ...
```

### Pydantic Models
Use Pydantic for data validation and serialization:
- CharacterSheet
- ModelConfig
- Settings

### Logging
Use Python's logging module:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Message")
```

### Error Handling
Graceful error handling with user-friendly messages in Russian

## Testing Structure

### `tests/` Directory
- `test_character.py` - CharacterSheet model tests
- `test_dice.py` - Dice rolling tests
- `test_rules.py` - Rules engine tests
- `test_*_agent.py` - Agent-specific tests
- Use `pytest` with `pytest-asyncio` for async tests

### Test Conventions
```python
import pytest

@pytest.mark.asyncio
async def test_agent_execution():
    agent = SomeAgent()
    result = await agent.execute(context)
    assert result["key"] == expected_value
```

## Documentation Structure

### `docs/` Directory
- `STRATEGIC_PLAN.md` - Overall architecture and roadmap
- `SPRINT*_SPEC.md` - Sprint-specific specifications
- `SPRINT*_CHECKLIST.md` - Task checklists
- `API_CONTRACTS.md` - Agent communication formats
- `README.md` - Documentation index

## Configuration Files

### `.env` (not in git)
Environment-specific secrets and configuration

### `.env.example`
Template for required environment variables

### `pyproject.toml`
Python project metadata, dependencies, and tool configuration

### `uv.lock`
Locked dependency versions (auto-generated)

## Import Conventions

Use absolute imports from `app`:
```python
from app.agents.base import BaseAgent
from app.game.character import CharacterSheet
from app.config.prompts import PROMPTS
```

## State Management

### FSM States (Aiogram)
Defined in `app/bot/states.py`:
- `idle` - No active conversation
- `in_conversation` - Active game session
- `character_creation` - Creating new character

### Game State
Stored in FSM context as dict:
```python
{
    "in_combat": bool,
    "enemies": list[str],
    "location": str,
    "combat_ended": bool,
    "enemy_attacks": list[dict]
}
```

### Character State
CharacterSheet object serialized to FSM context

## Future Structure (Sprint 3+)

### `app/memory/` - Memory System
- `episodic.py` - Episodic memory manager
- `semantic.py` - Semantic memory (lore)
- `embeddings.py` - Embedding generation
- `retrieval.py` - RAG pipeline

### `app/db/` - Database Layer
- `models.py` - SQLAlchemy/Pydantic models
- `supabase.py` - Supabase client
- `migrations/` - Database migrations
