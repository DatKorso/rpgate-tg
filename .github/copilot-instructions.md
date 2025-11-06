# AI Coding Agent Instructions - RPGate Telegram Bot

## Project Overview

AI-powered Game Master Telegram bot using multi-agent architecture. Russian UI for players, English codebase. Currently in Sprint 2 transitioning from basic LLM chat to sophisticated multi-agent GM system with game mechanics.

## Core Architecture Principles

### Multi-Agent GM System (Sprint 2+)

The bot uses **specialized agents** mimicking a real Game Master's mental processes:

1. **Rules Arbiter** - Resolves dice rolls, combat, skill checks (deterministic, low temp)
2. **Narrative Director** - Generates vivid story descriptions (creative, high temp)
3. **Response Synthesizer** - Combines outputs into formatted player message
4. **Memory Manager** (Sprint 3) - RAG-based long-term memory retrieval
5. **World State** (Sprint 3) - Tracks game state changes

**Orchestration:** Simple sequential execution in Sprint 2. Migrating to **CrewAI** in Sprint 3 for production workflows.

### Tech Stack

- **Bot Framework:** Aiogram 3.x with FSM (finite state machine)
- **Package Manager:** UV (faster than pip, already configured)
- **LLM Provider:** OpenRouter (unified API for Grok, GPT, Claude)
- **Database:** PostgreSQL + pgvector via Supabase (Sprint 3)
- **Agent Orchestration:** CrewAI (Sprint 3+)

## Critical File Locations

### Configuration & Entry Points
- `app/config.py` - Pydantic settings from `.env` (TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY)
- `app/main.py` - Bot entry point, dispatcher setup, polling loop
- `pyproject.toml` - Project metadata, scripts (`start` command)

### Game Mechanics (Sprint 2)
- `app/game/character.py` - CharacterSheet Pydantic model with D&D-style stats
- `app/game/dice.py` - DiceRoller system (d4-d100, advantage/disadvantage)
- `app/game/rules.py` - RulesEngine for attack resolution, skill checks, action type detection

### Agent System (Sprint 2)
- `app/agents/base.py` - BaseAgent abstract class
- `app/agents/rules_arbiter.py` - Mechanics resolution agent
- `app/agents/narrative_director.py` - Story generation agent
- `app/agents/response_synthesizer.py` - Final response formatting
- `app/agents/orchestrator.py` - Agent workflow coordination

### Bot Layer
- `app/bot/handlers.py` - Telegram message handlers, FSM integration
- `app/bot/states.py` - ConversationState FSM (idle, in_conversation, creating_character)
- `app/llm/client.py` - OpenRouter API wrapper (OpenAI-compatible)

### Documentation (READ THESE FIRST)
- `docs/STRATEGIC_PLAN.md` - **Architectural "bible"**, explains all decisions and roadmap
- `docs/SPRINT2_SPEC.md` - Detailed Sprint 2 tasks with code examples
- `docs/API_CONTRACTS.md` - Agent input/output JSON schemas

## Development Workflows

### Running the Bot

```bash
# Standard way
uv run python -m app.main

# Shortcut (defined in pyproject.toml)
uv run start

# Check setup before running
uv run python check_setup.py
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

Character data and conversation history are stored in FSM context, not database (Sprint 1-2):

```python
# Get character from state
data = await state.get_data()
character_data = data.get("character")
if character_data:
    character = CharacterSheet(**character_data)

# Update character
await state.update_data(character=character.model_dump_for_storage())
```

**In Sprint 3:** Migrate to PostgreSQL for persistence across sessions.

### Agent Input/Output Contracts

All agents follow strict JSON schemas (see `docs/API_CONTRACTS.md`). Example:

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
**Sprint 2 TODO:** Centralize all prompts in `app/config/prompts.py`. Until implemented, prompts are inline but should be easily extractable.

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

Different agents use different models/temperatures:
- **Rules Arbiter:** `gpt-4o-mini`, temp 0.1 (cheap, deterministic)
- **Narrative Director:** `grok-2`, temp 0.8 (quality, creative)
- **Response Synthesizer:** `gpt-4o`, temp 0.3 (best quality)

**Configured in:** Agent `__init__()` methods. Will move to `app/config/models.py` (Sprint 2 TODO).

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

**Current:** Sprint 2 in progress - Multi-agent system foundation

**Completed (Sprint 1):**
- ✅ Basic bot with LLM chat
- ✅ FSM state management
- ✅ Conversation history (short-term)
- ✅ Basic commands (/start, /help, /reset, /ping)

**In Progress (Sprint 2):**
- 🔄 Game mechanics (dice, character sheet, rules engine)
- 🔄 Multi-agent system (3 core agents)
- 🔄 Character creation flow
- 🔄 Beautiful formatted responses

**Next (Sprint 3):**
- ⏳ Long-term memory with RAG (Supabase + pgvector)
- ⏳ CrewAI integration for orchestration
- ⏳ Memory Manager & World State agents

## When You're Stuck

1. **Architectural questions:** Read `docs/STRATEGIC_PLAN.md` for the "why"
2. **Implementation details:** Check `docs/SPRINT2_SPEC.md` for step-by-step
3. **Data formats:** Consult `docs/API_CONTRACTS.md` for JSON schemas
4. **Code examples:** Look at existing agents in `app/agents/` or handlers in `app/bot/`
5. **Setup issues:** Run `uv run python check_setup.py` to diagnose

## Quick Reference Commands

```bash
# Start bot
uv run start

# Run tests
uv run pytest tests/ -v

# Check setup
uv run python check_setup.py

# Add dependency
uv add package-name

# Update dependencies
uv sync
```

---

**Remember:** This is a multi-agent AI GM system, not a simple chatbot. Each component has a specific role mimicking real Game Master cognitive processes. Read the strategic plan for deep architecture understanding.
