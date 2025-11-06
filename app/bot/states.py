"""
Finite State Machine states для управления диалогом бота.
"""
from aiogram.fsm.state import State, StatesGroup


class ConversationState(StatesGroup):
    """States для основного диалога с игроком."""
    
    # Начальное состояние - ожидание команды /start
    idle = State()
    
    # Игрок в активном диалоге с GM
    in_conversation = State()
    
    # Игрок создает нового персонажа (для будущих спринтов)
    creating_character = State()
