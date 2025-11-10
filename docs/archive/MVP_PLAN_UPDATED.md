# MVP Implementation Plan (UPDATED)

> **Дата:** 7 ноября 2025 г.  
> **Статус:** Sprint 2 завершен, Sprint 3 в процессе  
> **Цель:** Cost-optimized AI Game Master с долгосрочной памятью

---

## 📍 Current Status

### ✅ Sprint 1: Basic Bot (COMPLETED)
- Telegram bot с Aiogram 3.x
- Базовая LLM интеграция через OpenRouter
- FSM state management
- Простые команды (/start, /help, /reset)

### ✅ Sprint 2: Multi-Agent System (COMPLETED)
- Rules Arbiter agent (механики, броски)
- Narrative Director agent (storytelling)
- Response Synthesizer agent (форматирование)
- Character sheet system
- Dice rolling (d4-d100)
- Basic combat mechanics

### 🔄 Sprint 3: Memory System (IN PROGRESS)
- **Новая архитектура:** Cost-optimized подход
- **Ключевые решения:**
  - LLM-based importance scoring (zero overhead)
  - Temporal ranking без session summaries
  - Confidence-based knowledge scoping
  - Simple orchestrator (no CrewAI в MVP)

---

## 🎯 Sprint 3 Roadmap (2-3 недели)

### Week 1: Database Foundation

**Цель:** Setup Supabase + оптимизированная schema

**Tasks:**
1. Create Supabase project
2. Apply migration with updated schema:
   - ✅ `player_knowledge_confidence` column (метагейминг prevention)
   - ❌ Remove `summary` from sessions (избыточно)
   - ✅ Indexes для temporal ranking
3. Setup database client (`app/db/supabase.py`)
4. Update Pydantic models

**Deliverables:**
- Supabase project online
- Migration 001 applied
- DB connection working

**Success Criteria:**
- Can connect to Supabase
- Can create/read test data
- pgvector extension enabled

---

### Week 2: Memory System

**Цель:** Layered retrieval + smart storage

**Tasks:**
1. Implement `app/memory/embeddings.py`:
   - Embeddings через OpenRouter
   - Batch support для efficiency
   
2. Implement `app/memory/retrieval.py`:
   - Layered retrieval (recent + important + semantic)
   - Temporal ranking formula
   - Confidence filtering (player vs GM scope)
   
3. Implement `app/memory/smart_storage.py`:
   - Smart memory creation
   - Importance-based filtering (skip <3)
   
4. Update `app/agents/response_synthesizer.py`:
   - Add metadata extraction to JSON output
   - Importance scoring instructions
   - Confidence scoring instructions
   
5. Implement Memory Manager agent:
   - No LLM calls (pure logic)
   - Layered retrieval integration

**Deliverables:**
- Memory system fully functional
- Metadata extraction working
- Layered retrieval <500ms

**Success Criteria:**
- Can create memories with metadata
- Can retrieve relevant memories
- Importance/confidence scores accurate
- Cost overhead <5%

---

### Week 3: Integration & Testing

**Цель:** End-to-end integration

**Tasks:**
1. Implement World State agent:
   - Track game state changes
   - Save to DB
   - NPC relationship tracking (structured)
   
2. Update bot handlers:
   - Use layered retrieval
   - Use smart storage
   - Auto session management
   
3. Testing:
   - Multi-session continuity
   - Knowledge scoping (GM secrets)
   - Cost per turn verification
   
4. Documentation:
   - Sprint 3 completion checklist
   - Cost analysis report

**Deliverables:**
- Full integration working
- All tests passing
- Documentation complete

**Success Criteria:**
- Bot remembers past sessions
- No metagaming (GM secrets filtered)
- Cost per turn ~₽0.22
- Latency <3 seconds

---

## 💰 Cost Analysis (Updated)

### Base Cost (Sprint 2):
```
Rules Arbiter:        $0.00003
Narrative Director:   $0.00120
Response Synthesizer: $0.00075
────────────────────────────────
TOTAL:                $0.00198 (~₽0.20)
```

### Sprint 3 Overhead:
```
Embeddings (query):    $0.00000 (negligible)
Synthesizer metadata:  $0.00015 (+100 tokens)
World State update:    $0.00002
────────────────────────────────
OVERHEAD:             $0.00017 (~₽0.02)
```

### Total Cost per Turn:
```
Base + Memory = $0.00215 (~₽0.22)
Overhead: 8.5% (отлично!)
```

### Monthly Economics:
```
Assumptions:
- 100 active users
- 10 turns/day average
- 30 days

Cost: 100 × 10 × 30 × ₽0.22 = ₽6,600/мес
Revenue (₽500 subscription): ₽50,000/мес
Margin: 87% 🎉
```

---

## 🚀 Next Steps (Sprint 4)

### Production Deployment
1. Redis для FSM persistence
2. Webhooks вместо polling
3. Deploy на Railway/Render
4. Monitoring (Sentry)

### Feature Enhancements
1. **NPC Relationship System:**
   ```python
   world_state = {
       "npc_relationships": {
           "Элдар": {
               "relationship": "враг",
               "trust": -5,
               "last_interaction": "предательство"
           }
       }
   }
   ```

2. **Quest System:**
   ```python
   world_state = {
       "active_quests": [
           {
               "id": "merchant_betrayal",
               "stage": "betrayal_reveal",
               "flexible_outcomes": True,
               "alternative_paths": ["forgive", "kill", "ignore"]
           }
       ]
   }
   ```

3. **Auto Checkpoint System:**
   - Каждые 50 turns → create high-importance checkpoint memory
   - После 24h inactivity → auto-close session

---

## 📊 Success Metrics

### Technical Metrics:
- [ ] Response time <3 seconds
- [ ] Memory retrieval <500ms
- [ ] RAG accuracy >85%
- [ ] Cost per turn <₽0.25
- [ ] Uptime >95%

### User Experience Metrics:
- [ ] Multi-session continuity works
- [ ] No metagaming spoilers
- [ ] Character progression saved
- [ ] Natural conversation flow

### Business Metrics:
- [ ] Cost per user per month <₽70
- [ ] Gross margin >80%
- [ ] Churn rate <20%/month

---

## 🔑 Key Architectural Decisions

### Decision 1: No Session Summaries
**Reason:** Избыточность при постоянном memory storage  
**Alternative:** Layered retrieval (recent + important + semantic)  
**Savings:** ~$0.001 per session

### Decision 2: LLM-based Importance Scoring
**Reason:** Русский язык — keyword heuristics не работают  
**Implementation:** Through Synthesizer (zero overhead)  
**Cost:** $0.00 (уже в базовом call)

### Decision 3: Confidence Scores vs Hard Tags
**Reason:** LLM errors с hard tags хрупки  
**Implementation:** 3-level probabilistic (1.0, 0.5, 0.0)  
**Benefit:** Graceful degradation при ошибках

### Decision 4: Simple Orchestrator (No CrewAI)
**Reason:** MVP не требует сложных workflows  
**Alternative:** Sequential execution  
**Migration Path:** CrewAI/LangGraph в v2.0

### Decision 5: Personal Worlds (No Shared)
**Reason:** Проще state management для MVP  
**Alternative:** Per-user world_state  
**Migration Path:** Shared world в v2.0

---

## 📚 Key Documents

### Implementation Guides:
- `docs/SPRINT3_UPDATED.md` - Детальная спецификация Sprint 3
- `docs/STRATEGIC_PLAN.md` - Общий архитектурный план
- `docs/API_CONTRACTS.md` - Agent communication contracts

### Code References:
- `app/memory/retrieval.py` - Layered memory retrieval
- `app/memory/smart_storage.py` - LLM-based filtering
- `app/agents/response_synthesizer.py` - Metadata extraction

### Testing:
- `tests/test_memory_integration.py` - End-to-end memory tests
- `scripts/test_conversation.py` - CLI testing tool

---

## 🎮 Future Enhancements (v2.0)

### Advanced Memory:
- Memory consolidation для 100+ session campaigns
- Entity relationship graphs
- Automatic conflict resolution

### Advanced Orchestration:
- CrewAI/LangGraph integration
- Parallel agent execution
- Cyclical workflows (planning → execution → reflection)

### Multiplayer:
- Shared world support
- Player-to-player interactions
- Synchronized events

### Monetization:
- Подписочная модель (₽500/мес)
- Pay-as-go (₽0.50/turn)
- Premium tier с GPT-4o для всех agents

---

## ✅ Sprint 3 Checklist

### Week 1:
- [ ] Supabase project created
- [ ] Migration 001 applied
- [ ] Database connection working
- [ ] Models updated

### Week 2:
- [ ] Embeddings service working
- [ ] Layered retrieval implemented
- [ ] Smart storage implemented
- [ ] Metadata extraction working
- [ ] Memory Manager agent done

### Week 3:
- [ ] World State agent done
- [ ] Bot handlers updated
- [ ] Multi-session continuity tested
- [ ] Knowledge scoping tested
- [ ] Cost verified <₽0.25/turn
- [ ] Documentation complete

---

## 🚦 Go/No-Go Criteria для Sprint 4

**GO если:**
- ✅ Multi-session continuity работает
- ✅ Cost per turn <₽0.25
- ✅ Memory retrieval <500ms
- ✅ No metagaming spoilers
- ✅ 5+ successful test sessions

**NO-GO если:**
- ❌ Cost >₽0.30/turn
- ❌ Retrieval latency >1 second
- ❌ Frequent metagaming leaks
- ❌ Data loss issues

---

**Current Focus:** Завершить Week 2 Sprint 3 (Memory System)  
**Next Milestone:** End-to-end integration testing (Week 3)  
**Target Launch:** Sprint 4 completion + 1 week beta testing

**Questions?** См. `docs/SPRINT3_UPDATED.md` или спроси AI agent.

**Ready to code?** Погнали! 🚀
