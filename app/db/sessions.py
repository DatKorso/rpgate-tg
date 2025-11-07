"""CRUD operations for game_sessions table."""
import logging
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
import asyncpg

from app.db.supabase import get_db_connection

logger = logging.getLogger(__name__)


async def create_session(character_id: UUID) -> Optional[UUID]:
    """
    Create new game session.
    
    Args:
        character_id: Character UUID
        
    Returns:
        Session ID (UUID) or None if failed
    """
    conn = await get_db_connection()
    try:
        session_id = uuid4()
        await conn.execute(
            """
            INSERT INTO game_sessions (id, character_id, started_at, turns_count)
            VALUES ($1, $2, $3, 0)
            """,
            session_id,
            character_id,
            datetime.now()
        )
        
        logger.info(f"Created session {session_id} for character {character_id}")
        return session_id
        
    except Exception as e:
        logger.error(f"Error creating session: {e}", exc_info=True)
        return None
    finally:
        await conn.close()


async def get_active_session(character_id: UUID) -> Optional[UUID]:
    """
    Get active (not ended) session for character.
    
    Args:
        character_id: Character UUID
        
    Returns:
        Session ID or None if no active session
    """
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT id FROM game_sessions
            WHERE character_id = $1 AND ended_at IS NULL
            ORDER BY started_at DESC
            LIMIT 1
            """,
            character_id
        )
        
        if row:
            logger.info(f"Found active session {row['id']} for character {character_id}")
            return row["id"]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting active session: {e}", exc_info=True)
        return None
    finally:
        await conn.close()


async def end_session(session_id: UUID) -> bool:
    """
    Mark session as ended.
    
    Args:
        session_id: Session UUID
        
    Returns:
        True if successful, False otherwise
    """
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            """
            UPDATE game_sessions
            SET ended_at = $2
            WHERE id = $1 AND ended_at IS NULL
            """,
            session_id,
            datetime.now()
        )
        
        if result == "UPDATE 0":
            logger.warning(f"Session {session_id} not found or already ended")
            return False
        
        logger.info(f"Ended session {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error ending session: {e}", exc_info=True)
        return False
    finally:
        await conn.close()


async def update_session_stats(
    session_id: UUID,
    turns_increment: int = 0,
    damage_dealt_increment: int = 0,
    damage_taken_increment: int = 0
) -> bool:
    """
    Update session statistics (incremental).
    
    Args:
        session_id: Session UUID
        turns_increment: Number of turns to add
        damage_dealt_increment: Damage dealt to add
        damage_taken_increment: Damage taken to add
        
    Returns:
        True if successful, False otherwise
    """
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            """
            UPDATE game_sessions
            SET 
                turns_count = turns_count + $2,
                total_damage_dealt = total_damage_dealt + $3,
                total_damage_taken = total_damage_taken + $4
            WHERE id = $1
            """,
            session_id,
            turns_increment,
            damage_dealt_increment,
            damage_taken_increment
        )
        
        if result == "UPDATE 0":
            logger.warning(f"Session {session_id} not found for stats update")
            return False
        
        logger.debug(f"Updated stats for session {session_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating session stats: {e}", exc_info=True)
        return False
    finally:
        await conn.close()


async def get_or_create_session(character_id: UUID) -> UUID:
    """
    Get active session or create new one if not exists.
    
    Args:
        character_id: Character UUID
        
    Returns:
        Session ID (UUID)
    """
    session_id = await get_active_session(character_id)
    if session_id:
        return session_id
    
    session_id = await create_session(character_id)
    if session_id:
        return session_id
    
    # Fallback: return a new UUID (in-memory session)
    logger.error(f"Failed to create session for character {character_id}, using in-memory ID")
    return uuid4()


async def get_session_stats(session_id: UUID) -> Optional[dict]:
    """
    Get session statistics.
    
    Args:
        session_id: Session UUID
        
    Returns:
        Dict with stats or None if not found
    """
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT turns_count, total_damage_dealt, total_damage_taken, started_at, ended_at
            FROM game_sessions
            WHERE id = $1
            """,
            session_id
        )
        
        if not row:
            return None
        
        return {
            "turns_count": row["turns_count"],
            "total_damage_dealt": row["total_damage_dealt"],
            "total_damage_taken": row["total_damage_taken"],
            "started_at": row["started_at"],
            "ended_at": row["ended_at"]
        }
        
    except Exception as e:
        logger.error(f"Error getting session stats: {e}", exc_info=True)
        return None
    finally:
        await conn.close()
