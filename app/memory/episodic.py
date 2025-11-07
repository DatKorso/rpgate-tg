"""
Episodic Memory Manager - Store and retrieve game memories with vector search.

Manages episodic memories (events, dialogues, discoveries) using pgvector
for semantic search and retrieval.
"""

import logging
from typing import List, Optional
from uuid import UUID
import asyncpg

from app.db.supabase import get_db_connection
from app.db.models import EpisodicMemoryDB
from app.memory.embeddings import embeddings_service

logger = logging.getLogger(__name__)


class EpisodicMemoryManager:
    """Manager for episodic memories with vector search capabilities."""
    
    async def create_memory(
        self,
        character_id: UUID,
        content: str,
        session_id: Optional[UUID] = None,
        memory_type: str = "event",
        importance_score: int = 5,
        entities: Optional[List[str]] = None,
        location: Optional[str] = None,
    ) -> Optional[EpisodicMemoryDB]:
        """
        Create new episodic memory with embedding.
        
        Args:
            character_id: UUID of character
            content: Memory text content
            session_id: Optional session UUID
            memory_type: Type of memory (event, dialogue, discovery, combat)
            importance_score: Importance from 0-10 (default 5)
            entities: List of entities mentioned (e.g., ['goblin', 'tavern'])
            location: Location name
            
        Returns:
            Created memory object or None on failure
        """
        try:
            # Generate embedding for content
            logger.info(f"Generating embedding for memory: {content[:50]}...")
            embedding = await embeddings_service.embed_text(content)
            
            if not embedding:
                logger.error("Failed to generate embedding for memory")
                return None
            
            # Convert to PostgreSQL halfvec format string
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            # Insert into database
            conn = await get_db_connection()
            try:
                query = """
                    INSERT INTO episodic_memories 
                    (character_id, session_id, content, embedding, memory_type, 
                     importance_score, entities, location)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id, character_id, session_id, content, memory_type,
                              importance_score, entities, location, created_at
                """
                
                row = await conn.fetchrow(
                    query,
                    character_id,
                    session_id,
                    content,
                    embedding_str,  # Vector as string
                    memory_type,
                    importance_score,
                    entities or [],
                    location
                )
                
                if row:
                    memory = EpisodicMemoryDB(
                        id=row['id'],
                        character_id=row['character_id'],
                        session_id=row['session_id'],
                        content=row['content'],
                        memory_type=row['memory_type'],
                        importance_score=row['importance_score'],
                        entities=row['entities'],
                        location=row['location'],
                        created_at=row['created_at']
                    )
                    
                    logger.info(f"Created memory {memory.id} for character {character_id}")
                    return memory
                    
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error creating memory: {e}", exc_info=True)
            return None
    
    async def search_memories(
        self,
        character_id: UUID,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.5,
        memory_types: Optional[List[str]] = None,
        min_importance: int = 0
    ) -> List[tuple[EpisodicMemoryDB, float]]:
        """
        Search memories using semantic similarity.
        
        Args:
            character_id: UUID of character
            query: Search query text
            limit: Maximum number of results
            similarity_threshold: Minimum similarity (0-1, higher = more similar)
            memory_types: Filter by memory types
            min_importance: Minimum importance score
            
        Returns:
            List of (memory, similarity_score) tuples, sorted by relevance
        """
        try:
            # Generate query embedding
            logger.info(f"Searching memories for: {query[:50]}...")
            query_embedding = await embeddings_service.embed_text(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Convert to PostgreSQL halfvec format string
            query_embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            
            # Build query with filters
            conn = await get_db_connection()
            try:
                sql_parts = [
                    """
                    SELECT 
                        id, character_id, session_id, content, memory_type,
                        importance_score, entities, location, created_at,
                        1 - (embedding <=> $2) as similarity
                    FROM episodic_memories
                    WHERE character_id = $1
                    """
                ]
                params = [character_id, query_embedding_str]
                param_idx = 3
                
                # Add filters
                if memory_types:
                    sql_parts.append(f"AND memory_type = ANY(${param_idx})")
                    params.append(memory_types)
                    param_idx += 1
                
                if min_importance > 0:
                    sql_parts.append(f"AND importance_score >= ${param_idx}")
                    params.append(min_importance)
                    param_idx += 1
                
                # Add similarity threshold
                sql_parts.append(f"AND (1 - (embedding <=> $2)) >= ${param_idx}")
                params.append(similarity_threshold)
                param_idx += 1
                
                # Order and limit
                sql_parts.append("ORDER BY similarity DESC, importance_score DESC")
                sql_parts.append(f"LIMIT ${param_idx}")
                params.append(limit)
                
                sql = "\n".join(sql_parts)
                
                rows = await conn.fetch(sql, *params)
                
                results = []
                for row in rows:
                    memory = EpisodicMemoryDB(
                        id=row['id'],
                        character_id=row['character_id'],
                        session_id=row['session_id'],
                        content=row['content'],
                        memory_type=row['memory_type'],
                        importance_score=row['importance_score'],
                        entities=row['entities'],
                        location=row['location'],
                        created_at=row['created_at']
                    )
                    similarity = float(row['similarity'])
                    results.append((memory, similarity))
                
                logger.info(f"Found {len(results)} relevant memories")
                return results
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error searching memories: {e}", exc_info=True)
            return []
    
    async def get_recent_memories(
        self,
        character_id: UUID,
        limit: int = 10,
        session_id: Optional[UUID] = None
    ) -> List[EpisodicMemoryDB]:
        """
        Get most recent memories for character.
        
        Args:
            character_id: UUID of character
            limit: Maximum number of memories
            session_id: Optional session filter
            
        Returns:
            List of recent memories, newest first
        """
        try:
            conn = await get_db_connection()
            try:
                if session_id:
                    query = """
                        SELECT id, character_id, session_id, content, memory_type,
                               importance_score, entities, location, created_at
                        FROM episodic_memories
                        WHERE character_id = $1 AND session_id = $2
                        ORDER BY created_at DESC
                        LIMIT $3
                    """
                    rows = await conn.fetch(query, character_id, session_id, limit)
                else:
                    query = """
                        SELECT id, character_id, session_id, content, memory_type,
                               importance_score, entities, location, created_at
                        FROM episodic_memories
                        WHERE character_id = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query, character_id, limit)
                
                memories = [
                    EpisodicMemoryDB(
                        id=row['id'],
                        character_id=row['character_id'],
                        session_id=row['session_id'],
                        content=row['content'],
                        memory_type=row['memory_type'],
                        importance_score=row['importance_score'],
                        entities=row['entities'],
                        location=row['location'],
                        created_at=row['created_at']
                    )
                    for row in rows
                ]
                
                logger.info(f"Retrieved {len(memories)} recent memories")
                return memories
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting recent memories: {e}", exc_info=True)
            return []
    
    async def get_memory_by_id(self, memory_id: UUID) -> Optional[EpisodicMemoryDB]:
        """Get specific memory by ID."""
        try:
            conn = await get_db_connection()
            try:
                query = """
                    SELECT id, character_id, session_id, content, memory_type,
                           importance_score, entities, location, created_at
                    FROM episodic_memories
                    WHERE id = $1
                """
                row = await conn.fetchrow(query, memory_id)
                
                if row:
                    return EpisodicMemoryDB(
                        id=row['id'],
                        character_id=row['character_id'],
                        session_id=row['session_id'],
                        content=row['content'],
                        memory_type=row['memory_type'],
                        importance_score=row['importance_score'],
                        entities=row['entities'],
                        location=row['location'],
                        created_at=row['created_at']
                    )
                return None
                
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error getting memory: {e}", exc_info=True)
            return None


# Global instance
episodic_memory_manager = EpisodicMemoryManager()
