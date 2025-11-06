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

## Features (Sprint 1)

- ✅ Basic conversation with AI Game Master
- ✅ FSM state management (idle/in_conversation)
- ✅ Conversation history (last 10 messages)
- ✅ Commands: /start, /help, /reset, /ping
- ✅ Typing indicator для улучшения UX
- ✅ Error handling и logging
- ✅ Rate limit обработка от OpenRouter

## Next Steps (Sprint 2)

- Multi-agent architecture (CrewAI)
- Game mechanics (dice rolls, character sheet)
- Long-term memory (RAG + Vector DB)
