---
applyTo: '**'
---
# Code Structure & Conventions

## Module Organization

### `app/agents/` - Multi-Agent System
Fixed execution order: **Rules Arbiter → Narrative Director → Response Synthesizer**

- All agents inherit from `BaseAgent` and implement `async def execute(context: dict[str, Any]) -> dict[str, Any]`
- `orchestrator.py` coordinates workflow, never generates content
- Agent configs (model, temperature) in `app/config/models.py`
- Agent communication contracts in `docs/API_CONTRACTS.md`

### `app/bot/` - Telegram Layer
- `handlers.py` - Command/message handlers (all async)
- `states.py` - FSM states: `idle`, `in_conversation`, `character_creation`

### `app/config/` - Configuration
- `prompts.py` - **ALL Russian text goes here** (never hardcode Russian elsewhere)
- `models.py` - Per-agent LLM configurations
- `schemas.py` - Pydantic schemas for structured data

### `app/game/` - Game Mechanics
- `character.py` - CharacterSheet (Warrior, Ranger, Mage, Rogue)
- `dice.py` - DiceRoller (d4, d6, d8, d10, d12, d20, d100)
- `rules.py` - RulesEngine (attack resolution, skill checks)

### `app/db/` - Database (Sprint 3+)
- `models.py` - Pydantic/SQLAlchemy models
- `supabase.py` - Supabase client
- `migrations/` - SQL migration files

### `app/memory/` - Memory System (Sprint 3+)
- `episodic.py` - Conversation history with embeddings
- `embeddings.py` - Embedding generation
- RAG pipeline for context retrieval

## Code Style Rules

### Language
- Code, comments, variable names: **English only**
- User-facing text: **Russian only** (centralized in `app/config/prompts.py`)
- When adding features, add Russian text to `prompts.py` first

### Type Hints (Required)
```python
async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
    character: CharacterSheet = context["character"]
    return {"result": "success"}
```

### Async/Await (Required)
All bot handlers and agent methods must be async

### Imports
Use absolute imports from `app`:
```python
from app.agents.base import BaseAgent
from app.game.character import CharacterSheet
from app.config.prompts import PROMPTS
```

### Logging
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Message")  # Never use print()
```

### Error Handling
Catch exceptions gracefully, return Russian error messages to users

## State Management

### FSM Context Storage
- **Game state**: `{"in_combat": bool, "enemies": list[str], "location": str, "combat_ended": bool, "enemy_attacks": list[dict]}`
- **Character state**: CharacterSheet object serialized to FSM context
- Never store state outside FSM in MVP (database is Sprint 3+)

## Testing Conventions

```python
import pytest

@pytest.mark.asyncio
async def test_agent_execution():
    agent = SomeAgent()
    result = await agent.execute(context)
    assert result["key"] == expected_value
```

Tests in `tests/` mirror `app/` structure: `test_character.py`, `test_dice.py`, `test_rules.py`, `test_*_agent.py`

## Adding New Features

### New Game Mechanics
1. Implement in `app/game/rules.py` (RulesEngine)
2. Update `app/game/character.py` if character data changes
3. Modify Rules Arbiter to detect/resolve new actions
4. Add tests in `tests/test_rules.py`

### New Agent Capabilities
1. Update agent's `execute()` in `app/agents/`
2. Update API contract in `docs/API_CONTRACTS.md`
3. Adjust downstream agents if output format changes
4. Add agent-specific tests

### New Bot Commands
1. Add handler in `app/bot/handlers.py`
2. Add Russian text to `app/config/prompts.py`
3. Register handler in `main.py` dispatcher
4. Update FSM states if needed

## Response Formatting

Use Telegram Markdown with emojis (⚔️ 🎲 💀 🏹). Combat results show roll details, damage, HP changes. Keep responses concise but immersive.
