# GM Telegram Bot - MVP Sprint 1

AI-powered Game Master Telegram bot using Grok-4-fast via OpenRouter.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Create `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your API keys:
   - `TELEGRAM_BOT_TOKEN` - Get from [@BotFather](https://t.me/botfather)
   - `OPENROUTER_API_KEY` - Get from [OpenRouter](https://openrouter.ai/keys)
   
   See [SETUP.md](SETUP.md) for detailed instructions.

3. Check your setup (optional but recommended):
   ```bash
   uv run python check_setup.py
   ```

4. Run the bot:
   ```bash
   uv run python -m app.main
   ```
   
   Or using the shortcut:
   ```bash
   uv run start
   ```

## Architecture

- **FastAPI**: Web framework (reserved for Sprint 4 webhooks)
- **Aiogram 3.x**: Telegram Bot framework with FSM
- **OpenRouter**: LLM API gateway for Grok access
- **UV**: Fast Python package manager

## 🌍 Localization

- **UI/UX:** Russian (все сообщения бота, промпты для игроков)
- **Code:** English (код, документация, комментарии)
- **Prompts:** Centralized in `app/config/prompts.py` (Russian)
- **Model Config:** Centralized in `app/config/models.py` (per-agent settings)

## Features

### Sprint 1 ✅ (Foundation)
- ✅ Basic conversation with AI Game Master
- ✅ FSM state management (idle/in_conversation)
- ✅ Conversation history (last 10 messages)
- ✅ Commands: /start, /help, /reset, /ping
- ✅ Typing indicator для улучшения UX
- ✅ Error handling и logging
- ✅ Rate limit обработка от OpenRouter

### Sprint 2 ✅ (Multi-Agent System)
- ✅ **Multi-agent architecture** (Rules Arbiter, Narrative Director, Response Synthesizer)
- ✅ **Game mechanics** (d20 system, dice rolling, combat resolution, skill checks)
- ✅ **Character system** (creation flow, character sheet, HP/stats tracking)
- ✅ **LLM-based intent detection** (automatic action type detection)
- ✅ **Game state management** (combat tracking, location, enemies)
- ✅ **Inline keyboards** for better UX (character creation, class selection)
- ✅ **Formatted responses** with Markdown, emojis, and structured output
- ✅ **Centralized configuration** (prompts in `prompts.py`, models in `models.py`)
- ✅ **Character classes** (Warrior, Ranger, Mage, Rogue with different stats)

### Sprint 3 🔄 (Current - Memory System)
- 🔄 **Week 1**: Database infrastructure setup
  - ✅ Database schema designed (PostgreSQL + pgvector)
  - ✅ Migration scripts created
  - ✅ Pydantic models for DB entities
  - ✅ Supabase client wrapper
  - ⏳ Supabase project setup (manual step)
  - ⏳ Dependencies installation
  - ⏳ Migration application
- ⏳ **Week 2**: Memory system & agents
  - ⏳ Embeddings service (OpenAI)
  - ⏳ Episodic memory manager (vector search)
  - ⏳ Memory Manager agent
  - ⏳ World State agent
  - ⏳ CrewAI integration (optional)
- ⏳ **Week 3**: Integration & polish
  - ⏳ Character persistence
  - ⏳ Session management
  - ⏳ Bot handlers update
  - ⏳ Testing & documentation

**Getting Started with Sprint 3:**
See [docs/SPRINT3_SETUP_GUIDE.md](docs/SPRINT3_SETUP_GUIDE.md) for Supabase setup instructions.

## 📚 Documentation

Full documentation is available in the `docs/` folder:

- **[Strategic Plan](docs/STRATEGIC_PLAN.md)** — Architecture & roadmap (start here! 🚀)
- **[Sprint 2 Spec](docs/SPRINT2_SPEC.md)** — Current sprint tasks
- **[API Contracts](docs/API_CONTRACTS.md)** — Agent communication formats
- **[Documentation Index](docs/README.md)** — Full documentation map

## 🗺️ Roadmap

### ✅ Sprint 1: Foundation (Completed)
- Basic Telegram bot with LLM integration
- FSM state management
- Conversation history (short-term memory)
- Basic commands and error handling

### ✅ Sprint 2: Multi-Agent System (Completed)
**Duration:** 2-3 weeks

**Completed Features:**
- ✅ Multi-agent GM system (Rules Arbiter, Narrative Director, Response Synthesizer)
- ✅ LLM-based intent detection (automatic combat/skill detection)
- ✅ Game state management (combat tracking, location, enemies)
- ✅ Centralized prompts system (all prompts in `app/config/prompts.py`)
- ✅ Per-agent model configuration (temperature, max_tokens)
- ✅ Game mechanics (d20 system, combat, skill checks)
- ✅ Character creation with classes (Warrior, Ranger, Mage, Rogue)
- ✅ Character sheet tracking (HP, stats, inventory)
- ✅ Beautiful formatted responses with emojis and Markdown

**Documentation:** 
- [docs/SPRINT2_SPEC.md](docs/SPRINT2_SPEC.md) — Main specification
- [docs/SPRINT2_IMPROVEMENTS.md](docs/SPRINT2_IMPROVEMENTS.md) — Intent detection & combat state
- [docs/SPRINT2_PROMPTS_CONFIG.md](docs/SPRINT2_PROMPTS_CONFIG.md) — Prompts & config system

### 🔄 Sprint 3: Memory System + CrewAI (Current)
**Duration:** 2-3 weeks  
**Status:** Week 1 - Database Infrastructure (In Progress)

**Goals:**
- 🎯 Long-term memory with RAG pipeline
- 🎯 Supabase PostgreSQL + pgvector for vector search
- 🎯 Memory Manager agent (retrieves relevant context)
- 🎯 World State agent (persists game state)
- 🎯 Episodic & semantic memory systems
- 🎯 Multi-session continuity (bot remembers past sessions)
- 🎯 CrewAI integration for production-grade orchestration
- 🎯 Character persistence in database
- 🎯 Session management with LLM-generated summaries

**Week 1 Progress:**
- ✅ Database schema designed (5 tables with vector embeddings)
- ✅ Migration scripts created
- ✅ Pydantic models for all DB entities
- ✅ Supabase client wrapper with lazy initialization
- ✅ Configuration updated (Supabase + OpenAI settings)
- ⏳ **Next**: User needs to set up Supabase project and install dependencies

**Documentation:**
- [docs/SPRINT3_SPEC.md](docs/SPRINT3_SPEC.md) — Full specification with code examples
- [docs/SPRINT3_CHECKLIST.md](docs/SPRINT3_CHECKLIST.md) — Detailed task checklist
- [docs/SPRINT3_SETUP_GUIDE.md](docs/SPRINT3_SETUP_GUIDE.md) — Supabase setup instructions
- [docs/SPRINT3_PROGRESS.md](docs/SPRINT3_PROGRESS.md) — Current progress report

### ⏳ Sprint 4: Production Ready (Planned)
**Duration:** 1-2 weeks

**Goals:**
- Production-optimized CrewAI workflows (parallel execution)
- Redis for FSM persistence
- Webhooks instead of polling
- Deploy to Railway/Render
- Monitoring & cost tracking
- Load testing & optimization

**See:** [docs/STRATEGIC_PLAN.md](docs/STRATEGIC_PLAN.md) for detailed roadmap
