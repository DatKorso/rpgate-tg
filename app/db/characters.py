"""CRUD operations for characters table."""
import logging
import json
from typing import Optional
from uuid import UUID
from datetime import datetime
import asyncpg

from app.game.character import CharacterSheet
from app.db.supabase import get_db_connection

logger = logging.getLogger(__name__)


async def get_character_by_telegram_id(telegram_user_id: int) -> Optional[CharacterSheet]:
    """
    Load character from database by Telegram user ID.
    
    Args:
        telegram_user_id: User's Telegram ID
        
    Returns:
        CharacterSheet instance or None if not found
    """
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT id, telegram_user_id, name, character_sheet, created_at, updated_at, last_session_at
            FROM characters
            WHERE telegram_user_id = $1
            """,
            telegram_user_id
        )
        
        if not row:
            logger.info(f"No character found for telegram_user_id={telegram_user_id}")
            return None
        
        # Deserialize character_sheet JSON to CharacterSheet
        # asyncpg may return JSONB as string, parse it
        character_sheet_data = row["character_sheet"]
        if isinstance(character_sheet_data, str):
            character_sheet_data = json.loads(character_sheet_data)
        
        character_data = character_sheet_data.copy()
        character_data["id"] = row["id"]
        character_data["telegram_user_id"] = row["telegram_user_id"]
        character_data["name"] = row["name"]
        
        character = CharacterSheet(**character_data)
        logger.info(f"Loaded character {character.name} (ID: {character.id})")
        return character
        
    except Exception as e:
        logger.error(f"Error loading character: {e}", exc_info=True)
        return None
    finally:
        await conn.close()


async def create_character(character: CharacterSheet) -> bool:
    """
    Create new character in database.
    
    Args:
        character: CharacterSheet instance
        
    Returns:
        True if successful, False otherwise
    """
    conn = await get_db_connection()
    try:
        # Serialize character to JSON (exclude id, telegram_user_id, name - they're separate columns)
        character_sheet_json = character.model_dump(
            exclude={"id", "telegram_user_id", "name"}
        )
        
        # Convert to JSON string for JSONB column
        import json
        character_sheet_str = json.dumps(character_sheet_json)
        
        await conn.execute(
            """
            INSERT INTO characters (id, telegram_user_id, name, character_sheet, last_session_at)
            VALUES ($1, $2, $3, $4::jsonb, $5)
            """,
            character.id,
            character.telegram_user_id,
            character.name,
            character_sheet_str,
            datetime.now()
        )
        
        logger.info(f"Created character {character.name} (ID: {character.id})")
        return True
        
    except asyncpg.UniqueViolationError:
        logger.warning(f"Character already exists for telegram_user_id={character.telegram_user_id}")
        return False
    except Exception as e:
        logger.error(f"Error creating character: {e}", exc_info=True)
        return False
    finally:
        await conn.close()


async def update_character(character: CharacterSheet) -> bool:
    """
    Update existing character in database.
    
    Args:
        character: CharacterSheet instance with updated data
        
    Returns:
        True if successful, False otherwise
    """
    conn = await get_db_connection()
    try:
        # Serialize character to JSON
        character_sheet_json = character.model_dump(
            exclude={"id", "telegram_user_id", "name"}
        )
        
        # Convert to JSON string for JSONB column
        import json
        character_sheet_str = json.dumps(character_sheet_json)
        
        result = await conn.execute(
            """
            UPDATE characters
            SET name = $2, character_sheet = $3::jsonb, last_session_at = $4
            WHERE id = $1
            """,
            character.id,
            character.name,
            character_sheet_str,
            datetime.now()
        )
        
        if result == "UPDATE 0":
            logger.warning(f"Character {character.id} not found for update")
            return False
        
        logger.info(f"Updated character {character.name} (ID: {character.id})")
        return True
        
    except Exception as e:
        logger.error(f"Error updating character: {e}", exc_info=True)
        return False
    finally:
        await conn.close()


async def delete_character(character_id: UUID) -> bool:
    """
    Delete character from database.
    
    Args:
        character_id: Character UUID
        
    Returns:
        True if successful, False otherwise
    """
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            """
            DELETE FROM characters WHERE id = $1
            """,
            character_id
        )
        
        if result == "DELETE 0":
            logger.warning(f"Character {character_id} not found for deletion")
            return False
        
        logger.info(f"Deleted character {character_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting character: {e}", exc_info=True)
        return False
    finally:
        await conn.close()


async def get_or_create_character(
    telegram_user_id: int,
    character: CharacterSheet
) -> CharacterSheet:
    """
    Get existing character or create new one if not exists.
    
    Args:
        telegram_user_id: User's Telegram ID
        character: CharacterSheet to create if not exists
        
    Returns:
        CharacterSheet instance (existing or newly created)
    """
    existing = await get_character_by_telegram_id(telegram_user_id)
    if existing:
        return existing
    
    success = await create_character(character)
    if success:
        return character
    
    # If creation failed (race condition), try to load again
    existing = await get_character_by_telegram_id(telegram_user_id)
    if existing:
        return existing
    
    # Fallback: return the provided character (in-memory only)
    logger.error(f"Failed to create or load character for telegram_user_id={telegram_user_id}")
    return character
