# 📚 Documentation Index

> **Last Updated:** 7 ноября 2025 г.  
> **Current Sprint:** Sprint 3 (Memory System - Cost Optimized)

---

## 🎯 Start Here

### For PM (Non-Technical):
1. **[MVP Plan (Updated)](MVP_PLAN_UPDATED.md)** ⭐ - Roadmap на все спринты
2. **[Sprint 3 Changes Summary](SPRINT3_CHANGES_SUMMARY.md)** - Краткий summary изменений
3. **[Strategic Plan](STRATEGIC_PLAN.md)** - Общая архитектура проекта

### For AI Code Agent:
1. **[Sprint 3 Spec (Updated)](SPRINT3_UPDATED.md)** ⭐ - Детальная спецификация для реализации
2. **[API Contracts](API_CONTRACTS.md)** - Agent communication formats
3. **[Sprint 2 Spec](SPRINT2_SPEC.md)** - Референс существующих agents

---

## 📖 Core Documents

### Architecture & Planning:
- **[Strategic Plan](STRATEGIC_PLAN.md)** - Architectural "bible" проекта
  - Решение 3 критических проблем (память, агенты, стек)
  - Multi-agent system design
  - Updated Sprint 3 section (cost-optimized)

- **[MVP Plan (Updated)](MVP_PLAN_UPDATED.md)** ⭐ **NEW** - Актуальный roadmap
  - Current status (Sprint 1-2 done, Sprint 3 in progress)
  - Week-by-week breakdown
  - Cost economics (₽0.22/turn)
  - Success metrics

### Sprint Specifications:
- **[Sprint 3 Spec (Updated)](SPRINT3_UPDATED.md)** ⭐ **CURRENT**
  - Cost-optimized memory system
  - LLM-based importance scoring (zero overhead)
  - Temporal ranking (no session summaries)
  - Confidence-based knowledge scoping
  - Layered retrieval implementation

- **[Sprint 3 Changes Summary](SPRINT3_CHANGES_SUMMARY.md)** ⭐ **NEW** - Quick reference
  - Key problems solved
  - Architectural changes
  - Cost impact analysis
  - Migration path

- **[Sprint 2 Spec](SPRINT2_SPEC.md)** - Multi-agent system (✅ completed)
- **[Sprint 1 Checklist](SPRINT1_CHECKLIST.md)** - Basic bot (✅ completed)

### Technical Specs:
- **[API Contracts](API_CONTRACTS.md)** - Agent input/output schemas
- **[Sprint 3 Setup Guide](SPRINT3_SETUP_GUIDE.md)** - Database setup
- **[Sprint 3 Progress](SPRINT3_PROGRESS.md)** - Implementation tracking

---

## 🔥 Recent Changes (7 Nov 2025)

### Sprint 3 Architecture Updated:

**Problem 1 Solved:** Importance Scoring для русского языка
- ❌ Keyword heuristics не работают (морфология, синонимы)
- ✅ LLM-based scoring через Synthesizer (zero overhead)

**Problem 2 Solved:** Session Summaries избыточны
- ❌ Separate summary generation (+$0.001 per session)
- ✅ Temporal ranking + layered retrieval (бесшовная игра)

**Problem 3 Solved:** Metagaming Prevention
- ❌ Hard metadata tags (хрупко, LLM errors)
- ✅ Confidence scores (probabilistic, graceful degradation)

**Cost Impact:**
- Before: $0.00198 base + $0.0005 overhead = $0.00248
- After: $0.00198 base + $0.00017 overhead = $0.00215 (₽0.22)
- **Savings: 66% от projected overhead!**

См. **[Sprint 3 Changes Summary](SPRINT3_CHANGES_SUMMARY.md)** для деталей.

---

## 📊 Document Status

| Document | Status | Last Updated | Purpose |
|----------|--------|--------------|---------|
| **[MVP_PLAN_UPDATED.md](MVP_PLAN_UPDATED.md)** | ✅ Current | 2025-11-07 | Roadmap all sprints |
| **[SPRINT3_UPDATED.md](SPRINT3_UPDATED.md)** | ✅ Current | 2025-11-07 | Sprint 3 full spec |
| **[SPRINT3_CHANGES_SUMMARY.md](SPRINT3_CHANGES_SUMMARY.md)** | ✅ Current | 2025-11-07 | Quick reference |
| **[STRATEGIC_PLAN.md](STRATEGIC_PLAN.md)** | ✅ Updated | 2025-11-07 | Architecture bible |
| **[SPRINT3_SPEC.md](SPRINT3_SPEC.md)** | ⚠️ Deprecated | 2025-11-05 | Use UPDATED version |
| **[SPRINT2_SPEC.md](SPRINT2_SPEC.md)** | ✅ Reference | 2025-11-04 | Sprint 2 completed |
| **[API_CONTRACTS.md](API_CONTRACTS.md)** | ✅ Current | 2025-11-04 | Agent schemas |

---

## 🔍 Quick Navigation

### Looking for...

**Memory system architecture?**
→ [Sprint 3 Spec (Updated)](SPRINT3_UPDATED.md)

**Cost breakdown?**
→ [MVP Plan (Updated)](MVP_PLAN_UPDATED.md) или [Strategic Plan](STRATEGIC_PLAN.md)

**What changed recently?**
→ [Sprint 3 Changes Summary](SPRINT3_CHANGES_SUMMARY.md)

**Agent communication formats?**
→ [API Contracts](API_CONTRACTS.md)

**Overall project vision?**
→ [Strategic Plan](STRATEGIC_PLAN.md)

**Database setup instructions?**
→ [Sprint 3 Setup Guide](SPRINT3_SETUP_GUIDE.md)

**Game mechanics reference?**
→ [Sprint 2 Spec](SPRINT2_SPEC.md) + `app/game/` code

---

## 🚀 Quick Start Guide

### For PM:
```bash
1. Read MVP_PLAN_UPDATED.md (10 min) - Get big picture
2. Read SPRINT3_CHANGES_SUMMARY.md (5 min) - Understand recent changes
3. Give AI agent task from SPRINT3_UPDATED.md
```

### For AI Code Agent:
```bash
1. Read SPRINT3_UPDATED.md - Full implementation guide
2. Check API_CONTRACTS.md - Data formats
3. Implement tasks week-by-week from spec
4. Run tests: uv run pytest tests/
```

---

## 📝 Bug Fixes & Patches

- **[Enemy Damage Fix](BUGFIX_ENEMY_DAMAGE.md)** - Combat damage tracking
- **[JSON Output Fix](BUGFIX_JSON_OUTPUT.md)** - Response Synthesizer formatting
- **[Markdown Fix](MARKDOWN_FIX.md)** - Telegram Markdown parsing
- **[Halfvec Migration](HALFVEC_MIGRATION.md)** - Vector storage optimization
- **[CrewAI Changes](CHANGES_CREWAI.md)** - ⚠️ Deprecated (не используем в MVP)

---

## 💰 Cost Economics (Updated)

### Sprint 3 Target:
```
Cost per turn: ₽0.22
Monthly cost (100 users): ₽6,600
Monthly revenue (₽500 sub): ₽50,000
Gross margin: 87% 🎉
```

См. **[MVP Plan](MVP_PLAN_UPDATED.md)** для full breakdown.

---

## ✅ Current Sprint Status

**Sprint 3 Week-by-Week:**
- [ ] **Week 1:** Database setup (player_knowledge_confidence column)
- [ ] **Week 2:** Memory system (layered retrieval + smart storage)
- [ ] **Week 3:** Integration & testing

См. **[Sprint 3 Spec (Updated)](SPRINT3_UPDATED.md)** для деталей.

---

## 📞 Support

**Questions about architecture?**
→ Read [Strategic Plan](STRATEGIC_PLAN.md)

**Questions about current sprint?**
→ Read [Sprint 3 Spec (Updated)](SPRINT3_UPDATED.md)

**Questions about changes?**
→ Read [Sprint 3 Changes Summary](SPRINT3_CHANGES_SUMMARY.md)

**Questions about costs?**
→ Read [MVP Plan (Updated)](MVP_PLAN_UPDATED.md)

---

**Current Focus:** Sprint 3 Week 2 (Memory System Implementation)  
**Next Milestone:** End-to-end integration testing (Week 3)  
**Target Launch:** Sprint 4 completion + 1 week beta

**Start here:** [MVP Plan (Updated)](MVP_PLAN_UPDATED.md) 🚀

---

## 🗺️ Карта документации

### Для быстрого старта

| Документ | Когда читать | Время чтения |
|----------|-------------|--------------|
| **[STRATEGIC_PLAN.md](STRATEGIC_PLAN.md)** | Прямо сейчас | 30 мин |
| **[SPRINT2_SPEC.md](SPRINT2_SPEC.md)** | Перед началом Sprint 2 | 20 мин |

### Для разработки

| Документ | Когда читать | Для кого |
|----------|-------------|----------|
| **[SPRINT2_SPEC.md](SPRINT2_SPEC.md)** | Во время Sprint 2 | AI code agent + PM |
| **[API_CONTRACTS.md](API_CONTRACTS.md)** | При работе с агентами | AI code agent |
| **[development-plan.md](developent-plan.md)** | Reference (Sprint 1) | AI code agent |

### Для отслеживания прогресса

| Документ | Когда обновлять | Для кого |
|----------|----------------|----------|
| **[SPRINT1_CHECKLIST.md](SPRINT1_CHECKLIST.md)** | ✅ Завершен | PM |
| **SPRINT2_CHECKLIST.md** | 🔄 В процессе | PM |

---

## 📖 Описание документов

---

---

### 🎯 STRATEGIC_PLAN.md
**Главная "библия" проекта.** Глубокий анализ архитектуры и решений.

**Содержание:**
- ✅ Решение 3 главных проблем:
  - Долгосрочная память (RAG pipeline)
  - Архитектура суб-агентов (5 core agents)
  - Технологический стек (FastAPI + Aiogram + LangGraph)
- ✅ Мульти-агентная система с детальными спецификациями
- ✅ Roadmap на 3 месяца (Sprint 2-4)
- ✅ Cost optimization strategies
- ✅ Testing strategy

**Используй для:**
- Понимания "почему" за каждым решением
- Планирования следующих спринтов
- Reference при принятии архитектурных решений

---

### ⚙️ SPRINT2_SPEC.md
**Детальные задачи Sprint 2.** Пошаговые инструкции с кодом.

**Содержание:**
- Week 1: Game Mechanics (Character, Dice, Rules)
- Week 2: Agent System (5 agents + orchestrator)
- Week 3: Integration (Bot handlers + UI)

**Используй для:**
- Команд AI code agent (ссылайся на Task номера)
- Проверки что реализовано правильно
- Success criteria для каждой недели

**Пример команды:**
```
"Implement Task 1.1 from docs/SPRINT2_SPEC.md"
```

---

### 🔌 API_CONTRACTS.md
**Форматы данных между агентами.** Точные JSON схемы.

**Содержание:**
- Input/Output контракты для каждого агента
- Примеры данных
- Validation rules
- Response formatting guide

**Используй для:**
- Проверки что агенты возвращают правильные данные
- Debugging (когда что-то не работает)
- Reference при написании новых specs

---

### 📝 development-plan.md
**Sprint 1 legacy план.** Детальная спецификация первого спринта.

**Содержание:**
- Инициализация проекта с UV
- Структура проекта
- LLM client implementation
- FSM states
- Telegram handlers

**Используй для:**
- Reference если нужно понять как работает Sprint 1
- Обучающий материал для понимания структуры specs

**Статус:** ✅ Реализован полностью

---

### ✅ SPRINT1_CHECKLIST.md
**Чеклист Sprint 1.** Список выполненных задач.

**Содержание:**
- Инициализация проекта ✅
- Структура директорий ✅
- Configuration ✅
- LLM Client ✅
- FSM States ✅
- Telegram Handlers ✅
- Документация ✅

**Статус:** ✅ Все задачи завершены

---

## 🎯 Workflow для PM

### 1. **Планирование спринта**

Читай:
1. `STRATEGIC_PLAN.md` → понять цель спринта и архитектуру
2. `SPRINT2_SPEC.md` → увидеть конкретные задачи

### 2. **Разработка (каждый день)**

Используй:
1. `SPRINT2_SPEC.md` → выбрать Task и дать команду AI agent
2. `API_CONTRACTS.md` → если нужно проверить форматы

### 3. **Тестирование**

Команды:
1. `uv run start` → запустить бота
2. `uv run pytest tests/` → прогнать тесты
3. Проверь Success Criteria в `SPRINT2_SPEC.md`

### 4. **Troubleshooting**

Используй:
1. `STRATEGIC_PLAN.md` → понять "почему" за решениями
2. `API_CONTRACTS.md` → проверить контракты данных

---

## 🔄 Как документы связаны

```
STRATEGIC_PLAN.md (start here - understand "why")
        ↓
SPRINT2_SPEC.md (implement "what")
        ↓
API_CONTRACTS.md (verify "how")
```

---

## 📊 Roadmap документации

### Sprint 2 (текущий)
- ✅ STRATEGIC_PLAN.md
- ✅ SPRINT2_SPEC.md
- ✅ API_CONTRACTS.md
- ✅ QUICK_START_PM.md

### Sprint 3 (будущее)
- [ ] SPRINT3_SPEC.md — Memory system + CrewAI integration
- [ ] CREWAI_SETUP.md — Настройка CrewAI для GM system
- [ ] MEMORY_ARCHITECTURE.md — Детали RAG pipeline
- [ ] DATABASE_SCHEMA.md — Supabase schema

### Sprint 4 (будущее)
- [ ] SPRINT4_SPEC.md — Production optimization
- [ ] PRODUCTION_CHECKLIST.md — Pre-launch checklist
- [ ] MONITORING_GUIDE.md — Error tracking, metrics
- [ ] DEPLOYMENT_GUIDE.md — Deploy to Railway/Render

---

## 🎓 Learning Path для PM

**День 1:**
1. Прочитай STRATEGIC_PLAN.md (секции "Executive Summary" и "Решение трех проблем")
2. Запусти бота: `uv run start`
3. Протестируй текущий Sprint 1

**Неделя 1 (Sprint 2):**
1. Прочитай SPRINT2_SPEC.md Week 1
2. Дай команды AI agent для Tasks 1.1-1.3
3. Тестируй через `pytest`

**Неделя 2 (Sprint 2):**
1. Прочитай SPRINT2_SPEC.md Week 2
2. Изучи API_CONTRACTS.md для понимания агентов
3. Реализуй все 5 agents через AI agent

**Неделя 3 (Sprint 2):**
1. Прочитай SPRINT2_SPEC.md Week 3
2. Integration testing в Telegram
3. Sprint 2 completion! 🎉

---

## ❓ FAQ

**Q: С чего начать если я впервые в проекте?**
A: Читай `STRATEGIC_PLAN.md` → запускай бота (`uv run start`) → читай `SPRINT2_SPEC.md`

**Q: Какой документ давать AI code agent?**
A: Ссылайся на `SPRINT2_SPEC.md` с номером Task

**Q: Где искать примеры JSON форматов?**
A: В `API_CONTRACTS.md`

**Q: Как понять зачем нужна конкретная архитектура?**
A: Читай `STRATEGIC_PLAN.md` секцию про решение проблем

**Q: Где чеклист задач?**
A: `SPRINT1_CHECKLIST.md` (завершен), задачи Sprint 2 в `SPRINT2_SPEC.md`

**Q: Когда добавлять CrewAI?**
A: В Sprint 3. Sprint 2 используем простую sequential оркестрацию, CrewAI добавим вместе с Memory System.

---

## 📞 Поддержка

**Если что-то непонятно:**
1. Проверь `STRATEGIC_PLAN.md` для понимания архитектуры
2. Проверь `API_CONTRACTS.md` для форматов данных
3. Спроси AI agent: "Explain [концепт] from docs/STRATEGIC_PLAN.md"

**Если что-то не работает:**
1. Копируй полный текст ошибки
2. Дай команду AI agent: "Fix this error: [error text]. Check Task X.X in docs/SPRINT2_SPEC.md"
3. Прогони тесты: `uv run pytest tests/ -v`

---

## 🎯 Current Status

- ✅ **Sprint 1:** Completed
- 🔄 **Sprint 2:** In Progress
  - Week 1: Not started
  - Week 2: Not started
  - Week 3: Not started
- ⏳ **Sprint 3:** Planned (Memory + CrewAI)
- ⏳ **Sprint 4:** Planned (Production)

---

**Начни с [STRATEGIC_PLAN.md](STRATEGIC_PLAN.md)** 🚀

**Команды для быстрого старта:**
```bash
# Запуск бота
uv run start

# Тесты
uv run pytest tests/ -v

# Первая задача Sprint 2
# Дай AI agent: "Implement Task 1.1 from docs/SPRINT2_SPEC.md"
```
