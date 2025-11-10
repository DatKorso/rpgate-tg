# Sprint 3 Specification (UPDATED): Cost-Optimized Memory System

> **Обновлено:** 7 ноября 2025 г.  
> **Изменения:** Учтены решения по 3 критическим проблемам - LLM-based importance scoring, temporal ranking без session summaries, confidence-based knowledge scoping

---

## 📋 Sprint Overview

**Цель:** Реализовать долгосрочную память (RAG) с оптимизацией затрат, добавить persistence через Supabase, интегрировать Memory Manager и World State агентов.

**Timeframe:** 2-3 недели

**Success Criteria:**
- ✅ Бот помнит события из прошлых сессий (multi-session continuity)
- ✅ Memory retrieval работает быстро (<500ms) и точно (>85% accuracy)
- ✅ World State Agent корректно обновляет game state
- ✅ Memory Manager Agent извлекает релевантный контекст
- ✅ Данные персонажей сохраняются в PostgreSQL
- ✅ **LLM-based importance scoring** (zero overhead через Synthesizer)
- ✅ **Confidence-based knowledge scoping** (метагейминг prevention)
- ✅ **Temporal ranking** для бесшовных сессий (no session summaries)
- ✅ **Cost per turn <$0.0025** (5% overhead от базового)

---

## 🎯 Архитектурные изменения Sprint 3

### До Sprint 3 (текущее состояние):
```
User Input → Rules Arbiter → Narrative Director → Response Synthesizer
                ↓                   ↓                      ↓
            Character         Game State            Final Message
             (FSM)             (FSM)                (Telegram)
```

### После Sprint 3 (оптимизированная архитектура):
```
User Input
    ↓
Memory Manager Agent (Layered retrieval: recent + important + semantic)
    ↓
[Simple Sequential Orchestration]
    ↓
Rules Arbiter ──┐
                ├─→ World State Agent → Update DB
Narrative ──────┘        ↓
                Response Synthesizer (+ metadata extraction в JSON)
                        ↓
                  Final Message
                        ↓
                  Smart Memory Storage (importance + confidence filtering)
```

**Ключевые изменения:**
1. **Layered Memory Retrieval** - recent + important + semantic в одном проходе
2. **Zero-overhead metadata** - Synthesizer генерирует importance/confidence в существующем JSON
3. **No session summaries** - temporal ranking вместо явных session boundaries
4. **Confidence-based scoping** - 3-level system (1.0, 0.5, 0.0) для метагейминг prevention
5. **Simple orchestrator** - без CrewAI для MVP (проще, дешевле, быстрее)

---

## 🔑 Решение критических проблем

### Problem 1: Importance Scoring (русский язык)

**❌ НЕ используем:** Keyword heuristics (не работают для русского из-за морфологии)

**✅ Используем:** LLM-based scoring через Response Synthesizer (zero overhead)

**Implementation:**

```python
# В Response Synthesizer prompt добавляем:

system_prompt = """...(existing prompt)...

ОБЯЗАТЕЛЬНО верни JSON с метаданными для сохранения памяти:
{
  "final_message": "...",
  "memory_metadata": {
    "importance_score": 0-10,  // 0-2: trivial, 3-5: normal, 6-8: important, 9-10: critical
    "player_knowledge_confidence": 0.0-1.0,  // 1.0: knows, 0.5: unclear, 0.0: GM secret
    "key_entities": ["NPC names", "locations"],
    "memory_type": "event|dialogue|discovery|combat"
  }
}

Критерии importance:
- 9-10: Boss fights, plot twists, character death, major discoveries
- 6-8: Quest получение/completion, NPC betrayals, significant loot
- 3-5: Normal combat, dialogue, movement
- 0-2: Trivial actions, simple observations
"""
```

**Cost:** $0.00 (уже в базовом Synthesizer call)

---

### Problem 2: Session Summaries (избыточность)

**❌ НЕ используем:** Session summaries (дублирование + extra LLM calls)

**✅ Используем:** Layered retrieval + temporal ranking

**Implementation:**

```python
async def get_context_for_turn(character_id: UUID, query: str) -> str:
    """
    Single-pass memory retrieval без session summaries.
    
    Layers:
    1. Recent (last 10 memories) - для immediate continuity
    2. Important (importance >= 7) - для key plot points
    3. Semantic (vector search) - для specific context
    """
    
    # Layer 1: Recent (cheap SQL, no vectors)
    recent = await episodic_memory.get_recent_memories(
        character_id=character_id,
        limit=10
    )
    
    # Layer 2+3: Important + Semantic combined (one vector search)
    relevant = await episodic_memory.search_with_temporal_ranking(
        character_id=character_id,
        query_text=query,
        top_k=5,
        min_importance=6,
        recency_weight=0.3  # 70% semantic similarity, 30% recency
    )
    
    # Deduplicate by ID
    all_memories = deduplicate_by_id(recent + relevant)
    
    # Build context string
    return build_memory_context(all_memories)
```

**Temporal Ranking Formula:**

```python
# В search_with_temporal_ranking():

final_score = (
    semantic_similarity * 0.7 +
    recency_score * 0.3
)

# recency_score = 1.0 для today, 0.0 для 30+ days ago
recency_score = max(0, 1 - (days_since_creation / 30))
```

**Benefits:**
- Старые важные события (importance=9) всплывают через high importance
- Недавние средние события (importance=5) всплывают через recency
- Нет LLM calls для summaries
- Бесшовная игра - нет явных session boundaries

---

### Problem 3: Knowledge Scoping (метагейминг)

**❌ НЕ используем:** Hard metadata tagging (хрупко, ошибки LLM)

**✅ Используем:** Probabilistic confidence scores (3 levels)

**Implementation:**

```python
# В Response Synthesizer instructions:

"""
player_knowledge_confidence:
- 1.0: Персонаж точно знает (observed directly, told by NPC)
- 0.5: Неопределенно (rumor, inference, вероятно знает)
- 0.0: GM secret (персонаж не может знать)

Примеры:
- "Игрок встретил торговца" → 1.0 (знает)
- "Торговец выглядит нервным" → 1.0 (observed)
- "В пещере может быть опасно" → 0.5 (предположение)
- "В пещере засада из 5 гоблинов" → 0.0 (GM secret, не знает)
"""
```

**Retrieval filtering:**

```python
# Для player-facing responses
memories = await search_memories(
    query=query,
    min_confidence=0.5  # Только то, что персонаж знает/предполагает
)

# Для GM narrative generation
all_memories = await search_memories(
    query=query,
    min_confidence=0.0  # Всё, включая secrets
)
```

**Fallback если LLM ошибся:**

```python
# Conservative default
confidence = parsed_json.get("player_knowledge_confidence", 1.0)

# Assume player knows by default (безопаснее чем спойлеры)
```

**Benefits:**
- Soft filtering - если LLM ошибся с 0.9 вместо 1.0, не критично
- Temporal ranking со временем исправит важность
- Нет double-check LLM calls

---

## Week 1: Database Setup

### Task 1.1: Updated Database Schema

**File:** `app/db/migrations/001_initial_schema.sql`

**Key changes:**
- ✅ Add `player_knowledge_confidence` column
- ❌ Remove `summary` from game_sessions
- ✅ Add indexes for temporal ranking

```sql
-- ============================================
-- TABLE: episodic_memories (UPDATED)
-- ============================================
CREATE TABLE episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    session_id UUID REFERENCES game_sessions(id) ON DELETE SET NULL,
    
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    
    memory_type VARCHAR(50) DEFAULT 'event',
    importance_score INT DEFAULT 5 CHECK (importance_score >= 0 AND importance_score <= 10),
    
    -- 🆕 Knowledge scoping для метагейминг prevention
    player_knowledge_confidence FLOAT DEFAULT 1.0 
        CHECK (player_knowledge_confidence >= 0.0 AND player_knowledge_confidence <= 1.0),
    
    entities TEXT[],
    location VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(id),
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES game_sessions(id)
);

-- Indexes для layered retrieval
CREATE INDEX idx_memories_character_id ON episodic_memories(character_id);
CREATE INDEX idx_memories_created_at ON episodic_memories(created_at DESC);
CREATE INDEX idx_memories_importance ON episodic_memories(importance_score DESC);
CREATE INDEX idx_memories_confidence ON episodic_memories(player_knowledge_confidence DESC);

-- Vector index
CREATE INDEX idx_memories_embedding ON episodic_memories 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- ============================================
-- TABLE: game_sessions (SIMPLIFIED)
-- ============================================
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- ❌ summary удален - избыточен при layered retrieval
    
    turns_count INT DEFAULT 0,
    total_damage_dealt INT DEFAULT 0,
    total_damage_taken INT DEFAULT 0,
    
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

---

## Week 2: Memory System Implementation

### Task 2.1: Layered Memory Retrieval

**File:** `app/memory/retrieval.py`

```python
"""Optimized memory retrieval with layered approach."""
from typing import List, Dict
from uuid import UUID
import asyncpg
from app.config import settings
from app.memory.embeddings import embeddings_service
import logging

logger = logging.getLogger(__name__)


class MemoryRetrieval:
    """Layered memory retrieval system."""
    
    def __init__(self):
        self.db_url = settings.SUPABASE_DB_URL
    
    async def get_context_for_turn(
        self,
        character_id: UUID,
        query: str,
        scope: str = "player"  # "player" or "gm"
    ) -> List[Dict]:
        """
        Get memory context using layered retrieval.
        
        Layers:
        1. Recent (last 10 memories)
        2. Important (importance >= 7, any age)
        3. Semantic (vector search, top 5)
        
        Args:
            character_id: UUID of character
            query: Current action/query
            scope: "player" (filter GM secrets) or "gm" (all memories)
            
        Returns:
            List of memories, deduplicated and sorted by relevance
        """
        
        # Step 1: Get recent memories (cheap SQL)
        recent = await self._get_recent_layer(character_id, limit=10, scope=scope)
        
        # Step 2: Get important + semantic in one pass
        important_and_semantic = await self._get_important_semantic_layer(
            character_id=character_id,
            query=query,
            top_k=5,
            min_importance=6,
            recency_weight=0.3,
            scope=scope
        )
        
        # Step 3: Deduplicate and combine
        all_memories = self._deduplicate(recent + important_and_semantic)
        
        logger.info(f"Retrieved {len(all_memories)} memories for context")
        
        return all_memories
    
    async def _get_recent_layer(
        self,
        character_id: UUID,
        limit: int,
        scope: str
    ) -> List[Dict]:
        """Layer 1: Recent memories."""
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Confidence filter based on scope
            min_confidence = 0.5 if scope == "player" else 0.0
            
            sql = """
                SELECT id, content, memory_type, importance_score,
                       player_knowledge_confidence, entities, location, created_at
                FROM episodic_memories
                WHERE character_id = $1
                  AND player_knowledge_confidence >= $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            
            rows = await conn.fetch(sql, character_id, min_confidence, limit)
            return [dict(row) for row in rows]
            
        finally:
            await conn.close()
    
    async def _get_important_semantic_layer(
        self,
        character_id: UUID,
        query: str,
        top_k: int,
        min_importance: int,
        recency_weight: float,
        scope: str
    ) -> List[Dict]:
        """
        Layer 2+3: Important events + Semantic search with temporal ranking.
        
        Combined in one query for efficiency.
        """
        
        # Generate query embedding
        query_embedding = await embeddings_service.embed_text(query)
        
        conn = await asyncpg.connect(self.db_url)
        
        try:
            min_confidence = 0.5 if scope == "player" else 0.0
            
            sql = """
                SELECT 
                    id, content, memory_type, importance_score,
                    player_knowledge_confidence, entities, location, created_at,
                    
                    -- Semantic similarity
                    1 - (embedding <=> $2::vector) as semantic_similarity,
                    
                    -- Recency score (1.0 = today, 0.0 = 30+ days ago)
                    GREATEST(0, 1 - (EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0 / 30)) as recency_score,
                    
                    -- Combined score
                    (1 - (embedding <=> $2::vector)) * $4 + 
                    GREATEST(0, 1 - (EXTRACT(EPOCH FROM (NOW() - created_at)) / 86400.0 / 30)) * $5
                    as final_score
                    
                FROM episodic_memories
                WHERE character_id = $1
                  AND importance_score >= $3
                  AND player_knowledge_confidence >= $6
                ORDER BY final_score DESC
                LIMIT $7
            """
            
            rows = await conn.fetch(
                sql,
                character_id,
                query_embedding,
                min_importance,
                1.0 - recency_weight,  # semantic weight
                recency_weight,         # recency weight
                min_confidence,
                top_k
            )
            
            return [dict(row) for row in rows]
            
        finally:
            await conn.close()
    
    def _deduplicate(self, memories: List[Dict]) -> List[Dict]:
        """Remove duplicates by ID, keep first occurrence."""
        seen = set()
        unique = []
        
        for mem in memories:
            if mem['id'] not in seen:
                seen.add(mem['id'])
                unique.append(mem)
        
        return unique


# Global instance
memory_retrieval = MemoryRetrieval()
```

---

### Task 2.2: Smart Memory Creation

**File:** `app/memory/smart_storage.py`

```python
"""Smart memory storage with LLM-based filtering."""
from typing import Optional, Dict
from uuid import UUID
from app.memory.episodic import episodic_memory
import logging

logger = logging.getLogger(__name__)


async def create_smart_memory(
    character_id: UUID,
    session_id: Optional[UUID],
    user_action: str,
    gm_response: str,
    metadata: Dict,
    location: Optional[str] = None
) -> Optional[UUID]:
    """
    Create memory with smart filtering based on Synthesizer metadata.
    
    Args:
        character_id: Character UUID
        session_id: Session UUID
        user_action: Player's action
        gm_response: GM's response
        metadata: Metadata from Response Synthesizer:
            {
                "importance_score": 0-10,
                "player_knowledge_confidence": 0.0-1.0,
                "key_entities": ["entity1", "entity2"],
                "memory_type": "event|dialogue|discovery|combat"
            }
        location: Current location
        
    Returns:
        Created memory UUID or None if filtered out
    """
    
    importance = metadata.get("importance_score", 5)
    confidence = metadata.get("player_knowledge_confidence", 1.0)
    entities = metadata.get("key_entities", [])
    memory_type = metadata.get("memory_type", "event")
    
    # Filter: Don't store trivial memories
    if importance < 3:
        logger.info(f"Skipping low-importance memory (score={importance})")
        return None
    
    # Build content
    content = f"Player: {user_action}\nGM: {gm_response[:200]}"
    
    # Create memory
    memory_id = await episodic_memory.create_memory(
        character_id=character_id,
        session_id=session_id,
        content=content,
        memory_type=memory_type,
        importance_score=importance,
        player_knowledge_confidence=confidence,
        entities=entities,
        location=location
    )
    
    logger.info(
        f"Created memory {memory_id}: importance={importance}, "
        f"confidence={confidence}, type={memory_type}"
    )
    
    return memory_id
```

---

### Task 2.3: Updated Response Synthesizer

**File:** `app/agents/response_synthesizer.py` (UPDATE)

Add metadata extraction to existing prompt:

```python
class ResponseSynthesizerAgent(BaseAgent):
    """..."""
    
    def __init__(self):
        super().__init__(
            name="ResponseSynthesizer",
            model="gpt-4o",
            temperature=0.3
        )
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """..."""
        
        system_prompt = """Ты — финальный редактор ответов GM.

Твоя задача:
1. Объединить mechanics result и narrative description
2. Отформатировать красиво с эмодзи и Markdown
3. 🆕 ДОБАВИТЬ METADATA для сохранения памяти

Верни JSON:
{
  "final_message": "formatted message",
  "memory_metadata": {
    "importance_score": 0-10,
    "player_knowledge_confidence": 0.0-1.0,
    "key_entities": ["entity names"],
    "memory_type": "event|dialogue|discovery|combat"
  }
}

КРИТЕРИИ IMPORTANCE:
- 9-10: Boss fights, plot twists, character death, major quest milestones
- 6-8: Quest start/end, NPC betrayals, significant combat, major discoveries
- 3-5: Normal combat, dialogue with NPCs, exploration, minor loot
- 0-2: Trivial actions (осмотреться, пойти вперед), simple observations

КРИТЕРИИ CONFIDENCE:
- 1.0: Персонаж observed/heard directly, told by NPC, общеизвестные факты
- 0.5: Rumor, inference, предположения, неявная информация
- 0.0: GM secret, персонаж не может знать (засады, планы врагов, будущее)

KEY_ENTITIES: Извлеки имена NPC, локации, важные предметы из action/response
"""
        
        # ... (existing execution logic)
        
        # Parse response
        try:
            response_data = json.loads(llm_response)
            
            # Validate metadata structure
            if "memory_metadata" not in response_data:
                # Fallback to safe defaults
                response_data["memory_metadata"] = {
                    "importance_score": 5,
                    "player_knowledge_confidence": 1.0,
                    "key_entities": [],
                    "memory_type": "event"
                }
        except json.JSONDecodeError:
            logger.error("Failed to parse Synthesizer JSON, using defaults")
            response_data = {
                "final_message": llm_response,
                "memory_metadata": {
                    "importance_score": 5,
                    "player_knowledge_confidence": 1.0,
                    "key_entities": [],
                    "memory_type": "event"
                }
            }
        
        return response_data
```

---

## Week 3: Integration & Testing

### Task 3.1: Update Bot Handlers

**File:** `app/bot/handlers.py` (UPDATE)

```python
from app.memory.retrieval import memory_retrieval
from app.memory.smart_storage import create_smart_memory

@router.message(ConversationState.in_conversation, F.text)
async def handle_conversation(message: Message, state: FSMContext):
    """Main conversation handler with optimized memory."""
    
    user_message = message.text
    telegram_user_id = message.from_user.id
    
    # Load character from DB
    character = await character_repo.get_character_by_telegram_id(telegram_user_id)
    
    if not character:
        await message.answer("❌ Персонаж не найден. Используй /start")
        return
    
    # Get world state
    game_state = await world_state_agent.load_world_state(character.id)
    
    # Get/create session
    data = await state.get_data()
    session_id = data.get("session_id")
    
    if not session_id:
        session_id = await session_manager.start_session(character.id)
        await state.update_data(session_id=session_id)
    
    # 🆕 Layered memory retrieval
    memories = await memory_retrieval.get_context_for_turn(
        character_id=character.id,
        query=user_message,
        scope="player"  # Filter GM secrets
    )
    
    # Typing indicator
    typing_task = asyncio.create_task(_send_typing_indicator(message))
    
    try:
        # Process through orchestrator
        final_message, updated_character, updated_game_state, metadata = \
            await orchestrator.process_action(
                user_action=user_message,
                character=character,
                game_state=game_state,
                memories=memories
            )
    finally:
        typing_task.cancel()
    
    # Save character to DB
    await character_repo.create_or_update_character(updated_character)
    
    # 🆕 Smart memory creation (zero overhead - metadata from Synthesizer)
    await create_smart_memory(
        character_id=updated_character.id,
        session_id=session_id,
        user_action=user_message,
        gm_response=final_message,
        metadata=metadata,  # From Synthesizer JSON
        location=updated_game_state.get("location")
    )
    
    # Send response
    await message.answer(final_message, parse_mode="Markdown")
```

---

## Cost Analysis (Updated)

### Per-Turn Cost Breakdown:

```
Rules Arbiter:      gpt-4o-mini  ~200 tokens  = $0.00003
Narrative Director: grok-2       ~800 tokens  = $0.00120
Response Synthesizer: gpt-4o     ~600 tokens  = $0.00090  (+100 tokens для metadata)
World State:        gpt-4o-mini  ~150 tokens  = $0.00002
Memory Retrieval:   embeddings   ~50 tokens   = $0.00000  (negligible)
──────────────────────────────────────────────────────────
TOTAL:                                         $0.00215 (~₽0.22)
```

**Overhead от Sprint 2:** +$0.00025 (12%)

**Savings vs original plan:**
- ❌ No session summary generation: -$0.001
- ❌ No separate importance scorer: -$0.00002
- ❌ No confidence validation: -$0.00002
- ❌ No CrewAI overhead: -$0 (не используем)

**Net overhead:** Фактически НОЛЬ (metadata бесплатна в existing Synthesizer call)

---

## Success Criteria Checklist

По завершении Sprint 3 проверь:

- [ ] **Database:**
  - [ ] Supabase project создан
  - [ ] Migration 001 применена (с player_knowledge_confidence)
  - [ ] pgvector extension работает
  
- [ ] **Memory System:**
  - [ ] Layered retrieval (recent + important + semantic) работает
  - [ ] Temporal ranking корректно ранжирует по recency
  - [ ] Latency <500ms для retrieval
  - [ ] Accuracy >85% (subjective evaluation)
  
- [ ] **Smart Storage:**
  - [ ] Importance scoring через Synthesizer metadata
  - [ ] Confidence scores проставляются корректно
  - [ ] Trivial memories (importance <3) фильтруются
  
- [ ] **Knowledge Scoping:**
  - [ ] GM secrets (confidence=0.0) не попадают в player retrieval
  - [ ] Player-facing responses не спойлерят
  
- [ ] **Persistence:**
  - [ ] Characters сохраняются в DB
  - [ ] Sessions tracking работает
  - [ ] Memories создаются после каждого хода
  
- [ ] **Multi-session:**
  - [ ] Бот помнит события из прошлых сессий
  - [ ] Temporal ranking работает корректно
  - [ ] Нет явных session boundaries для игрока

---

## Migration from SPRINT3_SPEC.md

**Files to SKIP/DELETE:**
- ❌ `app/agents/crew_config.py` - CrewAI не используем в MVP
- ❌ `app/agents/crew_orchestrator.py` - Simple orchestrator вместо CrewAI
- ❌ `app/db/sessions.py → generate_session_summary()` - Не нужен
- ❌ `app/memory/chunking.py` - Упрощено в layered retrieval

**Files to UPDATE:**
- ✅ `app/db/migrations/001_initial_schema.sql` - Add player_knowledge_confidence, remove summary
- ✅ `app/db/models.py` - Update EpisodicMemoryDB, GameSessionDB
- ✅ `app/agents/response_synthesizer.py` - Add metadata extraction
- ✅ `app/memory/episodic.py` - Add confidence filtering
- ✅ `app/bot/handlers.py` - Use layered retrieval + smart storage

**New Files:**
- ✅ `app/memory/retrieval.py` - Layered memory retrieval
- ✅ `app/memory/smart_storage.py` - Smart memory creation

---

## Next Steps для PM

1. **Review этот документ** вместо старого SPRINT3_SPEC.md
2. **Дать AI agent задачу:**
   ```
   "Implement Sprint 3 according to SPRINT3_UPDATED.md.
   Start with Task 1.1: Database schema migration with updated fields."
   ```
3. **Testing workflow:**
   - После каждой недели делать integration test
   - Проверять cost per turn (должен быть ~$0.0022)
   - Subjective evaluation: помнит ли бот past events?

---

## Future Enhancements (Post-Sprint 3)

**Sprint 4 возможности:**
- **NPC relationship tracking** в structured format (вместо episodic memories)
- **Quest system** через world_state с flexible outcomes
- **Memory consolidation** для очень длинных кампаний (100+ sessions)
- **CrewAI migration** если понадобится parallel execution

**Pricing model:**
- Подписка: ₽500/мес (unlimited turns, fair use ~100/день)
- Cost per user per month: ₽66 (300 turns × ₽0.22)
- Margin: 87% (отличная экономика)

---

**Вопросы?** Пиши в issues.

**Ready to implement?** Погнали! 🚀
