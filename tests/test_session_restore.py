"""
Test session restoration after bot restart.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext

from app.bot.handlers import handle_any_message
from app.bot.states import ConversationState
from app.game.character import CharacterSheet


@pytest.fixture
def mock_message():
    """Create mock message."""
    message = MagicMock(spec=Message)
    message.text = "Иду на север"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 123456
    message.from_user.first_name = "TestUser"
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456
    message.answer = AsyncMock()
    message.bot = MagicMock()
    message.bot.send_chat_action = AsyncMock()
    return message


@pytest.fixture
def mock_state():
    """Create mock FSM context."""
    state = MagicMock(spec=FSMContext)
    state.get_state = AsyncMock(return_value=None)  # Simulate restart - no state
    state.set_state = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    state.update_data = AsyncMock()
    return state


@pytest.fixture
def test_character():
    """Create test character."""
    return CharacterSheet(
        id=uuid4(),
        telegram_user_id=123456,
        name="TestUser",
        strength=16,
        hp=25,
        max_hp=25,
        armor_class=14
    )


@pytest.mark.asyncio
async def test_session_restore_with_existing_character(mock_message, mock_state, test_character):
    """Test that session is restored when character exists in DB."""
    
    with patch("app.bot.handlers.get_character_by_telegram_id") as mock_get_char, \
         patch("app.bot.handlers.handle_conversation") as mock_handle_conv:
        
        mock_get_char.return_value = test_character
        mock_handle_conv.return_value = None
        
        # Call handler
        await handle_any_message(mock_message, mock_state)
        
        # Verify character was loaded
        mock_get_char.assert_called_once_with(123456)
        
        # Verify state was restored
        mock_state.set_state.assert_called_once_with(ConversationState.in_conversation)
        
        # Verify conversation handler was called
        mock_handle_conv.assert_called_once_with(mock_message, mock_state)


@pytest.mark.asyncio
async def test_session_no_restore_without_character(mock_message, mock_state):
    """Test that welcome message is shown when no character exists."""
    
    with patch("app.bot.handlers.get_character_by_telegram_id") as mock_get_char:
        mock_get_char.return_value = None
        
        # Call handler
        await handle_any_message(mock_message, mock_state)
        
        # Verify character was checked
        mock_get_char.assert_called_once_with(123456)
        
        # Verify state was NOT restored
        mock_state.set_state.assert_not_called()
        
        # Verify welcome message was sent
        mock_message.answer.assert_called_once()
        assert "Используй /start" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_session_already_in_conversation(mock_message, mock_state, test_character):
    """Test that state is not changed if already in conversation."""
    
    # Simulate already in conversation state
    mock_state.get_state = AsyncMock(return_value=ConversationState.in_conversation)
    
    with patch("app.bot.handlers.get_character_by_telegram_id") as mock_get_char, \
         patch("app.bot.handlers.handle_conversation") as mock_handle_conv:
        
        mock_get_char.return_value = test_character
        mock_handle_conv.return_value = None
        
        # Call handler
        await handle_any_message(mock_message, mock_state)
        
        # Verify state was NOT changed (already correct)
        mock_state.set_state.assert_not_called()
        
        # Verify conversation handler was still called
        mock_handle_conv.assert_called_once_with(mock_message, mock_state)
