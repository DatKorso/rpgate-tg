"""Tests for full reset character flow."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery, Message, User
from aiogram.fsm.context import FSMContext

from app.bot.handlers import (
    callback_full_reset,
    callback_confirm_full_reset,
    callback_cancel_full_reset,
)
from app.game.character import CharacterSheet
from app.config.prompts import UIPrompts


@pytest.fixture
def existing_character():
    return CharacterSheet(
        telegram_user_id=999,
        name="OldHero",
        strength=8,
        dexterity=9,
        constitution=10,
        intelligence=11,
        wisdom=12,
        charisma=13,
        hp=5,
        max_hp=25,
        armor_class=10,
        location="old_cave"
    )


def _mock_callback(data: str, user_id: int = 999):
    cb = MagicMock(spec=CallbackQuery)
    cb.data = data
    cb.answer = AsyncMock()
    user = MagicMock(spec=User)
    user.id = user_id
    user.first_name = "Player"
    cb.from_user = user
    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock()
    cb.message = msg
    return cb


@pytest.mark.asyncio
async def test_full_reset_warning_shown(existing_character):
    cb = _mock_callback("full_reset")
    state = MagicMock(spec=FSMContext)
    with patch("app.bot.handlers.get_character_by_telegram_id") as mock_get:
        mock_get.return_value = existing_character
        await callback_full_reset(cb, state)
    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    assert UIPrompts.FULL_RESET_WARNING in cb.message.edit_text.call_args[0][0]


@pytest.mark.asyncio
async def test_full_reset_confirm_deletes_character(existing_character):
    cb = _mock_callback("confirm_full_reset")
    state = MagicMock(spec=FSMContext)
    state.clear = AsyncMock()
    state.set_state = AsyncMock()
    with patch("app.bot.handlers.get_character_by_telegram_id") as mock_get, \
         patch("app.bot.handlers.delete_character") as mock_delete:
        mock_get.return_value = existing_character
        mock_delete.return_value = True
        await callback_confirm_full_reset(cb, state)
    mock_delete.assert_called_once_with(existing_character.id)
    state.clear.assert_called_once()
    cb.message.edit_text.assert_called_once()
    text_sent = cb.message.edit_text.call_args[0][0]
    assert UIPrompts.FULL_RESET_DONE.split("\n\n")[0] in text_sent
    # Ensure class selection buttons exist (warrior button)
    kwargs = cb.message.edit_text.call_args[1]
    markup = kwargs.get("reply_markup")
    assert markup is not None
    warrior_button = any(btn.callback_data == "class_warrior" for row in markup.inline_keyboard for btn in row)
    assert warrior_button, "Warrior class selection button missing after full reset"


@pytest.mark.asyncio
async def test_full_reset_cancel(existing_character):
    cb = _mock_callback("cancel_full_reset")
    state = MagicMock(spec=FSMContext)
    with patch("app.bot.handlers.get_character_by_telegram_id") as mock_get:
        mock_get.return_value = existing_character
        await callback_cancel_full_reset(cb, state)
    cb.answer.assert_called_once()
    cb.message.edit_text.assert_called_once()
    assert UIPrompts.FULL_RESET_CANCELLED in cb.message.edit_text.call_args[0][0]
