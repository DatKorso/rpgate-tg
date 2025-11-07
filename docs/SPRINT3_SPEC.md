# Sprint 3 Specification: Memory System & Production Infrastructure

> **Для AI Code Agent:** Этот документ содержит детальные спецификации для реализации Sprint 3. Основные задачи: внедрение долгосрочной памяти с RAG, миграция на CrewAI для оркестрации, добавление Memory Manager и World State агентов.

---

## 📋 Sprint Overview

**Цель:** Реализовать долгосрочную память (RAG), добавить persistence через Supabase, добавить Memory Manager и World State агентов с оптимизацией затрат.

**Timeframe:** 2-3 недели

**Success Criteria:**
- ✅ Бот помнит события из прошлых сессий (multi-session continuity)
- ✅ Memory retrieval работает быстро (<500ms) и точно (>85% accuracy)
- ✅ World State Agent корректно обновляет game state
- ✅ Memory Manager Agent извлекает релевантный контекст
- ✅ Данные персонажей сохраняются в PostgreSQL
- ✅ Importance scoring через LLM (single-pass, zero overhead)
- ✅ Knowledge scoping через confidence scores (метагейминг prevention)
- ✅ Temporal ranking для бесшовных сессий (без явных boundaries)

---

## 🎯 Архитектурные изменения Sprint 3

### До Sprint 3 (текущее состояние):
```
User Input → Rules Arbiter → Narrative Director → Response Synthesizer
                ↓                   ↓                      ↓
            Character         Game State            Final Message
             (FSM)             (FSM)                (Telegram)
```

### После Sprint 3:
```
User Input
    ↓
Memory Manager Agent (RAG retrieval из DB)
    ↓
[Sequential Orchestration - Simple для MVP]
    ↓
Rules Arbiter ─┐
               ├─→ World State Agent → Update DB
Narrative ─────┘        ↓
               Response Synthesizer (+ metadata extraction)
                        ↓
                  Final Message + Save Memory (smart filtering)
```

**Ключевые изменения:**
1. **Memory Manager** вызывается ПЕРВЫМ для извлечения контекста
2. **World State Agent** обновляет состояние мира и сохраняет в DB
3. **Simple orchestrator** (без CrewAI для MVP - проще, дешевле)
4. **PostgreSQL (Supabase)** хранит characters, memories, sessions
5. **Response Synthesizer** генерирует metadata в одном запросе (zero overhead)
6. **Smart memory filtering** - LLM-based importance + confidence scoring

---

## Week 1: Database Setup & Infrastructure

### Task 1.1: Supabase Project Setup

**Цель:** Создать Supabase проект и настроить database schema.

**Шаги:**

1. **Создать Supabase project:**
   - Зайти на [supabase.com](https://supabase.com)
   - Create new project
   - Выбрать регион (ближайший к целевой аудитории)
   - Сохранить connection string и anon key

2. **Добавить credentials в `.env`:**
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.your-project.supabase.co:5432/postgres
```

3. **Install dependencies:**
```bash
uv add supabase asyncpg sqlalchemy pgvector httpx
uv add --dev pytest-asyncio
```

**Note**: OpenAI package НЕ нужен - embeddings идут через OpenRouter API.

---

### Task 1.2: Database Schema Migration

**File:** `app/db/migrations/001_initial_schema.sql`

**Description:** SQL schema для characters, sessions, memories.

**Schema:**

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- TABLE: characters
-- ============================================
CREATE TABLE characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_user_id BIGINT UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    
    -- Character stats (JSON for flexibility)
    character_sheet JSONB NOT NULL,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_session_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_characters_telegram_user_id ON characters(telegram_user_id);
CREATE INDEX idx_characters_updated_at ON characters(updated_at DESC);

-- ============================================
-- TABLE: game_sessions
-- ============================================
CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- Session info
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- 🔄 Session summary удален - избыточен при постоянном memory storage
    -- Вместо этого используем temporal ranking и layered retrieval
    
    -- Stats
    turns_count INT DEFAULT 0,
    total_damage_dealt INT DEFAULT 0,
    total_damage_taken INT DEFAULT 0,
    
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(id)
);

CREATE INDEX idx_sessions_character_id ON game_sessions(character_id);
CREATE INDEX idx_sessions_started_at ON game_sessions(started_at DESC);

-- ============================================
-- TABLE: episodic_memories
-- ============================================
CREATE TABLE episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    session_id UUID REFERENCES game_sessions(id) ON DELETE SET NULL,
    
    -- Memory content
    content TEXT NOT NULL,
    
    -- Vector embedding для semantic search
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small dimension
    
    -- Memory metadata
    memory_type VARCHAR(50) DEFAULT 'event',  -- 'event', 'dialogue', 'discovery', 'combat'
    importance_score INT DEFAULT 5 CHECK (importance_score >= 0 AND importance_score <= 10),
    
    -- 🆕 Knowledge scoping для метагейминг prevention
    player_knowledge_confidence FLOAT DEFAULT 1.0 CHECK (player_knowledge_confidence >= 0.0 AND player_knowledge_confidence <= 1.0),
    -- 1.0 = персонаж точно знает, 0.5 = неопределенно, 0.0 = GM secret
    
    -- Entities for keyword filtering
    entities TEXT[],  -- ['goblin', 'tavern', 'Eldar the merchant']
    location VARCHAR(200),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(id),
    CONSTRAINT fk_session FOREIGN KEY (session_id) REFERENCES game_sessions(id)
);

CREATE INDEX idx_memories_character_id ON episodic_memories(character_id);
CREATE INDEX idx_memories_session_id ON episodic_memories(session_id);
CREATE INDEX idx_memories_created_at ON episodic_memories(created_at DESC);
CREATE INDEX idx_memories_importance ON episodic_memories(importance_score DESC);
CREATE INDEX idx_memories_confidence ON episodic_memories(player_knowledge_confidence DESC);

-- Vector similarity search index (IVFFlat for performance)
CREATE INDEX idx_memories_embedding ON episodic_memories 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- GIN index for entities array search
CREATE INDEX idx_memories_entities ON episodic_memories USING GIN(entities);

-- ============================================
-- TABLE: semantic_memories (World Lore)
-- ============================================
CREATE TABLE semantic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Content
    content TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,  -- 'rule', 'lore', 'location', 'npc', 'item'
    
    -- Vector embedding
    embedding VECTOR(1536),
    
    -- Metadata
    tags TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_semantic_category ON semantic_memories(category);
CREATE INDEX idx_semantic_embedding ON semantic_memories 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);

-- ============================================
-- TABLE: world_state (Global/per-character state)
-- ============================================
CREATE TABLE world_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    character_id UUID NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
    
    -- World state as JSON
    state_data JSONB NOT NULL DEFAULT '{}',
    
    -- For tracking changes
    version INT DEFAULT 1,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT fk_character FOREIGN KEY (character_id) REFERENCES characters(id),
    CONSTRAINT unique_character_state UNIQUE (character_id)
);

CREATE INDEX idx_world_state_character_id ON world_state(character_id);

-- ============================================
-- FUNCTIONS: Auto-update timestamps
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_characters_updated_at
    BEFORE UPDATE ON characters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_semantic_updated_at
    BEFORE UPDATE ON semantic_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_world_state_updated_at
    BEFORE UPDATE ON world_state
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SAMPLE DATA: Semantic Memories (Game Lore)
-- ============================================
INSERT INTO semantic_memories (content, category, tags) VALUES
    ('В этом мире магия запрещена королевским указом после Великой Магической Катастрофы. Использование заклинаний карается смертью.', 'lore', ARRAY['magic', 'law', 'history']),
    ('Город Новоград — крупнейший торговый центр королевства. Здесь можно купить любые товары, от простых инструментов до редких артефактов.', 'location', ARRAY['city', 'trade', 'Новоград']),
    ('Гоблины обитают в пещерах северных гор. Они агрессивны, но трусливы. AC: 12, HP: 7, атака: +4 (1d6+2 урона).', 'npc', ARRAY['goblin', 'enemy', 'combat']),
    ('Для проверки атаки брось d20 и прибавь модификатор силы. Если результат больше или равен AC противника — попадание.', 'rule', ARRAY['combat', 'attack', 'mechanics']);

```

**Применение миграции:**

**File:** `scripts/apply_migration.py`

```python
"""Apply database migration to Supabase."""
import asyncio
import asyncpg
from app.config import settings

async def apply_migration():
    """Apply initial schema migration."""
    # Read migration file
    with open('app/db/migrations/001_initial_schema.sql', 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    # Connect to database
    conn = await asyncpg.connect(settings.SUPABASE_DB_URL)
    
    try:
        print("Applying migration...")
        await conn.execute(migration_sql)
        print("✅ Migration applied successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_migration())
```

**Run migration:**
```bash
uv run python scripts/apply_migration.py
```

---

### Task 1.3: Database Client & Models

**File:** `app/db/supabase.py`

**Description:** Supabase client wrapper для удобной работы с DB.

```python
"""Supabase client for database operations."""
from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Wrapper для Supabase client."""
    
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        logger.info("Supabase client initialized")
    
    @property
    def db(self) -> Client:
        """Get Supabase client instance."""
        return self.client


# Global instance
supabase_client = SupabaseClient()
```

**File:** `app/db/models.py`

**Description:** Pydantic models для database entities.

```python
"""Database models."""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class CharacterDB(BaseModel):
    """Character model для database."""
    id: UUID
    telegram_user_id: int
    name: str
    character_sheet: dict  # JSON with CharacterSheet data
    created_at: datetime
    updated_at: datetime
    last_session_at: Optional[datetime] = None


class GameSessionDB(BaseModel):
    """Game session model."""
    id: UUID
    character_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    # summary удален - избыточен при layered retrieval
    turns_count: int = 0
    total_damage_dealt: int = 0
    total_damage_taken: int = 0


class EpisodicMemoryDB(BaseModel):
    """Episodic memory model."""
    id: UUID
    character_id: UUID
    session_id: Optional[UUID] = None
    content: str
    embedding: Optional[List[float]] = None  # Vector embedding
    memory_type: str = "event"
    importance_score: int = Field(default=5, ge=0, le=10)
    player_knowledge_confidence: float = Field(default=1.0, ge=0.0, le=1.0)  # 🆕 Knowledge scoping
    entities: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    created_at: datetime


class SemanticMemoryDB(BaseModel):
    """Semantic memory (world lore) model."""
    id: UUID
    content: str
    category: str  # 'rule', 'lore', 'location', 'npc', 'item'
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorldStateDB(BaseModel):
    """World state model."""
    id: UUID
    character_id: UUID
    state_data: dict
    version: int = 1
    updated_at: datetime
```

**Update config.py:**

**File:** `app/config.py` (ADD)

```python
# Add to Settings class:

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_DB_URL: str
    
    # Embeddings Configuration (uses OpenRouter)
    EMBEDDING_MODEL: str = "qwen/qwen3-embedding-8b"
    EMBEDDING_DIMENSION: int = 1536
```

---

## Week 2: Memory System & CrewAI Integration

### Task 2.1: Embeddings Service

**File:** `app/memory/embeddings.py`

**Description:** Service для генерации vector embeddings через OpenAI API.

```python
"""Embeddings service для vector search."""
from typing import List
import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service для генерации embeddings через OpenRouter API."""
    
    def __init__(self):
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding для одного текста.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.site_url,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": text,
                    },
                    timeout=30.0,
                )
                
                response.raise_for_status()
                data = response.json()
                
                embedding = data["data"][0]["embedding"]
                logger.debug(f"Generated embedding for text: {text[:50]}...")
                
                return embedding
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings для multiple texts (batch).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.site_url,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": texts,
                    },
                    timeout=60.0,
                )
                
                response.raise_for_status()
                data = response.json()
                
                embeddings = [item["embedding"] for item in data["data"]]
                logger.info(f"Generated {len(embeddings)} embeddings in batch")
                
                return embeddings
                
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise


# Global instance
embeddings_service = EmbeddingsService()
```

---

### Task 2.2: Episodic Memory Manager

**File:** `app/memory/episodic.py`

**Description:** CRUD operations для episodic memories.

```python
"""Episodic memory management."""
from typing import List, Optional
from uuid import UUID
import asyncpg
from app.config import settings
from app.memory.embeddings import embeddings_service
import logging

logger = logging.getLogger(__name__)


class EpisodicMemoryManager:
    """Manager для episodic memories (события персонажа)."""
    
    def __init__(self):
        self.db_url = settings.SUPABASE_DB_URL
    
    async def create_memory(
        self,
        character_id: UUID,
        content: str,
        session_id: Optional[UUID] = None,
        memory_type: str = "event",
        importance_score: int = 5,
        entities: Optional[List[str]] = None,
        location: Optional[str] = None
    ) -> UUID:
        """
        Create new episodic memory.
        
        Args:
            character_id: Character UUID
            content: Memory content (text)
            session_id: Session UUID (optional)
            memory_type: Type ('event', 'dialogue', 'discovery', 'combat')
            importance_score: 0-10 importance rating
            entities: List of entities mentioned (for filtering)
            location: Location where memory happened
            
        Returns:
            Created memory UUID
        """
        # Generate embedding
        embedding = await embeddings_service.embed_text(content)
        
        # Connect to DB
        conn = await asyncpg.connect(self.db_url)
        
        try:
            memory_id = await conn.fetchval(
                """
                INSERT INTO episodic_memories (
                    character_id, session_id, content, embedding, 
                    memory_type, importance_score, entities, location
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id
                """,
                character_id,
                session_id,
                content,
                embedding,
                memory_type,
                importance_score,
                entities or [],
                location
            )
            
            logger.info(f"Created memory {memory_id} for character {character_id}")
            return memory_id
            
        finally:
            await conn.close()
    
    async def search_memories(
        self,
        character_id: UUID,
        query_text: str,
        top_k: int = 5,
        min_importance: int = 0,
        entity_filter: Optional[List[str]] = None
    ) -> List[dict]:
        """
        Search memories using vector similarity + filters.
        
        Args:
            character_id: Character UUID
            query_text: Query text to search
            top_k: Number of results to return
            min_importance: Minimum importance score
            entity_filter: Filter by entities (optional)
            
        Returns:
            List of memories with similarity scores
        """
        # Generate query embedding
        query_embedding = await embeddings_service.embed_text(query_text)
        
        conn = await asyncpg.connect(self.db_url)
        
        try:
            # Build query
            sql = """
                SELECT 
                    id,
                    content,
                    memory_type,
                    importance_score,
                    entities,
                    location,
                    created_at,
                    1 - (embedding <=> $2::vector) as similarity
                FROM episodic_memories
                WHERE character_id = $1
                  AND importance_score >= $3
            """
            params = [character_id, query_embedding, min_importance]
            
            # Add entity filter if provided
            if entity_filter:
                sql += " AND entities && $4::text[]"
                params.append(entity_filter)
            
            sql += """
                ORDER BY embedding <=> $2::vector
                LIMIT $5
            """
            params.append(top_k)
            
            # Execute query
            rows = await conn.fetch(sql, *params)
            
            # Convert to dicts
            memories = []
            for row in rows:
                memories.append({
                    "id": row["id"],
                    "content": row["content"],
                    "memory_type": row["memory_type"],
                    "importance_score": row["importance_score"],
                    "entities": row["entities"],
                    "location": row["location"],
                    "created_at": row["created_at"],
                    "similarity": float(row["similarity"])
                })
            
            logger.info(
                f"Found {len(memories)} memories for query '{query_text[:30]}...' "
                f"(character {character_id})"
            )
            
            return memories
            
        finally:
            await conn.close()
    
    async def get_recent_memories(
        self,
        character_id: UUID,
        limit: int = 10
    ) -> List[dict]:
        """
        Get recent memories (for context).
        
        Args:
            character_id: Character UUID
            limit: Number of memories to return
            
        Returns:
            List of recent memories
        """
        conn = await asyncpg.connect(self.db_url)
        
        try:
            rows = await conn.fetch(
                """
                SELECT id, content, memory_type, importance_score, 
                       entities, location, created_at
                FROM episodic_memories
                WHERE character_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                character_id,
                limit
            )
            
            memories = [dict(row) for row in rows]
            return memories
            
        finally:
            await conn.close()


# Global instance
episodic_memory = EpisodicMemoryManager()
```

---

### Task 2.3: Memory Manager Agent

**File:** `app/agents/memory_manager.py`

**Description:** Agent для извлечения релевантного контекста из памяти.

```python
"""Memory Manager Agent - Campaign Historian."""
from typing import Any, List
from uuid import UUID
from app.agents.base import BaseAgent
from app.memory.episodic import episodic_memory
from app.game.character import CharacterSheet
import logging

logger = logging.getLogger(__name__)


class MemoryManagerAgent(BaseAgent):
    """
    Agent для управления памятью и retrieval.
    
    Роль: "Campaign Historian"
    Задача: Извлечь релевантный контекст из long-term памяти
    """
    
    def __init__(self):
        super().__init__(
            name="MemoryManager",
            model="",  # НЕ использует LLM, только embeddings + DB
            temperature=0.0
        )
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve relevant memories.
        
        Args:
            context: {
                "user_action": str,
                "character": CharacterSheet,
                "top_k": int (optional, default 3)
            }
            
        Returns:
            {
                "relevant_memories": List[dict],  # Top-K похожих memories
                "recent_memories": List[dict],     # Недавние события
                "memory_summary": str              # Текстовое резюме для промпта
            }
        """
        user_action = context["user_action"]
        character: CharacterSheet = context["character"]
        top_k = context.get("top_k", 3)
        
        character_id = character.id
        
        # Step 1: Vector search для релевантных memories
        relevant_memories = await episodic_memory.search_memories(
            character_id=character_id,
            query_text=user_action,
            top_k=top_k,
            min_importance=3  # Только важные события
        )
        
        # Step 2: Get recent memories для immediate context
        recent_memories = await episodic_memory.get_recent_memories(
            character_id=character_id,
            limit=5
        )
        
        # Step 3: Build memory summary для промпта
        memory_summary = self._build_memory_summary(
            relevant_memories,
            recent_memories
        )
        
        output = {
            "relevant_memories": relevant_memories,
            "recent_memories": recent_memories,
            "memory_summary": memory_summary
        }
        
        self.log_execution(context, output)
        return output
    
    def _build_memory_summary(
        self,
        relevant: List[dict],
        recent: List[dict]
    ) -> str:
        """Build текстовое резюме памяти для промпта."""
        parts = []
        
        if relevant:
            parts.append("📚 **Релевантные воспоминания:**")
            for mem in relevant[:3]:
                importance = "⭐" * mem["importance_score"]
                parts.append(f"- {mem['content']} {importance}")
        
        if recent:
            parts.append("\n📅 **Недавние события:**")
            for mem in recent[:3]:
                parts.append(f"- {mem['content']}")
        
        if not parts:
            return "Нет доступных воспоминаний."
        
        return "\n".join(parts)
```

---

### Task 2.4: World State Agent

**File:** `app/agents/world_state.py`

**Description:** Agent для обновления состояния мира и сохранения в DB.

```python
"""World State Agent - World Simulator."""
from typing import Any
from uuid import UUID
import asyncpg
from app.agents.base import BaseAgent
from app.game.character import CharacterSheet
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class WorldStateAgent(BaseAgent):
    """
    Agent для управления состоянием мира.
    
    Роль: "World Simulator"
    Задача: Обновить world state на основе действий игрока
    """
    
    def __init__(self):
        super().__init__(
            name="WorldState",
            model="gpt-4o-mini",
            temperature=0.0  # Детерминированность
        )
        self.db_url = settings.SUPABASE_DB_URL
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Update world state.
        
        Args:
            context: {
                "character": CharacterSheet,
                "game_state": dict,
                "mechanics_result": dict,
                "action_type": str
            }
            
        Returns:
            {
                "updated_game_state": dict,
                "state_changes": List[str]  # Human-readable changes
            }
        """
        character: CharacterSheet = context["character"]
        game_state = context.get("game_state", {})
        mechanics_result = context.get("mechanics_result", {})
        action_type = context.get("action_type", "other")
        
        # Deep copy game state
        updated_state = {**game_state}
        state_changes = []
        
        # Apply mechanics-based updates
        if action_type == "attack" and mechanics_result.get("hit"):
            # Enemy took damage
            damage = mechanics_result.get("total_damage", 0)
            
            # Check if enemy died (simple logic для MVP)
            if damage >= 7:  # Goblin HP
                if "enemies" in updated_state and updated_state["enemies"]:
                    killed_enemy = updated_state["enemies"][0]
                    updated_state["enemies"].remove(killed_enemy)
                    state_changes.append(f"{killed_enemy} повержен")
                    
                    # End combat if no more enemies
                    if not updated_state.get("enemies"):
                        updated_state["in_combat"] = False
                        state_changes.append("Бой завершен")
        
        # Save to database
        await self._save_world_state(character.id, updated_state)
        
        output = {
            "updated_game_state": updated_state,
            "state_changes": state_changes
        }
        
        self.log_execution(context, output)
        return output
    
    async def _save_world_state(self, character_id: UUID, state_data: dict):
        """Save world state to database."""
        conn = await asyncpg.connect(self.db_url)
        
        try:
            await conn.execute(
                """
                INSERT INTO world_state (character_id, state_data, version)
                VALUES ($1, $2, 1)
                ON CONFLICT (character_id) 
                DO UPDATE SET 
                    state_data = $2,
                    version = world_state.version + 1,
                    updated_at = NOW()
                """,
                character_id,
                state_data
            )
            
            logger.debug(f"Saved world state for character {character_id}")
            
        finally:
            await conn.close()
    
    async def load_world_state(self, character_id: UUID) -> dict:
        """Load world state from database."""
        conn = await asyncpg.connect(self.db_url)
        
        try:
            row = await conn.fetchrow(
                "SELECT state_data FROM world_state WHERE character_id = $1",
                character_id
            )
            
            if row:
                return row["state_data"]
            else:
                # Default state
                return {
                    "in_combat": False,
                    "enemies": [],
                    "location": "tavern"
                }
                
        finally:
            await conn.close()


# Global instance
world_state_agent = WorldStateAgent()
```

---

### Task 2.5: CrewAI Integration

**Install CrewAI:**
```bash
uv add crewai crewai-tools
```

**File:** `app/agents/crew_config.py`

**Description:** CrewAI configuration для агентов.

```python
"""CrewAI configuration."""
from crewai import Agent, Task, Crew, Process
from app.agents.memory_manager import MemoryManagerAgent
from app.agents.rules_arbiter import RulesArbiterAgent
from app.agents.narrative_director import NarrativeDirectorAgent
from app.agents.world_state import WorldStateAgent
from app.agents.response_synthesizer import ResponseSynthesizerAgent


def create_gm_crew() -> Crew:
    """
    Create CrewAI crew для GM system.
    
    Workflow:
    1. Memory Manager → retrieve context
    2. Rules Arbiter (parallel) Narrative Director → process action
    3. World State → update world
    4. Response Synthesizer → final message
    """
    
    # Define CrewAI Agents (wrapper around our agents)
    memory_agent = Agent(
        role="Campaign Historian",
        goal="Retrieve relevant memories and context for the current action",
        backstory="You are responsible for maintaining continuity across sessions",
        verbose=True
    )
    
    rules_agent = Agent(
        role="Rules Arbiter",
        goal="Resolve game mechanics (dice rolls, combat, skill checks)",
        backstory="You enforce game rules fairly and consistently",
        verbose=True
    )
    
    narrative_agent = Agent(
        role="Narrative Director",
        goal="Create vivid, engaging story descriptions",
        backstory="You bring the world to life through compelling narrative",
        verbose=True
    )
    
    world_agent = Agent(
        role="World Simulator",
        goal="Track and update the state of the game world",
        backstory="You maintain consistency of the world state",
        verbose=True
    )
    
    synthesizer_agent = Agent(
        role="Master Narrator",
        goal="Combine all outputs into a beautiful final message",
        backstory="You present the complete picture to the player",
        verbose=True
    )
    
    # Define Tasks
    memory_task = Task(
        description="Retrieve relevant memories for: {user_action}",
        agent=memory_agent,
        expected_output="Memory summary with relevant context"
    )
    
    rules_task = Task(
        description="Resolve mechanics for: {user_action}",
        agent=rules_agent,
        expected_output="Mechanics result with dice rolls and success/failure",
        context=[memory_task]  # Depends on memory
    )
    
    narrative_task = Task(
        description="Generate narrative description for: {user_action}",
        agent=narrative_agent,
        expected_output="Vivid narrative description (2-4 sentences)",
        context=[memory_task]  # Depends on memory
    )
    
    world_task = Task(
        description="Update world state based on action results",
        agent=world_agent,
        expected_output="Updated world state",
        context=[rules_task, narrative_task]  # Depends on both
    )
    
    synthesizer_task = Task(
        description="Create final formatted message for player",
        agent=synthesizer_agent,
        expected_output="Complete formatted message with mechanics + narrative",
        context=[rules_task, narrative_task, world_task]
    )
    
    # Create Crew
    crew = Crew(
        agents=[
            memory_agent,
            rules_agent,
            narrative_agent,
            world_agent,
            synthesizer_agent
        ],
        tasks=[
            memory_task,
            rules_task,
            narrative_task,
            world_task,
            synthesizer_task
        ],
        process=Process.sequential,  # Sequential для MVP
        verbose=True
    )
    
    return crew
```

**File:** `app/agents/crew_orchestrator.py`

**Description:** Новый orchestrator использующий CrewAI.

```python
"""CrewAI-based orchestrator."""
from typing import Any, Tuple
from app.agents.crew_config import create_gm_crew
from app.game.character import CharacterSheet
import logging

logger = logging.getLogger(__name__)


class CrewAIOrchestrator:
    """Orchestrator using CrewAI для agent coordination."""
    
    def __init__(self):
        self.crew = create_gm_crew()
    
    async def process_action(
        self,
        user_action: str,
        character: CharacterSheet,
        game_state: dict,
        recent_history: list = None
    ) -> Tuple[str, CharacterSheet, dict]:
        """
        Process user action through CrewAI crew.
        
        Args:
            user_action: Player's action text
            character: Character sheet
            game_state: Current game state
            recent_history: Recent conversation history
            
        Returns:
            (final_message, updated_character, updated_game_state)
        """
        logger.info(f"CrewAI processing: {user_action}")
        
        # Build inputs для CrewAI
        inputs = {
            "user_action": user_action,
            "character": character.model_dump(),
            "game_state": game_state,
            "recent_history": recent_history or []
        }
        
        # Execute crew
        result = await self.crew.kickoff_async(inputs=inputs)
        
        # Parse result
        # TODO: Extract final message, updated character, updated game state
        # For MVP, fallback to simple orchestrator
        
        logger.info("CrewAI processing complete")
        
        return result
```

**NOTE:** CrewAI интеграция потребует адаптации наших агентов под CrewAI Tools API. Для MVP можем начать с простого orchestrator и мигрировать постепенно.

---

## Week 3: Integration & Polish

### Task 3.1: Character Persistence

**File:** `app/db/characters.py`

**Description:** CRUD operations для characters в DB.

```python
"""Character database operations."""
from typing import Optional
from uuid import UUID
import asyncpg
from app.config import settings
from app.game.character import CharacterSheet
from app.db.models import CharacterDB
import logging

logger = logging.getLogger(__name__)


class CharacterRepository:
    """Repository для character persistence."""
    
    def __init__(self):
        self.db_url = settings.SUPABASE_DB_URL
    
    async def create_or_update_character(
        self,
        character: CharacterSheet
    ) -> UUID:
        """
        Create or update character in database.
        
        Args:
            character: CharacterSheet instance
            
        Returns:
            Character UUID
        """
        conn = await asyncpg.connect(self.db_url)
        
        try:
            character_id = await conn.fetchval(
                """
                INSERT INTO characters (
                    id, telegram_user_id, name, character_sheet
                )
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (telegram_user_id)
                DO UPDATE SET
                    name = $3,
                    character_sheet = $4,
                    updated_at = NOW()
                RETURNING id
                """,
                character.id,
                character.telegram_user_id,
                character.name,
                character.model_dump()
            )
            
            logger.info(f"Saved character {character_id} (user {character.telegram_user_id})")
            return character_id
            
        finally:
            await conn.close()
    
    async def get_character_by_telegram_id(
        self,
        telegram_user_id: int
    ) -> Optional[CharacterSheet]:
        """
        Get character by Telegram user ID.
        
        Args:
            telegram_user_id: Telegram user ID
            
        Returns:
            CharacterSheet or None if not found
        """
        conn = await asyncpg.connect(self.db_url)
        
        try:
            row = await conn.fetchrow(
                """
                SELECT character_sheet
                FROM characters
                WHERE telegram_user_id = $1
                """,
                telegram_user_id
            )
            
            if row:
                character_data = row["character_sheet"]
                character = CharacterSheet(**character_data)
                logger.debug(f"Loaded character for user {telegram_user_id}")
                return character
            else:
                return None
                
        finally:
            await conn.close()


# Global instance
character_repo = CharacterRepository()
```

---

### Task 3.2: Session Management

**File:** `app/db/sessions.py`

**Description:** Session tracking и summary generation.

```python
"""Game session management."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg
from app.config import settings
from app.llm.client import llm_client
import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """Manager для game sessions."""
    
    def __init__(self):
        self.db_url = settings.SUPABASE_DB_URL
    
    async def start_session(self, character_id: UUID) -> UUID:
        """
        Start new game session.
        
        Args:
            character_id: Character UUID
            
        Returns:
            Session UUID
        """
        conn = await asyncpg.connect(self.db_url)
        
        try:
            session_id = await conn.fetchval(
                """
                INSERT INTO game_sessions (character_id)
                VALUES ($1)
                RETURNING id
                """,
                character_id
            )
            
            logger.info(f"Started session {session_id} for character {character_id}")
            return session_id
            
        finally:
            await conn.close()
    
    async def end_session(
        self,
        session_id: UUID,
        conversation_history: list
    ):
        """
        End session and generate summary.
        
        Args:
            session_id: Session UUID
            conversation_history: Full conversation history
        """
        # Generate summary using LLM
        summary = await self._generate_session_summary(conversation_history)
        
        conn = await asyncpg.connect(self.db_url)
        
        try:
            await conn.execute(
                """
                UPDATE game_sessions
                SET ended_at = NOW(),
                    summary = $2
                WHERE id = $1
                """,
                session_id,
                summary
            )
            
            logger.info(f"Ended session {session_id}")
            
        finally:
            await conn.close()
    
    async def _generate_session_summary(self, history: list) -> str:
        """Generate LLM summary of session."""
        # Build conversation text
        conversation = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in history
        ])
        
        system_prompt = """Ты — архивариус игровых сессий.
Твоя задача — создать краткое резюме (2-3 предложения) игровой сессии.

Включи:
- Ключевые события
- Важных NPC
- Существенные решения игрока

Пиши от третьего лица в прошедшем времени."""

        user_prompt = f"""Игровая сессия:

{conversation}

Создай краткое резюме сессии."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        summary = await llm_client.get_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=200
        )
        
        return summary


# Global instance
session_manager = SessionManager()
```

---

### Task 3.3: Update Bot Handlers для Persistence

**File:** `app/bot/handlers.py` (UPDATE)

**Major changes:**

1. Load character from DB instead of FSM
2. Save character to DB after each action
3. Create memories after each turn
4. Start/end sessions

```python
# Add imports
from app.db.characters import character_repo
from app.db.sessions import session_manager
from app.memory.episodic import episodic_memory
from app.agents.world_state import world_state_agent

# Update handle_conversation
@router.message(ConversationState.in_conversation, F.text)
async def handle_conversation(message: Message, state: FSMContext):
    """Main handler with DB persistence."""
    user_message = message.text
    telegram_user_id = message.from_user.id
    
    # Load character from DB
    character = await character_repo.get_character_by_telegram_id(telegram_user_id)
    
    if not character:
        await message.answer("❌ Персонаж не найден. Используй /start для создания.")
        return
    
    # Load world state from DB
    game_state = await world_state_agent.load_world_state(character.id)
    
    # Get session from FSM (or create new)
    data = await state.get_data()
    session_id = data.get("session_id")
    
    if not session_id:
        session_id = await session_manager.start_session(character.id)
        await state.update_data(session_id=session_id)
    
    # Get history
    history = data.get("history", [])
    recent_messages = [msg["content"] for msg in history[-5:]]
    
    # Typing indicator
    typing_task = asyncio.create_task(_send_typing_indicator(message))
    
    try:
        # Process through orchestrator
        final_message, updated_character, updated_game_state = await orchestrator.process_action(
            user_action=user_message,
            character=character,
            game_state=game_state,
            recent_history=recent_messages
        )
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    # Save character to DB
    await character_repo.create_or_update_character(updated_character)
    
    # Create memory для этого хода
    await episodic_memory.create_memory(
        character_id=updated_character.id,
        session_id=session_id,
        content=f"Игрок: {user_message}\nGM: {final_message}",
        memory_type="event",
        importance_score=5,  # TODO: LLM-based importance scoring
        location=updated_game_state.get("location")
    )
    
    # Update history
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": final_message})
    
    if len(history) > 20:
        history = history[-20:]
    
    await state.update_data(history=history)
    
    # Send response
    await message.answer(final_message, parse_mode="Markdown")
```

---

### Task 3.4: Chunking & Importance Scoring

**File:** `app/memory/chunking.py`

**Description:** Smart chunking для conversation history.

```python
"""Conversation chunking для memory storage."""
from typing import List


class ConversationChunker:
    """Chunker для разбиения диалога на semantic chunks."""
    
    @staticmethod
    def chunk_by_turns(
        conversation: List[dict],
        chunk_size: int = 3
    ) -> List[str]:
        """
        Chunk conversation по turns (пары user-assistant).
        
        Args:
            conversation: List of {"role": ..., "content": ...}
            chunk_size: Number of turns per chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        current_chunk = []
        
        for i in range(0, len(conversation), 2):
            if i + 1 < len(conversation):
                # User + Assistant pair
                user_msg = conversation[i]["content"]
                assistant_msg = conversation[i + 1]["content"]
                
                current_chunk.append(f"Игрок: {user_msg}")
                current_chunk.append(f"GM: {assistant_msg}")
                
                if len(current_chunk) >= chunk_size * 2:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
        
        # Add remaining
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        
        return chunks


# Global instance
conversation_chunker = ConversationChunker()
```

---

### Task 3.5: Testing

**File:** `tests/test_memory.py`

```python
"""Tests для memory system."""
import pytest
from uuid import uuid4
from app.memory.episodic import episodic_memory
from app.memory.embeddings import embeddings_service


@pytest.mark.asyncio
async def test_create_memory():
    """Test memory creation."""
    character_id = uuid4()
    
    memory_id = await episodic_memory.create_memory(
        character_id=character_id,
        content="Игрок встретил торговца Элдара в таверне",
        memory_type="event",
        importance_score=7,
        entities=["Элдар", "таверна"],
        location="tavern"
    )
    
    assert memory_id is not None


@pytest.mark.asyncio
async def test_search_memories():
    """Test memory search."""
    character_id = uuid4()
    
    # Create test memories
    await episodic_memory.create_memory(
        character_id=character_id,
        content="Игрок встретил торговца Элдара",
        entities=["Элдар"]
    )
    
    # Search
    results = await episodic_memory.search_memories(
        character_id=character_id,
        query_text="торговец",
        top_k=5
    )
    
    assert len(results) > 0
    assert "Элдар" in results[0]["content"]


@pytest.mark.asyncio
async def test_embeddings():
    """Test embeddings generation."""
    text = "Тестовый текст для embedding"
    
    embedding = await embeddings_service.embed_text(text)
    
    assert len(embedding) == 1536  # text-embedding-3-small dimension
    assert all(isinstance(x, float) for x in embedding)
```

**Run tests:**
```bash
uv run pytest tests/test_memory.py -v
```

---

## Success Criteria Checklist

По завершении Sprint 3 проверь:

- [ ] **Database:**
  - [ ] Supabase project создан и настроен
  - [ ] Миграция применена успешно
  - [ ] pgvector extension работает
  
- [ ] **Memory System:**
  - [ ] Embeddings генерируются корректно
  - [ ] Memory search возвращает релевантные результаты
  - [ ] Latency <500ms для retrieval
  - [ ] Accuracy >85% (subjective evaluation)
  
- [ ] **Agents:**
  - [ ] Memory Manager извлекает контекст
  - [ ] World State сохраняет состояние в DB
  - [ ] Все агенты работают совместно
  
- [ ] **Persistence:**
  - [ ] Characters сохраняются в DB
  - [ ] Sessions создаются и завершаются
  - [ ] Memories создаются после каждого хода
  
- [ ] **Multi-session:**
  - [ ] Бот помнит события из прошлых сессий
  - [ ] Context корректно извлекается при новой сессии

---

## Cost Analysis Sprint 3

**New costs:**
- Embeddings: $0.02 / 1M tokens
  - Per memory creation (~100 tokens): $0.000002
  - Per search (query embedding): $0.000002
- Session summary LLM: ~$0.001 per session

**Total added cost per turn:** ~$0.00001 (negligible)

**Database costs (Supabase):**
- Free tier: 500MB database, 2GB bandwidth
- Should be enough для MVP (100-200 users)

---

## Migration Path: Simple Orchestrator → CrewAI

**Phase 1 (Week 2):** Install CrewAI, создать crew config
**Phase 2 (Week 3):** Постепенно мигрировать agents на CrewAI Tools API
**Phase 3 (Post-Sprint 3):** Full CrewAI orchestration с parallel execution

**Fallback:** Если CrewAI слишком сложен для MVP, оставляем простой orchestrator до Sprint 4.

---

## Next Steps After Sprint 3

**Sprint 4 будет включать:**
- Production deployment (Railway/Render)
- Redis для FSM persistence
- Webhooks вместо polling
- Advanced CrewAI workflows (parallel execution, loops)
- Cost optimization
- Monitoring & logging

---

## Appendix: Environment Variables

**Add to `.env`:**

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# OpenAI (for embeddings)
OPENAI_API_KEY=sk-...

# Embeddings config
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=4096
```

---

**Ready для Sprint 3? Let's build! 🚀**
