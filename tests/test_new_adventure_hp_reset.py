"""Regression test: starting a new adventure resets HP and stats for existing character."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, User, Message
from aiogram.fsm.context import FSMContext

from app.game.character import CharacterSheet
from app.bot.handlers import callback_select_class


@pytest.mark.asyncio
async def test_new_adventure_resets_hp_and_stats():
    """If character already exists, selecting a class for new adventure should reset stats and HP."""
    # Existing character with reduced HP and different stats
    existing_character = CharacterSheet(
        telegram_user_id=111,
        name="OldHero",
        strength=8,
        dexterity=9,
        constitution=10,
        intelligence=11,
        wisdom=12,
        charisma=13,
        hp=5,
        max_hp=25,  # Warrior intended max
        armor_class=10,
        location="old_ruins"
    )

    # Mocks for DB operations
    with patch("app.bot.handlers.create_character") as mock_create, \
         patch("app.bot.handlers.get_character_by_telegram_id") as mock_get, \
         patch("app.bot.handlers.update_character") as mock_update:
        mock_create.return_value = False  # Simulate unique violation (character already exists)
        mock_get.return_value = existing_character
        mock_update.return_value = True

        # Mock CallbackQuery
        callback = MagicMock(spec=CallbackQuery)
        callback.data = "class_warrior"
        callback.answer = AsyncMock()

        user = MagicMock(spec=User)
        user.id = 111
        user.first_name = "Player"
        callback.from_user = user

        message = MagicMock(spec=Message)
        message.edit_text = AsyncMock()
        callback.message = message

        # Mock FSM state
        state = MagicMock(spec=FSMContext)
        state.update_data = AsyncMock()
        state.set_state = AsyncMock()

        # Execute handler
        await callback_select_class(callback, state)

        # Ensure update_character called with reset stats
        assert mock_update.called, "Character update was not called for existing character reset"
        updated_char = mock_update.call_args[0][0]

        # HP reset
        assert updated_char.hp == updated_char.max_hp == 25
        # Strength updated to warrior preset
        assert updated_char.strength == 16
        # Armor class updated
        assert updated_char.armor_class == 14
        # XP reset
        assert updated_char.xp == 0
        # Location updated
        assert updated_char.location == "ancient_ruins"

        # FSM character stored has full HP
        assert state.update_data.called
        stored_payload = state.update_data.call_args[1]["character"]
        assert stored_payload["hp"] == stored_payload["max_hp"] == 25

