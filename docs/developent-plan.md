# --- DEPRECATED: Typo filename. Use development-plan.md instead. ---
Отлично! Вот детальная спецификация Sprint 1 для AI code agent с пошаговыми инструкциями и структурой проекта.

## Sprint 1: Foundation — Детальная спецификация

**Цель:** Создать рабочий Telegram бот с базовой интеграцией LLM и FSM для управления состояниями диалога.

**Timeframe:** 1-2 недели

### Шаг 1: Инициализация проекта с UV

**1.1 Создание структуры проекта**

Выполните команды для создания нового проекта:

```bash
uv init
```

**1.2 Установка зависимостей**

Добавьте необходимые пакеты через UV:

```bash
# Core dependencies
uv add fastapi aiogram==3.13.0 openai python-dotenv pydantic-settings

# Development dependencies  
uv add --group dev pytest pytest-asyncio black ruff
```

**Ожидаемый результат:** Создан файл `pyproject.toml` со следующим содержимым:

```toml
[project]
name = "rpgate-tg"
version = "0.1.0"
description = "AI-powered Game Master Telegram Bot"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "aiogram>=3.13.0",
    "openai>=1.54.0",
    "python-dotenv>=1.0.0",
    "pydantic-settings>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "black>=24.10.0",
    "ruff>=0.7.0",
]
```

### Шаг 2: Структура проекта

Создайте следующую структуру директорий:

```
rpgate-tg/
├── .env                    # Environment variables (создать вручную)
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore file
├── docs/                   # Documentation folder
│   └── development-plan.md # Этот файл
├── pyproject.toml         # UV project configuration
├── uv.lock               # UV lock file (автогенерируется)
├── README.md             # Project documentation
└── app/
    ├── __init__.py
    ├── main.py           # Entry point
    ├── config.py         # Configuration loader
    ├── bot/
    │   ├── __init__.py
    │   ├── handlers.py   # Telegram handlers
    │   └── states.py     # FSM states
    └── llm/
        ├── __init__.py
        └── client.py     # OpenRouter/Grok client
```

### Шаг 3: Конфигурация (.env файлы)

**3.1 Создайте файл `.env.example` в корне проекта (шаблон):**

```env
# Telegram Bot Token (получить у @BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# OpenRouter API Key (получить на openrouter.ai)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional: Your site URL for OpenRouter rankings
SITE_URL=http://localhost:8000

# LLM Model
LLM_MODEL=x-ai/grok-beta-fast
```

**3.2 Создайте файл `.env` в корне проекта (скопируйте из `.env.example` и заполните реальными значениями):**

```bash
cp .env.example .env
# Затем отредактируйте .env и добавьте свои ключи
```

### Шаг 4: Код — Configuration Module

**Файл: `app/config.py`**

```python
"""
Configuration module для загрузки environment variables.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    site_url: str = Field(default="http://localhost:8000", alias="SITE_URL")
    llm_model: str = Field(default="x-ai/grok-beta-fast", alias="LLM_MODEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance с валидацией
try:
    settings = Settings()
except Exception as e:
    raise RuntimeError(
        f"Failed to load settings. Please check your .env file exists and contains "
        f"required variables: TELEGRAM_BOT_TOKEN, OPENROUTER_API_KEY. "
        f"You can copy .env.example to .env and fill in your values. Error: {e}"
    )
```



### Шаг 5: Код — LLM Client (OpenRouter + Grok)

**Файл: `app/llm/client.py`**

```python
"""
OpenRouter client для работы с Grok-4-fast через OpenAI-совместимый API.
"""
import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client для взаимодействия с LLM через OpenRouter."""
    
    def __init__(self):
        """Initialize OpenRouter client with Grok configuration."""
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self.model = settings.llm_model
        self.extra_headers = {
            "HTTP-Referer": settings.site_url,
        }
    
    async def get_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Получить completion от LLM.
        
        Args:
            messages: List of message dicts с ролями 'system', 'user', 'assistant'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers=self.extra_headers,
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"LLM API Error: {e}", exc_info=True)
            
            # Обработка rate limits от OpenRouter
            if "rate_limit" in str(e).lower() or "429" in str(e):
                return "⏳ I'm getting too many requests right now. Please wait a moment and try again."
            
            # Обработка других ошибок API
            return "❌ Sorry, I encountered an error processing your request. Please try again later."


# Singleton instance
llm_client = LLMClient()
```

**Технические детали для AI agent:**
- OpenRouter использует OpenAI-совместимый API endpoint `https://openrouter.ai/api/v1`
- Модель Grok-4-fast указывается как `x-ai/grok-beta-fast`
- `HTTP-Referer` header опциональный, но рекомендуется для отслеживания на OpenRouter

### Шаг 6: Код — FSM States

**Файл: `app/bot/states.py`**

```python
"""
Finite State Machine states для управления диалогом бота.
"""
from aiogram.fsm.state import State, StatesGroup


class ConversationState(StatesGroup):
    """States для основного диалога с игроком."""
    
    # Начальное состояние - ожидание команды /start
    idle = State()
    
    # Игрок в активном диалоге с GM
    in_conversation = State()
    
    # Игрок создает нового персонажа (для будущих спринтов)
    creating_character = State()
```

**Примечание:** На этапе MVP используем только `idle` и `in_conversation`. Остальные states добавятся в Sprint 2-3.

### Шаг 7: Код — Telegram Handlers

**Файл: `app/bot/handlers.py`**

```python
"""
Telegram bot handlers для обработки сообщений пользователя.
"""
import asyncio
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import ConversationState
from app.llm.client import llm_client


# Router для всех handlers
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler для команды /start - инициализация бота.
    """
    await state.set_state(ConversationState.in_conversation)
    await message.answer(
        "🎲 Welcome, adventurer! I am your AI Game Master.\n\n"
        "Tell me what you want to do, and I'll narrate your story.\n"
        "Type /help for available commands."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handler для команды /help - показать доступные команды.
    """
    help_text = (
        "🎮 **Available Commands:**\n\n"
        "/start - Start or restart conversation\n"
        "/help - Show this help message\n"
        "/reset - Clear conversation history\n"
        "/ping - Check bot status\n\n"
        "Just send me a message to continue your adventure!"
    )
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    """
    Handler для команды /ping - проверка работоспособности бота.
    """
    await message.answer("🟢 Bot is online and ready!")



@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """
    Handler для команды /reset - очистка истории и сброс состояния.
    """
    await state.clear()
    await state.set_state(ConversationState.idle)
    await message.answer("✨ Conversation reset! Use /start to begin a new adventure.")


@router.message(
    ConversationState.in_conversation,
    F.text  # Только текстовые сообщения
)
async def handle_conversation(message: Message, state: FSMContext):
    """
    Main handler для диалога с игроком в активном состоянии.
    Отправляет сообщение пользователя в LLM и возвращает ответ.
    """
    user_message = message.text
    
    # Получаем историю из FSM context (пока простая реализация)
    data = await state.get_data()
    conversation_history = data.get("history", [])
    
    # Добавляем системный промпт (базовый для MVP)
    if not conversation_history:
        conversation_history.append({
            "role": "system",
            "content": (
                "You are an experienced Game Master running a fantasy RPG adventure. "
                "Narrate the story vividly, respond to player actions, and create "
                "engaging scenarios. Keep responses concise (2-3 paragraphs max)."
            )
        })
    
    # Добавляем сообщение пользователя
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Запускаем typing indicator в фоне
    typing_task = asyncio.create_task(
        _send_typing_indicator(message)
    )
    
    try:
        # Получаем ответ от LLM
        gm_response = await llm_client.get_completion(
            messages=conversation_history,
            temperature=0.8,  # Creativity для narrative
            max_tokens=600,
        )
    finally:
        # Останавливаем typing indicator
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    # Добавляем ответ GM в историю
    conversation_history.append({
        "role": "assistant",
        "content": gm_response
    })
    
    # Сохраняем обновленную историю (ограничение: последние 10 сообщений)
    if len(conversation_history) > 21:  # system + 10 pairs
        conversation_history = [conversation_history[0]] + conversation_history[-20:]
    
    await state.update_data(history=conversation_history)
    
    # Отправляем ответ игроку
    await message.answer(gm_response)


@router.message(ConversationState.idle)
async def handle_idle_state(message: Message):
    """
    Handler для сообщений в idle состоянии.
    Предлагает пользователю начать с /start.
    """
    await message.answer(
        "👋 Hey there! Use /start to begin your adventure, "
        "or /help to see available commands."
    )


async def _send_typing_indicator(message: Message):
    """
    Вспомогательная функция для отправки typing indicator в цикле.
    Запускается как фоновая задача и отменяется после получения ответа от LLM.
    """
    try:
        while True:
            await message.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            # Typing indicator живет ~5 секунд, обновляем каждые 4 секунды
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        # Нормальное завершение при отмене задачи
        pass
```

**Технические детали для AI agent:**
- `Router()` используется для группировки handlers в Aiogram 3.x
- `StateFilter` автоматически применяется через декоратор `@router.message(State)`
- FSM context хранит данные в памяти (для production нужен Redis - Sprint 3)
- История ограничена 10 сообщениями для управления токенами в context window
- Typing indicator запускается в отдельной asyncio задаче и автоматически отменяется после получения ответа
- Функция `_send_typing_indicator()` обновляет typing каждые 4 секунды (indicator живет ~5 секунд)

### Шаг 8: Код — Main Application

**Файл: `app/main.py`**

```python
"""
Entry point для Telegram бота.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.bot.handlers import router
from app.bot.states import ConversationState


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Main function для запуска бота.
    """
    # Initialize Bot instance
    bot = Bot(token=settings.telegram_bot_token)
    
    # Initialize Dispatcher with FSM storage
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register router with handlers
    dp.include_router(router)
    
    logger.info("Starting bot...")
    
    try:
        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
```

**Технические детали для AI agent:**
- `MemoryStorage()` используется для хранения FSM states в RAM (для MVP достаточно)
- `dp.resolve_used_update_types()` автоматически определяет нужные типы updates
- `start_polling()` запускает long-polling для получения updates от Telegram

### Шаг 9: Запуск проекта

**9.1 Запуск бота локально**

Используйте UV для запуска:

```bash
uv run python -m app.main
```

Или добавьте скрипт в `pyproject.toml`:

```toml
[project.scripts]
start = "app.main:main"
```

Тогда запуск упрощается до:

```bash
uv run start
```

**9.2 Тестирование функциональности**

Проверьте работу бота в Telegram:

1. ✅ `/ping` — бот отвечает что онлайн
2. ✅ `/start` — бот приветствует и переводит в состояние `in_conversation`
3. ✅ Отправьте любое сообщение — бот показывает typing indicator и отвечает через LLM (Grok)
4. ✅ `/help` — бот показывает список команд
5. ✅ `/reset` — бот очищает историю и возвращается в `idle`
6. ✅ Отправьте сообщение в idle — бот просит использовать `/start`

### Шаг 10: Добавьте .gitignore

**Файл: `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
.uv/

# Environment variables
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log
```

### Шаг 11: README.md

**Файл: `README.md`**

```markdown
# GM Telegram Bot - MVP Sprint 1

AI-powered Game Master Telegram bot using Grok-4-fast via OpenRouter.

## Setup

1. Install dependencies:
   ```
   uv sync
   ```

2. Create `.env` file (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your API keys.

3. Run the bot:
   ```
   uv run python -m app.main
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
```

***

## Deliverable Checklist для Sprint 1

После выполнения всех шагов у вас должно быть:

- ✅ Проект инициализирован через UV с правильной структурой
- ✅ Все зависимости установлены (`pyproject.toml` + `uv.lock`)
- ✅ `.env.example` файл создан как шаблон
- ✅ `.env` файл настроен с Telegram token и OpenRouter API key
- ✅ Валидация конфигурации с понятными сообщениями об ошибках
- ✅ LLM client работает с Grok-4-fast через OpenRouter
- ✅ Aiogram 3.x бот с FSM (2 states: idle, in_conversation)
- ✅ 5 команд работают: `/start`, `/help`, `/reset`, `/ping`, и обычные сообщения
- ✅ История диалога сохраняется в FSM context (последние 10 сообщений)
- ✅ Бот отвечает через LLM с GM persona
- ✅ Typing indicator в отдельной asyncio задаче
- ✅ Улучшенный error handling с логированием через logger
- ✅ Обработка rate limits от OpenRouter
- ✅ Документация в README.md