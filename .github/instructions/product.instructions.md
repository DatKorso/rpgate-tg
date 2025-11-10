---
applyTo: '**'
---
# Product Context

## RPGate - AI Game Master Bot

AI-powered Telegram bot that runs D&D-style RPG sessions. Players interact in natural language while the bot handles storytelling, dice mechanics, combat, and character management.

## Development Status

**Sprint 3 (Current):** Memory system with RAG and database persistence
- Sprint 1: ✅ Basic bot with LLM integration
- Sprint 2: ✅ Multi-agent system with game mechanics

## Core Product Rules

### Localization Requirements
- **All user-facing text MUST be in Russian** - bot messages, prompts, UI text
- **Code, comments, and docs MUST be in English**
- **Prompts are centralized** in `app/config/prompts.py` - never hardcode Russian text elsewhere
- When adding new features, always add Russian text to `prompts.py` first

### Game Mechanics
- **D&D-inspired d20 system** - use existing `DiceRoller` and `RulesEngine` classes
- **Character classes:** Warrior, Ranger, Mage, Rogue (defined in `character.py`)
- **Combat resolution:** Attack rolls vs AC, damage rolls, HP tracking
- **Skill checks:** d20 + modifiers vs DC
- Never invent new mechanics - extend existing systems in `app/game/`

### Multi-Agent Architecture
**Agent execution order is fixed:** Rules Arbiter → Narrative Director → Response Synthesizer

- **Rules Arbiter** - Detects player intent, resolves mechanics, updates game state
- **Narrative Director** - Generates story descriptions based on rules output
- **Response Synthesizer** - Formats final message with Markdown and emojis
- **Orchestrator** - Coordinates the workflow, never generates content itself

When modifying agents:
- Each agent has specific responsibilities - don't blur boundaries
- Agents communicate via structured dicts (see `docs/architecture/API_CONTRACTS.md`)
- All agents inherit from `BaseAgent` and implement `execute()`
- Agent configs (model, temperature) are in `app/config/models.py`

### State Management
- **FSM states:** `idle`, `in_conversation`, `character_creation` (defined in `app/bot/states.py`)
- **Game state** stored in FSM context as dict with keys: `in_combat`, `enemies`, `location`, `combat_ended`, `enemy_attacks`
- **Character state** serialized as `CharacterSheet` object in FSM context
- Never store state outside FSM context in MVP (database persistence is Sprint 3+)

### LLM Integration
- **Primary model:** `x-ai/grok-4-fast` (fast, cost-effective)
- **Alternative:** `x-ai/grok-2` (higher quality narrative)
- **Provider:** OpenRouter via `app/llm/client.py`
- Model selection per agent configured in `app/config/models.py`
- Always use structured output when possible (JSON mode)

### Response Formatting
- Use Telegram Markdown formatting (bold, italic, code blocks)
- Include emojis for visual appeal (⚔️ 🎲 💀 🏹 etc.)
- Combat results show: roll details, damage, HP changes
- Keep responses concise but immersive

## Feature Development Guidelines

### Adding New Game Mechanics
1. Implement logic in `app/game/rules.py` (RulesEngine)
2. Update `app/game/character.py` if character data changes
3. Modify Rules Arbiter to detect and resolve new actions
4. Add tests in `tests/test_rules.py`

### Adding New Agent Capabilities
1. Update agent's `execute()` method in `app/agents/`
2. Update API contract in `docs/architecture/API_CONTRACTS.md`
3. Adjust downstream agents if output format changes
4. Add agent-specific tests
5. Document changes in `docs/development/CHANGELOG.md`

### Adding New Bot Commands
1. Add handler in `app/bot/handlers.py`
2. Add Russian text to `app/config/prompts.py`
3. Register handler in `main.py` dispatcher
4. Update FSM states if needed

### Memory System (Sprint 3+)
- **Episodic memory:** Conversation history with embeddings (pgvector)
- **Semantic memory:** World lore and facts
- **RAG pipeline:** Retrieve relevant memories before agent execution
- Database schema in `app/db/migrations/`
- Supabase client in `app/db/supabase.py`

## Quality Standards

- **Type hints required** - all functions and methods must have type annotations
- **Async/await throughout** - all bot handlers and agent methods are async
- **Pydantic for validation** - use Pydantic models for structured data
- **Error handling** - graceful failures with Russian error messages to users
- **Logging** - use Python logging module, not print statements
- **Tests** - add tests for new game mechanics and agent logic