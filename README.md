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

## Features (Sprint 1)

- ✅ Basic conversation with AI Game Master
- ✅ FSM state management (idle/in_conversation)
- ✅ Conversation history (last 10 messages)
- ✅ Commands: /start, /help, /reset, /ping
- ✅ Typing indicator для улучшения UX
- ✅ Error handling и logging
- ✅ Rate limit обработка от OpenRouter

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

### 🔄 Sprint 2: Multi-Agent System (In Progress)
**Weeks:** 2-3

**Goals:**
- Multi-agent GM system (Rules Arbiter, Narrative Director, Response Synthesizer)
- **LLM-based intent detection** (automatic combat/skill detection)
- **Game state management** (combat tracking, location, enemies)
- **Centralized prompts system** (all prompts in `app/config/prompts.py`)
- **Per-agent model configuration** (temperature, max_tokens)
- Game mechanics (d20 system, combat, skill checks)
- Character creation with classes
- Character sheet tracking (HP, stats, inventory)

**See:** 
- [docs/SPRINT2_SPEC.md](docs/SPRINT2_SPEC.md) — Main specification
- [docs/SPRINT2_IMPROVEMENTS.md](docs/SPRINT2_IMPROVEMENTS.md) — Intent detection & combat state
- [docs/SPRINT2_PROMPTS_CONFIG.md](docs/SPRINT2_PROMPTS_CONFIG.md) — Prompts & config system

### ⏳ Sprint 3: Memory System + CrewAI (Planned)
**Weeks:** 2-3

**Goals:**
- Long-term memory with RAG pipeline
- Supabase PostgreSQL + pgvector
- Memory Manager agent
- Episodic & semantic memory
- Multi-session continuity
- **CrewAI integration** for production-grade orchestration

### ⏳ Sprint 4: Production Ready (Planned)
**Weeks:** 1-2

**Goals:**
- Production-optimized CrewAI configuration
- Redis for FSM persistence
- Webhooks instead of polling
- Deploy to Railway/Render
- Monitoring & cost tracking

**See:** [docs/STRATEGIC_PLAN.md](docs/STRATEGIC_PLAN.md) for detailed roadmap
