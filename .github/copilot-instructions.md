# AI Coding Agent Instructions - RPGate Telegram Bot

## Project Overview

AI-powered Game Master Telegram bot using multi-agent architecture. Russian UI for players, English codebase. **Sprint 3 Complete** - Full memory system with RAG, database persistence, and all 5 agents operational.

## Core Architecture Principles

### Multi-Agent GM System (✅ Fully Implemented)

The bot uses **specialized agents** mimicking a real Game Master's mental processes:

1. **Memory Manager** - RAG-based context retrieval from episodic memory (pgvector)
2. **Rules Arbiter** - Intent detection + dice mechanics resolution (d20 system)
3. **Narrative Director** - Vivid story descriptions + combat state tracking
4. **World State Agent** - Game state persistence to PostgreSQL
5. **Response Synthesizer** - Final message formatting with Markdown + emojis

**Execution Order (Fixed):**
```
Memory Manager → [Rules Arbiter + Narrative Director (parallel)] → World State → Response Synthesizer → Save Memory
```

### Tech Stack

- **Bot Framework:** Aiogram 3.13.0 with FSM (async/await throughout)
- **Package Manager:** UV (fast Python package manager)
- **LLM Provider:** OpenRouter (primary model: `x-ai/grok-4-fast`)
- **Database:** Supabase (PostgreSQL + pgvector for embeddings)
- **Embeddings:** OpenRouter (`qwen/qwen3-embedding-4b` (1536 dimensions))
- **Agent Orchestration:** Custom orchestrator in `app/agents/orchestrator.py` (no CrewAI)

## Critical File Locations

### Configuration & Entry Points
- `app/config.py` - Pydantic settings from `.env` (TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY, SUPABASE_URL, SUPABASE_KEY)
- `app/main.py` - Bot entry point, dispatcher setup, polling loop
- `pyproject.toml` - Project metadata, scripts (`uv run start`)
- `.github/instructions/` - **Modular instruction files** (product, structure, tech)

### Game Mechanics
- `app/game/character.py` - CharacterSheet Pydantic model (Warrior, Ranger, Mage, Rogue)
- `app/game/dice.py` - DiceRoller system (d4-d100, advantage/disadvantage)
- `app/game/rules.py` - RulesEngine (attack resolution, skill checks, action detection)

### Agent System (All Agents Implemented)
- `app/agents/base.py` - BaseAgent abstract class
- `app/agents/memory_manager.py` - RAG memory retrieval (embeddings + vector search)
- `app/agents/rules_arbiter.py` - Intent analysis + mechanics resolution
- `app/agents/narrative_director.py` - Story generation + combat state extraction
- `app/agents/world_state.py` - Game state persistence to PostgreSQL
- `app/agents/response_synthesizer.py` - Final response formatting
- `app/agents/orchestrator.py` - **Coordinates all agents** (main workflow)

### Bot Layer
- `app/bot/handlers.py` - Telegram message handlers, FSM integration, **DB-first character loading**
- `app/bot/states.py` - FSM states: `idle`, `in_conversation`, `character_creation`
- `app/llm/client.py` - OpenRouter API wrapper (OpenAI-compatible)

### Database & Memory (Sprint 3)
- `app/db/supabase.py` - Supabase client singleton
- `app/db/characters.py` - Character CRUD (create, get, update, delete)
- `app/db/sessions.py` - Session management (create, end, update stats)
- `app/db/models.py` - Pydantic models for DB entities
- `app/db/migrations/` - SQL migrations (001_initial_schema.sql, 002_switch_to_halfvec.sql)
- `app/memory/episodic.py` - Episodic memory manager (RAG pipeline)
- `app/memory/embeddings.py` - OpenAI embeddings wrapper

### Configuration System (Centralized)
- `app/config/prompts.py` - **ALL Russian text goes here** (RulesArbiterPrompts, NarrativeDirectorPrompts, UIPrompts, etc.)
- `app/config/models.py` - Per-agent LLM configs (model, temperature, max_tokens)
- `app/config/schemas.py` - Pydantic schemas for structured data

### Documentation
- `docs/architecture/STRATEGIC_PLAN.md` - Architectural "bible" (decisions, roadmap)
- `docs/development/SPRINT3_PROGRESS.md` - Consolidated Sprint 3 (integration + summary)
- `docs/architecture/API_CONTRACTS.md` - Agent input/output JSON schemas

## Development Workflows

### Running the Bot

```bash
# Standard way
uv run python -m app.main

# Shortcut (defined in pyproject.toml)
uv run start
```

### Testing

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_dice.py -v

# With coverage
uv run pytest tests/ --cov=app --cov-report=html
```

### Database Operations

```bash
# Test database connection
uv run python scripts/test_db_connection.py

# Apply migration
uv run python scripts/apply_migration.py migrations/001_initial_schema.sql

# Check database tables (via Supabase dashboard or psql)
# Tables: characters, game_sessions, episodic_memories, world_state
```

### Adding Dependencies

```bash
# Add runtime dependency
uv add package-name

# Add dev dependency
uv add --dev package-name

# Never use pip directly - UV handles everything
```

## Project-Specific Conventions

### Localization Rules (CRITICAL)

- **Code & Documentation:** English (functions, variables, comments, docstrings)
- **User-Facing Text:** Russian (bot messages, prompts, UI elements)
- **Model Prompts:** Russian (centralized in `app/config/prompts.py` when implemented)

**Example:**
```python
# ✅ CORRECT
async def handle_conversation(message: Message, state: FSMContext):
    """Handle user conversation in active state."""  # English docstring
    await message.answer("🎲 Добро пожаловать, искатель приключений!")  # Russian UI

# ❌ WRONG
async def обработать_диалог(message: Message, state: FSMContext):
    await message.answer("Welcome, adventurer!")
```

### FSM State Management Pattern

Character data is **loaded from database first**, with FSM fallback for backward compatibility:

```python
# DB-first approach (Sprint 3)
from app.db.characters import get_character_by_telegram_id

character = await get_character_by_telegram_id(telegram_user_id)
if not character:
    # FSM fallback
    data = await state.get_data()
    character_data = data.get("character")
    if character_data:
        character = CharacterSheet(**character_data)

# Update character in DB
from app.db.characters import update_character
await update_character(character)
```

**State in FSM context:** Conversation history, temporary game flags (combat_ended, etc.)
**State in PostgreSQL:** Character sheets, game sessions, episodic memories, world state

### Agent Input/Output Contracts

All agents follow strict JSON schemas (see `docs/architecture/API_CONTRACTS.md`). Example:

```python
# Rules Arbiter Output
{
    "action_type": "attack" | "skill_check" | "spell" | "other",
    "mechanics_result": {...},  # Dice rolls, damage, etc.
    "success": bool,
    "narrative_hints": ["critical_hit", "fumble", ...]
}
```

**Always validate** agent outputs match contracts. Use Pydantic models where possible.

### Response Formatting

Final messages use **Markdown + emojis** for better UX:

```markdown
🎲 **Атака** [🎲 18+3 = 21] ✅ Попадание!
💔 **Урон:** 10 HP

[Narrative description in Russian]

❤️ **HP:** 15/20
📍 **Локация:** goblin_cave
```

**Emoji map:** `🎲` actions, `✅/❌` results, `💥` critical, `❤️` health, `📍` location

### Error Handling for LLM APIs

```python
try:
    response = await llm_client.get_completion(...)
except Exception as e:
    logger.error(f"LLM API Error: {e}", exc_info=True)
    
    if "rate_limit" in str(e).lower() or "429" in str(e):
        return "⏳ Слишком много запросов. Подожди и попробуй снова."
    
    return "❌ Извини, произошла ошибка. Попробуй позже."
```

## Common Pitfalls

### DO NOT use pip or python directly
```bash
# ❌ WRONG
pip install package
python app/main.py

# ✅ CORRECT
uv add package
uv run python -m app.main
```

### DO NOT hardcode prompts in agent code
All prompts are centralized in `app/config/prompts.py`. Russian text for players, English for system prompts.

Example:
```python
from app.config.prompts import RulesArbiterPrompts

# Use centralized prompts
system_prompt = RulesArbiterPrompts.INTENT_ANALYSIS_SYSTEM
user_prompt = RulesArbiterPrompts.INTENT_ANALYSIS_USER.format(
    context=context,
    user_action=user_action
)
```

### DO NOT mix languages
Keep code/comments in English, user text in Russian. Never translate code identifiers.

### DO NOT skip async/await
All agent methods and handlers are async:
```python
# ✅ CORRECT
async def execute(self, context: dict) -> dict:
    result = await llm_client.get_completion(...)
    
# ❌ WRONG
def execute(self, context: dict) -> dict:
    result = llm_client.get_completion(...)  # Won't work
```

## Integration Points

### Aiogram → Agents Flow

```
User message → handlers.py → orchestrator.py → [Rules, Narrative, Synthesizer] → Final message
```

**Key file:** `app/bot/handlers.py` - `handle_conversation()` function integrates agents.

### LLM Model Selection per Agent

Different agents use different models/temperatures (configured in `app/config/models.py`):
- **Rules Arbiter:** `x-ai/grok-4-fast`, temp 0.1 (fast, deterministic)
- **Narrative Director:** `x-ai/grok-4-fast`, temp 0.8 (creative)
- **Response Synthesizer:** `x-ai/grok-4-fast`, temp 0.3 (balanced)

Example:
```python
from app.config.models import AGENT_CONFIGS

# Access agent-specific config
config = AGENT_CONFIGS.RULES_ARBITER
response = await llm_client.get_completion(
    messages=[...],
    temperature=config.temperature,
    max_tokens=config.max_tokens
)
```

### OpenRouter Client Usage

```python
from app.llm.client import llm_client

# Always use async
response = await llm_client.get_completion(
    messages=[{"role": "system", "content": "..."}, ...],
    temperature=0.7,
    max_tokens=500
)
```

Returns plain string. Error handling is built-in (rate limits, API errors).

## Sprint Status & Next Steps

**Current:** Sprint 3 Complete - Multi-agent system with database persistence and memory

**Completed (Sprint 1):**
- ✅ Basic bot with LLM chat
- ✅ FSM state management
- ✅ Conversation history (short-term)
- ✅ Basic commands (/start, /help, /reset, /ping)

**Completed (Sprint 2):**
- ✅ Game mechanics (dice, character sheet, rules engine)
- ✅ Multi-agent system (5 core agents)
- ✅ Character creation flow
- ✅ Beautiful formatted responses
- ✅ Intent detection system
- ✅ Combat state tracking

**Completed (Sprint 3):**
- ✅ Long-term memory with RAG (Supabase + pgvector)
- ✅ Memory Manager & World State agents
- ✅ Database persistence (characters, sessions, memories)
- ✅ Episodic memory with embeddings
- ✅ Full multi-session continuity

**Next (Sprint 4):**
- ⏳ Connection pooling (asyncpg)
- ⏳ Retry logic and caching
- ⏳ Webhook support (FastAPI)
- ⏳ Advanced RAG (re-ranking, hybrid search)
- ⏳ Production deployment

## When You're Stuck

1. **Architectural questions:** Read `docs/architecture/STRATEGIC_PLAN.md` for the "why"
2. **Implementation details:** Use `docs/development/SPRINT3_PROGRESS.md` (integration + summary consolidated)
3. **Data formats:** Consult `docs/architecture/API_CONTRACTS.md` for JSON schemas
4. **Code examples:** Look at existing agents in `app/agents/` or handlers in `app/bot/`
5. **Setup issues:** Run `uv run python scripts/check_week3_setup.py` to diagnose
6. **Database schema:** See `app/db/migrations/001_initial_schema.sql`

## Quick Reference Commands

```bash
# Start bot
uv run start

# Run tests
uv run pytest tests/ -v

# Test DB connection
uv run python scripts/test_db_connection.py

# Add dependency
uv add package-name

# Update dependencies
uv sync
```

---

**Remember:** This is a multi-agent AI GM system with full database persistence, not a simple chatbot. Each component has a specific role mimicking real Game Master cognitive processes. Characters and game state persist across sessions via PostgreSQL + pgvector.
