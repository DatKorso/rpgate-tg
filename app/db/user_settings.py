"""CRUD operations for user_settings table (combat toggle)."""

from typing import Optional, Dict, Any
import logging

from app.db.supabase import get_db_connection

logger = logging.getLogger(__name__)


async def get_user_settings_by_telegram_id(telegram_user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch user settings by Telegram user ID.

    Returns dict: {"telegram_user_id": int, "combat_enabled": bool} or None.
    """
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            """
            SELECT telegram_user_id, combat_enabled
            FROM user_settings
            WHERE telegram_user_id = $1
            """,
            telegram_user_id,
        )
        if not row:
            return None
        return {
            "telegram_user_id": row["telegram_user_id"],
            "combat_enabled": row["combat_enabled"],
        }
    except Exception as e:
        logger.error(f"Error loading user settings: {e}", exc_info=True)
        return None
    finally:
        await conn.close()


async def create_or_update_user_settings(telegram_user_id: int, combat_enabled: bool = True) -> Dict[str, Any]:
    """Create settings row or update existing one.

    Returns dict with current values.
    """
    conn = await get_db_connection()
    try:
        await conn.execute(
            """
            INSERT INTO user_settings (telegram_user_id, combat_enabled)
            VALUES ($1, $2)
            ON CONFLICT (telegram_user_id)
            DO UPDATE SET combat_enabled = EXCLUDED.combat_enabled, updated_at = NOW()
            """,
            telegram_user_id,
            combat_enabled,
        )
        return {"telegram_user_id": telegram_user_id, "combat_enabled": combat_enabled}
    except Exception as e:
        logger.error(f"Error creating/updating user settings: {e}", exc_info=True)
        return {"telegram_user_id": telegram_user_id, "combat_enabled": combat_enabled}
    finally:
        await conn.close()


async def update_combat_enabled(telegram_user_id: int, enabled: bool) -> bool:
    """Update combat_enabled flag.

    Returns True on success.
    """
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            """
            UPDATE user_settings
            SET combat_enabled = $2, updated_at = NOW()
            WHERE telegram_user_id = $1
            """,
            telegram_user_id,
            enabled,
        )
        if result == "UPDATE 0":
            # Row does not exist yet, create it
            await conn.execute(
                """
                INSERT INTO user_settings (telegram_user_id, combat_enabled)
                VALUES ($1, $2)
                """,
                telegram_user_id,
                enabled,
            )
        return True
    except Exception as e:
        logger.error(f"Error updating combat_enabled: {e}", exc_info=True)
        return False
    finally:
        await conn.close()
