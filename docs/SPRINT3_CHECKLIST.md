# Sprint 3 Checklist: Memory System & Production Infrastructure

> **Quick reference** для отслеживания прогресса Sprint 3

---

## 📊 Sprint Overview

**Сроки:** 2-3 недели  
**Статус:** 🔄 In Progress (Started: 7 ноября 2025)  
**Главная цель:** Долгосрочная память + Database persistence + CrewAI

---

## Week 1: Database Setup & Infrastructure

### ✅ Prerequisites

- [✅] **Task 0.1:** Прочитать `SPRINT3_SPEC.md`
- [✅] **Task 0.2:** Убедиться что Sprint 2 завершен и работает
- [✅] **Task 0.3:** Backup текущего состояния проекта

---

### 🗄️ Database Setup

- [ ] **Task 1.1:** Supabase Project Setup
  - [ ] Создать Supabase account (если нет)
  - [ ] Создать новый project
  - [ ] Сохранить SUPABASE_URL, SUPABASE_KEY, SUPABASE_DB_URL
  - [ ] Добавить credentials в `.env`
  - ℹ️  **See `docs/SPRINT3_SETUP_GUIDE.md` for detailed instructions**
  
- [✅] **Task 1.2:** Install Dependencies
  ```bash
  uv add supabase asyncpg sqlalchemy pgvector httpx
  uv add --dev pytest-asyncio
  ```
  **Note**: OpenAI package НЕ нужен - embeddings через OpenRouter
  - [✅] asyncpg installed
  - [✅] httpx installed

- [✅] **Task 1.3:** Database Schema Migration
  - [✅] Создать `app/db/migrations/001_initial_schema.sql`
  - [✅] Создать `scripts/apply_migration.py`
  - [✅] Применить миграцию: `uv run python scripts/apply_migration.py`
  - [✅] Создать `app/db/migrations/002_switch_to_halfvec.sql` - переход на halfvec(2560)
  - [✅] Применить halfvec миграцию - использует fp16 вместо fp32
  - [✅] Проверить таблицы в Supabase dashboard
  - [✅] Проверить что pgvector extension установлен
  
- [✅] **Task 1.4:** Database Client & Models
  - [✅] Создать `app/db/__init__.py`
  - [✅] Создать `app/db/supabase.py` - Supabase client wrapper
  - [✅] Создать `app/db/models.py` - Pydantic models для DB entities
  - [✅] Обновить `app/config/__init__.py` - добавить Supabase settings (Pydantic v2)
  - [✅] Обновить `.env.example` с новыми переменными
  - [✅] Создать `scripts/check_sprint3_setup.py` - verification script
  - [✅] Протестировать config loading - ✅ PASSED

---

## Week 2: Memory System & Agents

### 🧠 Memory System

- [✅] **Task 2.1:** Embeddings Service
  - [✅] Создать `app/memory/__init__.py`
  - [✅] Создать `app/memory/embeddings.py` (uses OpenRouter API)
  - [✅] Протестировать embeddings generation
  - [✅] Переход на qwen/qwen3-embedding-4b (2560 dimensions)
  - [✅] Verify dimension = 2560 with halfvec (fp16 storage)
  - [✅] Fix API int/float type inconsistency

- [✅] **Task 2.2:** Episodic Memory Manager
  - [✅] Создать `app/memory/episodic.py`
  - [✅] Implement `create_memory()`
  - [✅] Implement `search_memories()` с vector search
  - [✅] Implement `get_recent_memories()`
  - [✅] Test vector search с sample data
  - [✅] Update for halfvec format

- [ ] **Task 2.3:** Memory Manager Agent
  - [ ] Создать `app/agents/memory_manager.py`
  - [ ] Implement `execute()` - RAG retrieval
  - [ ] Implement `_build_memory_summary()`
  - [ ] Unit test для agent

- [ ] **Task 2.4:** World State Agent
  - [ ] Создать `app/agents/world_state.py`
  - [ ] Implement `execute()` - update game state
  - [ ] Implement `_save_world_state()` - save to DB
  - [ ] Implement `load_world_state()` - load from DB
  - [ ] Test state persistence

---

### 🤖 CrewAI Integration

- [ ] **Task 2.5:** Install CrewAI
  ```bash
  uv add crewai crewai-tools
  ```

- [ ] **Task 2.6:** CrewAI Configuration
  - [ ] Создать `app/agents/crew_config.py`
  - [ ] Define CrewAI Agents (wrappers)
  - [ ] Define CrewAI Tasks
  - [ ] Create Crew с sequential process
  - [ ] Test basic crew execution

- [ ] **Task 2.7:** CrewAI Orchestrator
  - [ ] Создать `app/agents/crew_orchestrator.py`
  - [ ] Implement `process_action()` using CrewAI
  - [ ] Test vs old orchestrator (compare outputs)
  
**NOTE:** CrewAI integration опциональна для MVP. Можно оставить простой orchestrator до Sprint 4.

---

## Week 3: Integration & Polish

### 💾 Persistence

- [ ] **Task 3.1:** Character Persistence
  - [ ] Создать `app/db/characters.py`
  - [ ] Implement `create_or_update_character()`
  - [ ] Implement `get_character_by_telegram_id()`
  - [ ] Test CRUD operations

- [ ] **Task 3.2:** Session Management
  - [ ] Создать `app/db/sessions.py`
  - [ ] Implement `start_session()`
  - [ ] Implement `end_session()` с LLM summary
  - [ ] Implement `_generate_session_summary()`
  - [ ] Test session lifecycle

- [ ] **Task 3.3:** Update Bot Handlers
  - [ ] Обновить `app/bot/handlers.py`
  - [ ] Load character from DB вместо FSM
  - [ ] Save character to DB after each turn
  - [ ] Create memory after each turn
  - [ ] Start/end sessions properly
  - [ ] Load world state from DB

---

### 🔧 Advanced Features

- [ ] **Task 3.4:** Chunking & Importance Scoring
  - [ ] Создать `app/memory/chunking.py`
  - [ ] Implement `chunk_by_turns()`
  - [ ] Implement importance scoring (optional, can use default=5)

- [ ] **Task 3.5:** Semantic Memories (World Lore)
  - [ ] Verify sample lore в database (from migration)
  - [ ] Test semantic memory search
  - [ ] (Optional) Add more lore entries

---

### 🧪 Testing

- [ ] **Task 3.6:** Memory System Tests
  - [ ] Создать `tests/test_memory.py`
  - [ ] Test embeddings generation
  - [ ] Test memory creation
  - [ ] Test memory search (vector similarity)
  - [ ] Test recent memories retrieval

- [ ] **Task 3.7:** Integration Tests
  - [ ] Создать `tests/test_integration_sprint3.py`
  - [ ] Test full flow: action → memory retrieval → response → save
  - [ ] Test multi-session continuity
  - [ ] Test character persistence across restarts

- [ ] **Task 3.8:** Run All Tests
  ```bash
  uv run pytest tests/ -v
  uv run pytest tests/test_memory.py -v --cov=app/memory
  ```

---

### 📝 Documentation

- [ ] **Task 3.9:** Update Documentation
  - [ ] Update `README.md` - добавить Sprint 3 features
  - [ ] Update `STRATEGIC_PLAN.md` - отметить Sprint 3 завершенным
  - [ ] Создать `docs/MEMORY_SYSTEM.md` - документация memory architecture

---

## 🎯 Success Criteria

### Обязательные (Must Have)

- [ ] ✅ **Database работает:**
  - [ ] Все таблицы созданы
  - [ ] pgvector extension установлен
  - [ ] Можно писать и читать данные

- [ ] ✅ **Memory System работает:**
  - [ ] Embeddings генерируются
  - [ ] Vector search возвращает релевантные результаты
  - [ ] Latency <500ms для retrieval
  
- [ ] ✅ **Persistence работает:**
  - [ ] Characters сохраняются в DB
  - [ ] World state сохраняется
  - [ ] Sessions создаются и завершаются
  
- [ ] ✅ **Multi-session continuity:**
  - [ ] Бот помнит события из прошлых сессий
  - [ ] Memory Manager извлекает релевантный контекст
  - [ ] Context качественный (subjective evaluation)

### Опциональные (Nice to Have)

- [ ] 🌟 **CrewAI integration:**
  - [ ] Agents работают через CrewAI
  - [ ] Workflow стабильный
  
- [ ] 🌟 **Advanced features:**
  - [ ] Importance scoring работает
  - [ ] Chunking оптимизирован
  - [ ] Semantic memories используются

---

## 🚨 Troubleshooting

### Database Issues

**Problem:** Migration fails  
**Solution:** Check Supabase connection string, verify pgvector extension

**Problem:** Vector search не работает  
**Solution:** Verify index created: `CREATE INDEX ... USING ivfflat`

### Memory Issues

**Problem:** Embeddings API fails  
**Solution:** Check OPENAI_API_KEY, verify API quota

**Problem:** Search latency >500ms  
**Solution:** Add more indexes, reduce top_k, optimize query

### Integration Issues

**Problem:** CrewAI слишком сложен  
**Solution:** Fallback to simple orchestrator, migrate в Sprint 4

---

## 📊 Metrics to Track

### Performance

- [ ] Memory retrieval latency: **Target <500ms**
- [ ] Memory search accuracy: **Target >85%**
- [ ] Database query time: **Target <100ms**

### Cost

- [ ] Embeddings cost per turn: **~$0.00001**
- [ ] Total cost per turn: **~$0.01** (не должно сильно вырасти)
- [ ] Database storage: **Monitor в Supabase dashboard**

### Quality

- [ ] Memory relevance (subjective): **Good/Bad rating**
- [ ] Multi-session continuity: **Does bot remember?**
- [ ] Context quality: **Is retrieved context helpful?**

---

## 🎓 Learning Resources

### Supabase
- [Supabase Docs](https://supabase.com/docs)
- [pgvector Guide](https://supabase.com/docs/guides/ai/vector-search)

### Vector Embeddings
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Understanding Vector Search](https://www.pinecone.io/learn/vector-search/)

### CrewAI
- [CrewAI Documentation](https://docs.crewai.com/)
- [CrewAI Examples](https://github.com/joaomdmoura/crewAI-examples)

---

## 🔄 Migration from FSM to DB

### Current (Sprint 2):
```
Character → FSM context
Game State → FSM context
History → FSM context (последние 20 сообщений)
```

### After Sprint 3:
```
Character → PostgreSQL (persistent)
Game State → PostgreSQL (persistent)
History → Episodic Memories (all history, chunked)
Session → FSM context (только session_id)
```

### Migration Steps:
1. Load character from DB в начале conversation
2. Save character to DB после каждого хода
3. Create memory после каждого ответа
4. Keep session_id в FSM для tracking

---

## ✅ Final Checklist

Before marking Sprint 3 complete:

- [ ] Все tests проходят
- [ ] Бот запускается без ошибок
- [ ] Database connection стабильна
- [ ] Memory system работает
- [ ] Multi-session tested manually
- [ ] Documentation обновлена
- [ ] Code committed to git
- [ ] Sprint review проведен

---

**Status Legend:**
- ⏳ Not Started
- 🔄 In Progress  
- ✅ Completed
- ❌ Blocked
- 🌟 Optional

**Last Updated:** (дата начала Sprint 3)
