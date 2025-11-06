# 🎲 RPGate Telegram Bot - Strategic Plan & Architecture

> **Для PM:** Этот документ — твоя "библия" проекта. Здесь разобраны все архитектурные решения, даны спецификации для AI code agent и roadmap на ближайшие 3 месяца.

---

## 📊 Executive Summary

**Цель проекта:** Создать MVP Telegram бота с AI Game Master, способного вести долгие нарративные сессии с элементами игровых механик.

**Текущий статус:** Sprint 1 ✅ завершен (базовый бот + LLM интеграция)

**Следующий этап:** Sprint 2 — Мульти-агентная архитектура + игровые механики

**Технологический стек (финальный):**
- **Backend:** FastAPI (async, type hints для AI agent)
- **Bot Framework:** Aiogram 3.x (FSM, middleware)
- **Agent Orchestration:** LangGraph (production-ready, циклические workflow)
- **Database:** Supabase PostgreSQL + pgvector (векторная память)
- **LLM Provider:** OpenRouter (гибкость в выборе моделей)
- **Package Manager:** UV (быстрая установка зависимостей)

---

## 🎯 Решение трех критических проблем

### Проблема #1: Долгосрочная память

**Суть проблемы:** Если сессия длится 100+ сообщений, невозможно держать всё в контексте LLM (context window ограничен).

#### Архитектурное решение: Трехуровневая система памяти

```
┌─────────────────────────────────────────────────────────────┐
│                   ТРЕХУРОВНЕВАЯ ПАМЯТЬ                       │
├─────────────────────────────────────────────────────────────┤
│ Level 1: Short-term (Immediate Context)                     │
│ ├─ Последние 5-10 сообщений                                 │
│ ├─ Хранение: FSM context (Redis в production)               │
│ └─ Всегда в промпте агентов                                 │
├─────────────────────────────────────────────────────────────┤
│ Level 2: Medium-term (Session Memory)                       │
│ ├─ Текущая игровая сессия (1-3 часа)                        │
│ ├─ Хранение: PostgreSQL + векторные embeddings              │
│ ├─ Chunking: по 128 токенов или семантическим границам      │
│ └─ Retrieval: RAG с semantic search                         │
├─────────────────────────────────────────────────────────────┤
│ Level 3: Long-term (Character History)                      │
│ ├─ Вся история персонажа за все сессии                      │
│ ├─ Хранение: Compressed summaries + key events              │
│ ├─ Retrieval: Hybrid (keyword + embedding + importance)     │
│ └─ Update frequency: После каждой сессии                    │
└─────────────────────────────────────────────────────────────┘
```

#### Типы памяти (Memory Types)

**1. Semantic Memory** — Знания о мире
- Игровые правила, лор, механики
- Хранится в vector DB как read-only
- Не меняется в рантайме
- Пример: "В этом мире магия запрещена законом"

**2. Episodic Memory** — События и факты
- Что случилось с персонажем
- Structured storage с timestamps
- Importance scoring для приоритизации
- Пример: "2025-11-05 15:30 - Игрок встретил торговца Элдара в таверне"

**3. Procedural Memory** — Как делать действия
- Шаблоны для повторяющихся механик
- Инструкции для агентов
- Пример: "Для проверки атаки бросить d20 + модификатор силы"

**4. Character Sheet Memory** — Текущее состояние
- HP, статы, инвентарь, квесты
- Structured JSON в PostgreSQL
- Real-time updates
- Пример: `{"hp": 15, "max_hp": 20, "gold": 45, "location": "Tavern"}`

#### RAG Pipeline для retrieval

```
User action: "Я возвращаюсь к торговцу"
      ↓
[1] Embed query с помощью OpenAI embeddings API
      ↓
[2] Vector search в pgvector (top-k=5 похожих memories)
      ↓
[3] Keyword filter: "торговец", "Элдар", "таверна"
      ↓
[4] Rerank by: recency (недавние события) + importance (0-10 score)
      ↓
[5] Inject top-3 memories в промпт Memory Manager Agent
      ↓
Output: "Ты уже встречал торговца Элдара в таверне 3 дня назад. 
         Он предлагал тебе карту старого замка за 100 золотых."
```

#### Практическая реализация для Sprint 3

**Database Schema (PostgreSQL):**

```sql
-- Таблица персонажей
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(100),
    character_sheet JSONB,  -- {hp, stats, inventory, etc}
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица игровых сессий
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID REFERENCES characters(id),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    summary TEXT  -- LLM-generated summary после завершения
);

-- Таблица эпизодической памяти с векторным поиском
CREATE TABLE episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID REFERENCES characters(id),
    session_id UUID REFERENCES game_sessions(id),
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    importance_score INT DEFAULT 5,  -- 0-10
    entities TEXT[],  -- ["Элдар", "таверна", "карта"]
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индекс для векторного поиска
CREATE INDEX ON episodic_memories 
USING ivfflat (embedding vector_cosine_ops);

-- Таблица семантической памяти (мировой лор)
CREATE TABLE semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50),  -- 'rule', 'lore', 'location'
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Chunking Strategy:**

```python
# Пример chunking логики для AI agent
def chunk_conversation(messages: list[dict], chunk_size: int = 128) -> list[str]:
    """
    Разбивает диалог на chunks для сохранения в memory.
    
    Стратегия:
    1. Группируем по 128 токенов ИЛИ
    2. По семантическим границам (смена локации, конец боя, конец диалога с NPC)
    """
    # Детальную реализацию делает AI code agent
    pass

def create_session_summary(session_messages: list[dict]) -> str:
    """
    Создает LLM-summary текущей сессии для long-term хранения.
    Вызывается после завершения сессии или каждые 50 сообщений.
    """
    pass
```

**Metrics для оценки качества памяти:**
- **Recall accuracy:** Сколько релевантных фактов извлечено? (target: >85%)
- **Precision:** Сколько извлеченных фактов реально релевантны? (target: >90%)
- **Latency:** Время на retrieval (target: <500ms)

**Cost optimization:**
- Embeddings: используем `text-embedding-3-small` ($0.02 за 1M токенов) вместо `text-embedding-3-large`
- Кэшируем embeddings для повторяющихся запросов
- Batch processing для embeddings (до 100 chunks за раз)

---

### Проблема #2: Архитектура суб-агентов

**Суть проблемы:** Непонятно, какие агенты нужны обязательно, как они взаимодействуют, и как сбалансировать качество/скорость/цену.

#### Решение: Специализированная мульти-агентная система

Как GM со стажем скажу — хороший мастеринг это не один процесс, а параллельное жонглирование несколькими ролями. Ты одновременно:
1. **Storyteller** — рассказываешь историю
2. **Referee** — применяешь правила
3. **World Simulator** — отслеживаешь состояние мира
4. **NPC Actor** — играешь за неигровых персонажей

Наша агентная система должна отражать эти роли.

#### Core Agents (обязательные для MVP)

```
┌────────────────────────────────────────────────────────────┐
│                 МУЛЬТИ-АГЕНТНАЯ СИСТЕМА GM                  │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  User Input: "Я атакую гоблина мечом"                      │
│       ↓                                                     │
│  ┌─────────────────────────────────────┐                   │
│  │ 1. MEMORY MANAGER AGENT             │                   │
│  │ Роль: "Campaign Historian"          │                   │
│  │ Task: Извлечь релевантный контекст  │                   │
│  │ Output: "В прошлой сессии ты ранен, │                   │
│  │         у тебя 12/20 HP"            │                   │
│  └─────────────────────────────────────┘                   │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │        PARALLEL EXECUTION (async)            │          │
│  │  ┌────────────────┐  ┌─────────────────┐    │          │
│  │  │ 2. RULES       │  │ 3. NARRATIVE    │    │          │
│  │  │    ARBITER     │  │    DIRECTOR     │    │          │
│  │  │                │  │                 │    │          │
│  │  │ "Rules Lawyer" │  │ "Storyteller"   │    │          │
│  │  │                │  │                 │    │          │
│  │  │ Броски d20,    │  │ Описание боя,   │    │          │
│  │  │ вычисления     │  │ эмоции, темп    │    │          │
│  │  └────────────────┘  └─────────────────┘    │          │
│  │           ↓                    ↓             │          │
│  │  ┌────────────────────────────────────┐     │          │
│  │  │ 4. WORLD STATE AGENT              │     │          │
│  │  │ Роль: "World Simulator"           │     │          │
│  │  │ Task: Обновить состояние мира     │     │          │
│  │  │ Output: {hp: 7, goblin_dead: true}│     │          │
│  │  └────────────────────────────────────┘     │          │
│  └──────────────────────────────────────────────┘          │
│       ↓                                                     │
│  ┌─────────────────────────────────────┐                   │
│  │ 5. RESPONSE SYNTHESIZER AGENT       │                   │
│  │ Роль: "Master Narrator"             │                   │
│  │ Task: Собрать все outputs в один    │                   │
│  │       красивый narrative ответ      │                   │
│  └─────────────────────────────────────┘                   │
│       ↓                                                     │
│  User Output: "🎲 Ты размахиваешься мечом! [бросок: 18]   │
│                Клинок пронзает гоблина. Он падает.         │
│                [HP: 7/20] [Гоблин: мёртв]"                 │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

#### Детальные спецификации агентов

**Agent #1: Memory Manager**
- **Роль:** Campaign Historian
- **Когда вызывается:** ПЕРВЫМ, перед всеми остальными
- **Input:** User action + character_id
- **Process:** 
  1. Embed user action
  2. Vector search в episodic_memories (top-5)
  3. Keyword filter по entities
  4. Rerank by recency + importance
- **Output:** Top-3 релевантных воспоминания + character sheet
- **LLM Model:** НЕ НУЖНА (чистая логика + embeddings API)
- **Latency:** ~300ms
- **Cost:** $0.0001 за retrieval (embeddings)

**Agent #2: Rules Arbiter**
- **Роль:** Rules Lawyer / Referee
- **Когда вызывается:** В параллели с Narrative Director
- **Input:** User action + character sheet + relevant rules
- **Process:**
  1. Определить тип действия (атака/проверка навыка/магия)
  2. Извлечь нужные правила из Procedural Memory
  3. Выполнить броски (d20 + модификаторы)
  4. Вычислить результат (success/failure/critical)
- **Output:** Structured JSON с результатами
  ```json
  {
    "action_type": "attack",
    "roll": 18,
    "modifier": 3,
    "total": 21,
    "result": "success",
    "damage_roll": 7,
    "effects": ["goblin_hp_reduced"]
  }
  ```
- **LLM Model:** `grok-beta-fast` или `gpt-4o-mini` (дешевый для структурированных задач)
- **Temperature:** 0.1 (низкая для консистентности)
- **Max tokens:** 200
- **Latency:** ~500ms
- **Cost:** ~$0.001 за запрос

**Agent #3: Narrative Director**
- **Роль:** Storyteller / Narrator
- **Когда вызывается:** В параллели с Rules Arbiter
- **Input:** User action + recent conversation history + world context
- **Process:**
  1. Анализировать действие игрока
  2. Генерировать яркое описание
  3. Поддерживать tone/жанр (fantasy/cyberpunk/horror)
  4. Добавлять эмоции и сенсорные детали
- **Output:** Красивый narrative текст (2-4 предложения)
  ```
  "Ты резко выхватываешь меч и размахиваешься в сторону гоблина. 
   Клинок со свистом рассекает воздух и пронзает его грудь. 
   Гоблин хрипит и падает на колени, из раны течёт чёрная кровь."
  ```
- **LLM Model:** `grok-2` или `claude-3.5-sonnet` (качественный для narrative)
- **Temperature:** 0.8 (высокая для creativity)
- **Max tokens:** 300
- **Latency:** ~1200ms
- **Cost:** ~$0.005 за запрос

**Agent #4: World State Agent**
- **Роль:** World Simulator / State Manager
- **Когда вызывается:** После Rules Arbiter (нужны результаты бросков)
- **Input:** Rules output + current world state
- **Process:**
  1. Обновить HP персонажа
  2. Обновить состояние NPC (мертв/ранен/убегает)
  3. Изменить локацию если нужно
  4. Обновить inventory
  5. Проверить квестовые триггеры
- **Output:** Updated character sheet + world state changes
  ```json
  {
    "character_sheet_updates": {
      "hp": 7,
      "location": "goblin_cave_room_2"
    },
    "world_changes": {
      "goblin_1": "dead",
      "quest_goblin_slayer_progress": 1
    }
  }
  ```
- **LLM Model:** `gpt-4o-mini` (структурированные обновления)
- **Temperature:** 0.0 (детерминированность)
- **Max tokens:** 150
- **Latency:** ~400ms
- **Cost:** ~$0.0008 за запрос

**Agent #5: Response Synthesizer**
- **Роль:** Master Narrator / Final Editor
- **Когда вызывается:** ПОСЛЕДНИМ, получает outputs всех агентов
- **Input:** 
  - Rules output (броски, результаты)
  - Narrative output (описание)
  - World state changes
- **Process:**
  1. Собрать все pieces в coherent response
  2. Добавить UI элементы (эмодзи, форматирование)
  3. Убрать противоречия между агентами
  4. Сформировать финальный текст
- **Output:** Готовое сообщение для игрока
  ```
  🎲 **Атака мечом** [🎲 18+3 = 21] ✅ Успех!
  
  Ты резко выхватываешь меч и размахиваешься в сторону гоблина. 
  Клинок со свистом рассекает воздух и пронзает его грудь. 
  Гоблин хрипит и падает на колени, из раны течёт чёрная кровь.
  
  💔 Урон: 7 HP
  ⚔️ Гоблин повержен!
  
  ❤️ Твоё здоровье: 7/20 HP
  📍 Локация: Пещера гоблинов, комната 2
  ```
- **LLM Model:** `gpt-4o` (лучший для финального качества)
- **Temperature:** 0.3 (баланс creativity + консистентности)
- **Max tokens:** 400
- **Latency:** ~800ms
- **Cost:** ~$0.002 за запрос

#### Optional Agents (Sprint 4+)

**Agent #6: Tone/Emotion Analyzer**
- **Роль:** Emotional Intelligence
- **Цель:** Анализировать эмоциональное состояние игрока и подстраивать подачу
- **Пример:** Если игрок фрустрирован после серии неудач — GM смягчает тон или даёт подсказку

**Agent #7: Content Safety Filter**
- **Роль:** Content Moderator
- **Цель:** Фильтровать нежелательный контент (NSFW, violence beyond rating)
- **Критичность:** Важно для публичного релиза

#### Workflow Execution Strategy

**Последовательность (Sequence):**
```
Memory Manager → [Parallel: Rules + Narrative + World] → Response Synthesizer
```

**Latency Analysis:**
- Memory Manager: 300ms
- Parallel (longest = Narrative): 1200ms
- Response Synthesizer: 800ms
- **Total:** ~2300ms (2.3 секунды)

**Optimization для latency:**
1. **Streaming response:** Response Synthesizer может начать отправлять текст до завершения World State Agent
2. **Caching:** Кэшировать rules lookups и world state queries
3. **Model selection:** Для Rules/World использовать быстрые модели (gpt-4o-mini, grok-beta-fast)

**Cost per turn:**
- Memory: $0.0001
- Rules: $0.001
- Narrative: $0.005
- World: $0.0008
- Synthesizer: $0.002
- **Total:** ~$0.009 за ход (~$0.01)

При 100 ходах в сессии: **$1.00 за сессию**

**Снижение costs (если нужно):**
1. Использовать Grok вместо Claude для Narrative (-60% cost)
2. Batch embeddings для Memory Manager
3. Кэшировать промпты через OpenRouter caching

---

### Проблема #3: Технологический стек для AI Code Agent

**Суть проблемы:** Нужен стек, который:
1. Хорошо понимается AI code agent (Copilot/Claude)
2. Высокоуровневый (минимум boilerplate)
3. Масштабируемый
4. Быстрый в разработке и тестировании

#### Финальный Tech Stack (обновленный)

**✅ Backend Framework: FastAPI**
- **Почему:** Async из коробки, type hints (AI агенты их обожают), автодокументация, огромное комьюнити
- **Для AI agent:** Декларативный стиль, понятные паттерны

**✅ Bot Framework: Aiogram 3.x**
- **Почему:** FSM для state management, middleware, отличная async поддержка
- **Уже используется:** В Sprint 1

**✅ Agent Orchestration: CrewAI**
- **Почему выбрали для MVP:**
  - Быстрый setup (<1 час для прототипа)
  - Простая декларативная конфигурация агентов
  - Built-in role-based agents (идеально для GM концепта)
  - Хорошая интеграция с OpenRouter
  - Достаточно для sequential и simple parallel workflows
  - Минимум boilerplate кода

**Для Sprint 2-3:** CrewAI покроет все наши нужды. Если в будущем понадобятся циклические workflow или более сложная оркестрация — можно мигрировать на LangGraph в Sprint 4+.

**✅ Database: Supabase (PostgreSQL + pgvector)**
- **Почему:**
  - PostgreSQL — надежная, AI agent знает SQL
  - pgvector — векторный поиск из коробки
  - REST API автогенерируется (меньше кода)
  - RLS policies для безопасности
  - Бесплатный tier для MVP
- **Альтернатива:** Простой PostgreSQL + Qdrant (separate vector DB) если нужна более продвинутая векторная семантика

**✅ Package Manager: UV**
- **Уже используется:** В Sprint 1
- **Почему:** Быстрее pip в 10-100x, понятный для AI agent

**✅ LLM Provider: OpenRouter**
- **Уже используется:** В Sprint 1
- **Почему:** Единый API для разных моделей (Grok, GPT, Claude), легко менять модели без переписывания кода

**❌ НЕ используем (для MVP):**
- ~~LangChain/LangGraph~~ — слишком heavyweight для прототипа, CrewAI проще и быстрее
- ~~Vector DB (Pinecone/Weaviate)~~ — pgvector в Supabase достаточно для MVP
- ~~Redis~~ — MemoryStorage достаточно для MVP, Redis в production (Sprint 4)

#### Структура проекта (финальная)

```
rpgate-tg/
├── .env
├── .gitignore
├── pyproject.toml
├── uv.lock
├── README.md
├── docs/
│   ├── STRATEGIC_PLAN.md          # Этот документ
│   ├── development-plan.md
│   ├── SPRINT1_CHECKLIST.md
│   ├── SPRINT2_SPEC.md           # Спецификация для Sprint 2
│   └── API_CONTRACTS.md          # Контракты между агентами
├── app/
│   ├── __init__.py
│   ├── main.py                   # Entry point
│   ├── config.py                 # Settings
│   ├── bot/                      # Telegram bot layer
│   │   ├── __init__.py
│   │   ├── handlers.py
│   │   ├── states.py
│   │   └── keyboards.py         # Inline keyboards (Sprint 2)
│   ├── agents/                   # 🆕 Multi-agent system
│   │   ├── __init__.py
│   │   ├── base.py              # Base agent class
│   │   ├── memory_manager.py
│   │   ├── rules_arbiter.py
│   │   ├── narrative_director.py
│   │   ├── world_state.py
│   │   ├── response_synthesizer.py
│   │   └── orchestrator.py      # Agent workflow orchestrator
│   ├── game/                     # 🆕 Game mechanics
│   │   ├── __init__.py
│   │   ├── character.py         # Character sheet model
│   │   ├── dice.py              # Dice rolling system
│   │   ├── rules.py             # Game rules engine
│   │   └── world.py             # World state management
│   ├── memory/                   # 🆕 Memory system (Sprint 3)
│   │   ├── __init__.py
│   │   ├── episodic.py          # Episodic memory manager
│   │   ├── semantic.py          # Semantic memory (lore)
│   │   ├── embeddings.py        # Embedding generation
│   │   └── retrieval.py         # RAG pipeline
│   ├── db/                       # 🆕 Database layer (Sprint 3)
│   │   ├── __init__.py
│   │   ├── models.py            # SQLAlchemy/Pydantic models
│   │   ├── supabase.py          # Supabase client
│   │   └── migrations/          # DB migrations
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py            # OpenRouter client (существующий)
│   │   └── prompts.py           # 🆕 Prompt templates
│   └── utils/
│       ├── __init__.py
│       ├── logging.py           # Structured logging
│       └── metrics.py           # Performance metrics
├── tests/                        # 🆕 Testing (Sprint 2+)
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_game_mechanics.py
│   └── fixtures/                # Test data
│       └── test_scenarios.json
└── scripts/                      # 🆕 Utility scripts
    ├── seed_lore.py             # Загрузка начального лора в DB
    └── test_conversation.py     # CLI для тестирования без Telegram
```

#### Development Workflow для PM

Как PM без знания кода, твой workflow:

1. **Пишешь спецификацию** в Markdown (например, `SPRINT2_SPEC.md`)
2. **Описываешь behaviour** агента в plain English
3. **Даешь AI code agent** команду: "Реализуй Agent #2 (Rules Arbiter) согласно спецификации в docs/SPRINT2_SPEC.md"
4. **Тестируешь** через CLI: `uv run python scripts/test_conversation.py`
5. **Итерируешь** если нужно

**Пример спецификации для AI agent:**

```markdown
## Task: Implement Rules Arbiter Agent

**File:** `app/agents/rules_arbiter.py`

**Requirements:**
- Agent class наследуется от BaseAgent
- Метод `execute(user_action: str, character_sheet: dict) -> dict`
- Определяет тип действия (attack/skill_check/spell)
- Для атаки: бросает d20 + модификатор силы
- Возвращает structured JSON с результатом

**Input example:**
```python
{
  "user_action": "Я атакую гоблина мечом",
  "character_sheet": {"strength_mod": 3}
}
```

**Output example:**
```python
{
  "action_type": "attack",
  "roll": 18,
  "modifier": 3,
  "total": 21,
  "result": "success"
}
```

**LLM Model:** gpt-4o-mini  
**Temperature:** 0.1  
**Max tokens:** 200
```

AI code agent возьмет эту спецификацию и сгенерирует правильный код.

---

## 🗺️ Roadmap на 3 месяца

### Sprint 2: Multi-Agent Foundation (2-3 недели)

**Цель:** Базовая мульти-агентная система с игровыми механиками

**Deliverables:**
- ✅ 3 core agents: Rules Arbiter, Narrative Director, Response Synthesizer
- ✅ Простая система бросков (d20 + модификаторы)
- ✅ Character sheet в JSON (хранение в FSM context)
- ✅ Базовые game mechanics (атака, проверка навыков)
- ✅ Ручная оркестрация агентов (без LangGraph пока)

**Структура Sprint 2:**

**Week 1: Game Mechanics Foundation**
- [ ] Создать `app/game/character.py` — Character model (Pydantic)
- [ ] Создать `app/game/dice.py` — Dice rolling system (d4, d6, d8, d10, d12, d20, d100)
- [ ] Создать `app/game/rules.py` — Rules engine (attack resolution, skill checks)
- [ ] Unit tests для dice и rules

**Week 2: Agent System**
- [ ] Создать `app/agents/base.py` — Base agent class
- [ ] Реализовать Rules Arbiter agent
- [ ] Реализовать Narrative Director agent
- [ ] Реализовать Response Synthesizer agent
- [ ] Создать `app/agents/orchestrator.py` — Simple sequential orchestrator

**Week 3: Integration**
- [ ] Обновить `app/bot/handlers.py` — интегрировать agents вместо прямого LLM вызова
- [ ] Добавить character creation flow (новый FSM state)
- [ ] Добавить inline keyboards для выбора действий
- [ ] Testing через Telegram bot
- [ ] Документация Sprint 2 completion

**Success Criteria:**
- Бот может вести бой с базовыми механиками (атака, проверки)
- Ответы красиво отформатированы (Synthesizer работает)
- Character sheet отслеживается корректно

---

### Sprint 3: Memory System + CrewAI Integration (2-3 недели)

**Цель:** Долгосрочная память работает + переход на CrewAI для оркестрации

**Deliverables:**
- ✅ Supabase PostgreSQL + pgvector setup
- ✅ Memory Manager agent
- ✅ Episodic memory с chunking
- ✅ RAG pipeline для retrieval
- ✅ World State agent для глобального состояния
- ✅ **CrewAI integration** для production-grade orchestration

**Структура Sprint 3:**

**Week 1: Database Setup**
- [ ] Setup Supabase project
- [ ] Database schema migration (characters, sessions, episodic_memories, semantic_memories)
- [ ] Create `app/db/supabase.py` — Supabase client
- [ ] Create `app/db/models.py` — Pydantic models для DB entities
- [ ] Install CrewAI: `uv add crewai crewai-tools`

**Week 2: Memory System + CrewAI Setup**
- [ ] Реализовать `app/memory/embeddings.py` — OpenAI embeddings API wrapper
- [ ] Реализовать `app/memory/episodic.py` — Episodic memory CRUD
- [ ] Реализовать `app/memory/retrieval.py` — RAG pipeline (vector search + reranking)
- [ ] Реализовать Memory Manager agent
- [ ] **Convert agents to CrewAI format** (add @agent and @task decorators)

**Week 3: Integration & World State**
- [ ] Реализовать World State agent
- [ ] **Create CrewAI Crew** configuration в `app/agents/crew.py`
- [ ] Migrate orchestrator to use CrewAI Crew
- [ ] Chunking system для conversation history
- [ ] Session summary generation (LLM-based)
- [ ] Testing: multi-session continuity

**Success Criteria:**
- Бот помнит события из прошлых сессий
- Memory retrieval latency <500ms
- RAG accuracy >85%
- CrewAI оркестрация работает smoothly
- Agents execute в правильной последовательности

---

### Sprint 4: Polish & Production (1-2 недели)

**Цель:** Production-ready MVP

**Deliverables:**
- ✅ Production-grade CrewAI configuration (оптимизация workflow)
- ✅ Redis для FSM storage (замена MemoryStorage)
- ✅ Webhooks вместо polling
- ✅ Error handling & monitoring
- ✅ Cost tracking & optimization
- ✅ Deploy на Railway/Render

**Структура Sprint 4:**

**Week 1: Production Infrastructure**
- [ ] Setup Redis для FSM persistence
- [ ] Migrate от polling к webhooks (FastAPI endpoint)
- [ ] Optimize CrewAI workflow (parallel execution где возможно)
- [ ] Structured logging (JSON logs)
- [ ] Cost tracking middleware

**Week 2: Deploy & Monitoring**
- [ ] Dockerfile для deployment
- [ ] Deploy на Railway (или Render)
- [ ] Setup monitoring (Sentry для errors)
- [ ] Load testing (simulate 10 concurrent users)
- [ ] Documentation для deploy process

**Success Criteria:**
- Бот работает в production 24/7
- Latency <3 секунды на ход
- Cost <$0.02 за ход
- Uptime >99%

**Optional (если нужна более сложная оркестрация):**
- [ ] Migrate от CrewAI к LangGraph для advanced workflows

---

## 📝 Спецификации для AI Code Agent

Для каждой задачи создаются детальные spec-файлы в `docs/specs/`:

### Пример: Sprint 2 Spec

Создам отдельный файл `docs/SPRINT2_SPEC.md` (см. следующий документ)

---

## 🎮 Game Design: Single World vs Personal Worlds

**Рекомендация для MVP: Personal Worlds**

**Почему:**
1. **Проще state management** — каждый игрок имеет свой world state, нет race conditions
2. **Легче масштабировать** — каждый пользователь независим
3. **Быстрее разработка** — не нужна синхронизация между игроками
4. **Лучше для тестирования** — можно тестировать параллельно

**Общий мир (Shared World) — для v2.0:**
- Требует coordination между игроками
- Нужна система синхронизации событий
- Сложнее в разработке (+ 3-4 недели)
- Но круче для multiplayer experience

**Архитектурное решение:** Делаем систему так, чтобы переход был легким:
- World State agent работает с `world_id` параметром
- Для MVP: `world_id = user_id` (personal world)
- Для v2: `world_id = "shared_world_1"` (общий мир)

---

## 📊 Metrics & Success Criteria

### MVP Success Metrics

**User Experience:**
- [ ] Response time <3 секунды на ход
- [ ] Conversation continuity >5 сессий
- [ ] User retention >30% после 3 дней

**Technical:**
- [ ] Uptime >95%
- [ ] Cost per session <$1.50
- [ ] Memory retrieval accuracy >85%
- [ ] Error rate <1%

**Narrative Quality (subjective):**
- [ ] GM responses звучат natural и engaging
- [ ] Consistency в narrative (нет противоречий)
- [ ] Game mechanics работают fair

---

## 🛠️ Testing Strategy (без фронтенда)

### Тестирование для PM без кода

**1. CLI Test Script** (`scripts/test_conversation.py`)

```python
# Пример использования для PM:
# uv run python scripts/test_conversation.py

# Скрипт запускает conversation в терминале без Telegram
# Ты вводишь действия игрока, видишь ответы GM
# Идеально для быстрого тестирования агентов
```

**2. Test Scenarios** (`tests/fixtures/test_scenarios.json`)

```json
[
  {
    "name": "Basic Attack",
    "user_action": "Я атакую гоблина мечом",
    "expected_mechanics": {
      "action_type": "attack",
      "dice": "d20"
    },
    "expected_narrative_contains": ["меч", "гоблин"]
  },
  {
    "name": "Skill Check",
    "user_action": "Я пытаюсь взломать дверь",
    "expected_mechanics": {
      "action_type": "skill_check",
      "skill": "lockpicking"
    }
  }
]
```

AI code agent прогоняет эти scenarios и проверяет outputs.

**3. Unit Tests для агентов**

```python
# tests/test_agents.py
def test_rules_arbiter_attack():
    agent = RulesArbiterAgent()
    result = agent.execute(
        user_action="Я атакую гоблина",
        character_sheet={"strength_mod": 3}
    )
    assert result["action_type"] == "attack"
    assert "roll" in result
    assert result["roll"] >= 1 and result["roll"] <= 20
```

---

## 💰 Cost Optimization Strategies

### Текущий cost: ~$0.01 за ход

**Если нужно снизить:**

1. **Model downgrade для non-critical agents:**
   - Narrative Director: `grok-2` → `grok-beta-fast` (-70% cost)
   - Rules Arbiter: `gpt-4o-mini` → `gpt-3.5-turbo` (-50% cost)

2. **Prompt caching через OpenRouter:**
   - System prompts кэшируются, платишь только за новые tokens
   - Savings: ~40% для повторяющихся промптов

3. **Batch requests:**
   - Собирать несколько memory queries в один batch

4. **Conditional agent invocation:**
   - Если действие простое ("Я иду вперед") — пропускаем Rules Arbiter

**Target cost для production:** <$0.02 за ход → $2.00 за 100-ходовую сессию

---

## 🚀 Next Steps для PM

### Immediate Actions (сегодня):

1. ✅ Прочитать этот Strategic Plan
2. ✅ Убедиться что Sprint 1 работает (`uv run start`)
3. ✅ Прочитать `docs/SPRINT2_SPEC.md` (создам следующим)

### This Week:

1. [ ] Определиться с game mechanics (какие dice, какие stats для персонажа)
2. [ ] Написать начальный lore для мира (2-3 параграфа)
3. [ ] Дать AI code agent задачу: "Start Sprint 2 - implement dice system"

### This Month:

1. [ ] Завершить Sprint 2
2. [ ] Протестировать бота с друзьями
3. [ ] Собрать feedback на game mechanics

---

## 📚 Ресурсы и референсы

**Документация:**
- [Aiogram 3.x Docs](https://docs.aiogram.dev/en/latest/)
- [CrewAI Docs](https://docs.crewai.com/)
- [Supabase Docs](https://supabase.com/docs)
- [OpenRouter Models](https://openrouter.ai/models)

**Inspiration (AI GM системы):**
- [AI Dungeon](https://play.aidungeon.io/) — пионер AI storytelling
- [NovelAI](https://novelai.net/) — narrative generation
- [ChatGPT DM](https://github.com/examples) — community projects

**GM Best Practices (для промптов):**
- "Return of the Lazy Dungeon Master" by Michael Shea
- "The Alexandrian" blog — GMing techniques

---

## 🎯 Summary для быстрого старта

**Ты как PM должен:**
1. **Для каждой фичи** писать spec в plain English
2. **Давать AI agent** конкретные задачи из spec
3. **Тестировать** через CLI или Telegram
4. **Итерировать** на основе результатов

**AI code agent должен:**
1. **Читать spec** файлы из `docs/specs/`
2. **Генерировать код** согласно спецификациям
3. **Следовать архитектуре** из этого Strategic Plan
4. **Писать тесты** для каждого компонента

**Следующий документ:** `docs/SPRINT2_SPEC.md` — детальная спецификация для Sprint 2

---

*Этот документ — living document. Обновляй по мере development.*

**Вопросы?** Пиши в issues или комментарии к коду.

**Готов к Sprint 2?** Давай!
