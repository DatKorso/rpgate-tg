# Изменения: Переход на CrewAI

> **Дата:** 6 ноября 2025  
> **Причина:** Для MVP проект слишком мал для LangGraph, CrewAI позволит быстрее создать прототип

---

## 🔄 Что изменилось

### Основное решение

**Было:** LangGraph для agent orchestration  
**Стало:** CrewAI для agent orchestration

**Обоснование:**
- ✅ CrewAI быстрее в setup (<1 час vs несколько часов для LangGraph)
- ✅ Проще для прототипа (декларативная конфигурация)
- ✅ Достаточно для sequential и simple parallel workflows MVP
- ✅ Меньше boilerplate кода
- ✅ Built-in role-based agents (идеально для GM концепта)
- ✅ Хорошая интеграция с OpenRouter

**Migration path:** 
- Если в будущем понадобятся циклические workflows или более сложная оркестрация — можно мигрировать на LangGraph в Sprint 4+

---

## 📝 Обновленные документы

### 1. STRATEGIC_PLAN.md
**Секция "Технологический стек":**
- ✅ Заменен LangGraph на CrewAI
- ✅ Добавлено обоснование выбора CrewAI для MVP
- ✅ Указано что LangGraph опционален для future optimization

**Секция "Sprint 3":**
- ✅ Переименован в "Memory System + CrewAI Integration"
- ✅ Добавлена Week 1: Install CrewAI
- ✅ Добавлена Week 2: Convert agents to CrewAI format
- ✅ Добавлена Week 3: Create CrewAI Crew configuration

**Секция "Sprint 4":**
- ✅ Убрана "LangGraph orchestration"
- ✅ Добавлена "Production-grade CrewAI configuration"
- ✅ Добавлен optional пункт: "Migrate to LangGraph if needed"

**Секция "Ресурсы":**
- ✅ Заменена ссылка на LangGraph Docs → CrewAI Docs

---

### 2. SPRINT2_SPEC.md
**Task 2.5 (Agent Orchestrator):**
- ✅ Добавлено примечание: "Simple sequential orchestrator (без CrewAI пока)"
- ✅ Указано что CrewAI добавим в Sprint 3

**Week 2 checklist:**
- ✅ Обновлено описание: "Simple sequential orchestrator (без CrewAI пока)"

---

### 3. API_CONTRACTS.md
**Version History:**
- ✅ v1.1: Изменено "LangGraph state contracts" → "CrewAI integration"
- ✅ v1.2: Изменено на "Production optimization contracts"

---

### 4. README.md (docs/)
**Для быстрого старта:**
- ✅ Удалена ссылка на QUICK_START_PM.md (файл удален по решению PM)
- ✅ STRATEGIC_PLAN.md теперь первый документ для чтения

**Workflow для PM:**
- ✅ Упрощен без ссылок на QUICK_START_PM.md
- ✅ Добавлены прямые команды (`uv run start`, `uv run pytest`)

**Roadmap документации:**
- ✅ Sprint 3: Добавлен CREWAI_SETUP.md
- ✅ Sprint 4: Убраны упоминания LangGraph

**Learning Path:**
- ✅ Обновлен под новую структуру без QUICK_START_PM.md
- ✅ Добавлен FAQ: "Когда добавлять CrewAI?"

---

### 5. README.md (корневой)
**Documentation:**
- ✅ Убрана ссылка на QUICK_START_PM.md
- ✅ STRATEGIC_PLAN.md теперь с пометкой "start here! 🚀"

**Sprint 3:**
- ✅ Переименован в "Memory System + CrewAI"
- ✅ Добавлена цель: "CrewAI integration for production-grade orchestration"

**Sprint 4:**
- ✅ Убрана "LangGraph orchestration"
- ✅ Добавлена "Production-optimized CrewAI configuration"

---

## 🎯 Новый Roadmap

### Sprint 2 (текущий) - 2-3 недели
**Цель:** Multi-agent system с **простой sequential оркестрацией**

**Deliverables:**
- ✅ 3 core agents (Rules Arbiter, Narrative Director, Response Synthesizer)
- ✅ Game mechanics (d20 system)
- ✅ Character creation
- ✅ Simple orchestrator **БЕЗ CrewAI** (чистый Python)

---

### Sprint 3 (следующий) - 2-3 недели
**Цель:** Memory System + **CrewAI Integration**

**Deliverables:**
- ✅ Long-term memory (RAG pipeline)
- ✅ Supabase + pgvector
- ✅ Memory Manager agent
- ✅ World State agent
- ✅ **Migrate to CrewAI** for orchestration
- ✅ Convert agents to CrewAI format (@agent decorators)
- ✅ Create CrewAI Crew configuration

**Новые задачи:**
1. Install CrewAI: `uv add crewai crewai-tools`
2. Convert existing agents to CrewAI format
3. Create `app/agents/crew.py` with Crew configuration
4. Test CrewAI workflow

---

### Sprint 4 (финал) - 1-2 недели
**Цель:** Production Ready

**Deliverables:**
- ✅ Production-optimized CrewAI config
- ✅ Redis for FSM
- ✅ Webhooks
- ✅ Deploy
- ✅ Monitoring

**Optional:**
- [ ] Migrate to LangGraph (только если нужны сложные циклические workflows)

---

## 🚀 Для AI Code Agent

### Sprint 2: БЕЗ изменений
- Продолжаем реализовывать Tasks 1.1-3.2 из SPRINT2_SPEC.md
- Orchestrator остается простым Python классом (без фреймворков)

### Sprint 3: Новые задачи

**После реализации Memory Manager:**

```bash
# Install CrewAI
uv add crewai crewai-tools
```

**Convert agents to CrewAI format:**

Пример для Rules Arbiter:

```python
from crewai import Agent, Task

rules_arbiter = Agent(
    role="Rules Arbiter",
    goal="Resolve game mechanics and dice rolls accurately",
    backstory="You are an experienced D&D referee who knows all the rules...",
    verbose=True,
    allow_delegation=False
)

def create_rules_task(user_action: str, character: CharacterSheet) -> Task:
    return Task(
        description=f"Resolve action: {user_action}",
        agent=rules_arbiter,
        expected_output="JSON with mechanics result"
    )
```

**Create Crew:**

```python
from crewai import Crew, Process

gm_crew = Crew(
    agents=[memory_manager, rules_arbiter, narrative_director, response_synthesizer],
    tasks=[memory_task, rules_task, narrative_task, synthesis_task],
    process=Process.sequential,  # Sequential execution
    verbose=True
)

# Execute
result = gm_crew.kickoff()
```

---

## 📊 Comparison: CrewAI vs LangGraph для нашего проекта

| Критерий | CrewAI | LangGraph |
|----------|--------|-----------|
| **Setup time** | <1 час | 2-4 часа |
| **Learning curve** | Легко (декларативный) | Средне (граф-структура) |
| **Sequential workflows** | ✅ Отлично | ✅ Отлично |
| **Parallel workflows** | ✅ Поддерживается | ✅ Отлично |
| **Циклические workflows** | ❌ Ограничено | ✅ Нативно |
| **State persistence** | ✅ Встроенная | ✅ Checkpointing |
| **Observability** | ✅ Хорошая | ✅ Отличная (LangSmith) |
| **Подходит для MVP** | ✅ ДА | ⚠️ Overkill |

**Вывод для нашего случая:**
- Sprint 2-3: CrewAI идеален ✅
- Sprint 4+: Если нужны сложные циклы → можно мигрировать на LangGraph

---

## ✅ Action Items для PM

### Сейчас (Sprint 2):
- ✅ Ничего не меняется
- ✅ Продолжай development по SPRINT2_SPEC.md
- ✅ Simple orchestrator в Task 2.5

### Перед Sprint 3:
- [ ] Прочитай CrewAI Docs: https://docs.crewai.com/
- [ ] Посмотри примеры CrewAI workflows
- [ ] Подготовь game lore для semantic memory

### Во время Sprint 3:
- [ ] Команда для AI agent: "Install CrewAI and convert agents to CrewAI format"
- [ ] Тестируй CrewAI workflow через Telegram
- [ ] Проверь что latency не увеличилась

---

## 📚 Ресурсы

**CrewAI:**
- [Official Docs](https://docs.crewai.com/)
- [GitHub Examples](https://github.com/joaomdmoura/crewAI-examples)
- [CrewAI + OpenRouter Guide](https://docs.crewai.com/how-to/llm-connections/)

**Migration (если понадобится):**
- [CrewAI → LangGraph Migration Guide](https://python.langchain.com/docs/langgraph)

---

**Документация обновлена. Готов к Sprint 2!** 🚀
