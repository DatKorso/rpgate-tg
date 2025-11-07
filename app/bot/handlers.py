"""
Telegram bot handlers для обработки сообщений пользователя.
"""
import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from app.bot.states import ConversationState
from app.agents.orchestrator import AgentOrchestrator
from app.game.character import CharacterSheet
from app.config.prompts import UIPrompts, CombatPrompts
from app.db.characters import get_character_by_telegram_id, create_character, update_character
from app.db.sessions import get_or_create_session, update_session_stats
from app.agents.world_state import world_state_agent


# Logger
logger = logging.getLogger(__name__)

# Router для всех handlers
router = Router()

# Global orchestrator instance
orchestrator = AgentOrchestrator()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handler для команды /start с inline keyboard."""
    await state.set_state(ConversationState.idle)
    
    # Create inline keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Новое приключение", callback_data="new_adventure")],
        [InlineKeyboardButton(text="📖 Продолжить игру", callback_data="continue_game")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="show_help")]
    ])
    
    await message.answer(
        UIPrompts.WELCOME,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "new_adventure")
async def callback_new_adventure(callback: CallbackQuery, state: FSMContext):
    """Start character creation."""
    await callback.answer()
    
    # Create class selection keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Воин", callback_data="class_warrior")],
        [InlineKeyboardButton(text="🏹 Следопыт", callback_data="class_ranger")],
        [InlineKeyboardButton(text="🔮 Маг", callback_data="class_mage")],
        [InlineKeyboardButton(text="🗡️ Плут", callback_data="class_rogue")]
    ])
    
    await callback.message.edit_text(
        UIPrompts.CHARACTER_CREATION,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "continue_game")
async def callback_continue_game(callback: CallbackQuery, state: FSMContext):
    """Continue existing game."""
    await callback.answer()
    
    data = await state.get_data()
    character_data = data.get("character")
    
    if not character_data:
        await callback.message.edit_text(
            "❌ У тебя ещё нет персонажа. Создай нового героя!",
            parse_mode="Markdown"
        )
        return
    
    await state.set_state(ConversationState.in_conversation)
    await callback.message.edit_text(
        "📖 **Игра продолжается!**\n\nЧто ты хочешь сделать?",
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "show_help")
async def callback_show_help(callback: CallbackQuery):
    """Show help message."""
    await callback.answer()
    await callback.message.edit_text(UIPrompts.HELP, parse_mode="Markdown")


@router.callback_query(F.data.startswith("class_"))
async def callback_select_class(callback: CallbackQuery, state: FSMContext):
    """Handle class selection and create character in DB."""
    await callback.answer()
    
    if not callback.data:
        return
    
    class_name = callback.data.replace("class_", "")
    
    # Create character with class-specific stats
    class_stats = {
        "warrior": {
            "strength": 16, 
            "constitution": 14, 
            "hp": 25, 
            "max_hp": 25,
            "armor_class": 14,
            "class_name": "Воин",
            "emoji": "⚔️"
        },
        "ranger": {
            "dexterity": 16, 
            "wisdom": 14, 
            "hp": 22, 
            "max_hp": 22,
            "armor_class": 13,
            "class_name": "Следопыт",
            "emoji": "🏹"
        },
        "mage": {
            "intelligence": 16, 
            "wisdom": 14, 
            "hp": 16, 
            "max_hp": 16,
            "armor_class": 10,
            "class_name": "Маг",
            "emoji": "🔮"
        },
        "rogue": {
            "dexterity": 16, 
            "charisma": 14, 
            "hp": 18, 
            "max_hp": 18,
            "armor_class": 12,
            "class_name": "Плут",
            "emoji": "🗡️"
        },
    }
    
    stats = class_stats.get(class_name, class_stats["warrior"])
    telegram_user_id = callback.from_user.id if callback.from_user else 0
    user_name = callback.from_user.first_name if callback.from_user else "Искатель приключений"
    
    # Create character
    character = CharacterSheet(
        telegram_user_id=telegram_user_id,
        name=user_name,
        strength=stats.get("strength", 10),
        dexterity=stats.get("dexterity", 10),
        constitution=stats.get("constitution", 10),
        intelligence=stats.get("intelligence", 10),
        wisdom=stats.get("wisdom", 10),
        charisma=stats.get("charisma", 10),
        hp=stats["hp"],
        max_hp=stats["max_hp"],
        armor_class=stats["armor_class"],
        location="ancient_ruins"
    )
    
    # Save character to database
    success = await create_character(character)
    
    if not success:
        logger.warning(f"Character already exists for user {telegram_user_id}, loading existing")
        # Load existing character
        existing_character = await get_character_by_telegram_id(telegram_user_id)
        if existing_character:
            character = existing_character
    
    # Initialize game state (will be saved to DB on first action)
    game_state = {
        "in_combat": False,
        "enemies": [],
        "location": "ancient_ruins",
        "combat_ended": False
    }
    
    # Save to FSM state (backward compatibility)
    await state.update_data(
        character=character.model_dump_for_storage(),
        game_state=game_state,
        history=[]
    )
    await state.set_state(ConversationState.in_conversation)
    
    # Format character sheet message
    intro_scene = UIPrompts.INTRO_SCENES.get(class_name, UIPrompts.INTRO_SCENES["warrior"])
    
    message_text = UIPrompts.CHARACTER_SHEET.format(
        emoji=stats["emoji"],
        name=character.name,
        class_name=stats["class_name"],
        hp=character.hp,
        max_hp=character.max_hp,
        strength=character.strength,
        strength_mod=character.strength_mod,
        dexterity=character.dexterity,
        dexterity_mod=character.dexterity_mod,
        constitution=character.constitution,
        constitution_mod=character.constitution_mod,
        intelligence=character.intelligence,
        intelligence_mod=character.intelligence_mod,
        wisdom=character.wisdom,
        wisdom_mod=character.wisdom_mod,
        charisma=character.charisma,
        charisma_mod=character.charisma_mod,
        intro_scene=intro_scene
    )
    
    if callback.message:
        await callback.message.edit_text(message_text, parse_mode="Markdown")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handler для команды /help."""
    await message.answer(UIPrompts.HELP, parse_mode="Markdown")


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    """Handler для команды /ping."""
    await message.answer("🟢 Bot is online and ready!")

@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """Handler для команды /reset."""
    await state.clear()
    await state.set_state(ConversationState.idle)
    await message.answer("✨ Игра сброшена! Используй /start для нового приключения.")


@router.message(ConversationState.in_conversation, F.text)
async def handle_conversation(message: Message, state: FSMContext):
    """Main handler with database integration (Sprint 3)."""
    user_message = message.text
    
    if not user_message:
        await message.answer(UIPrompts.ERROR_GENERIC)
        return
    
    telegram_user_id = message.from_user.id if message.from_user else 0
    
    # Load character from database instead of FSM
    character = await get_character_by_telegram_id(telegram_user_id)
    
    if not character:
        # Fallback: check FSM for in-memory character (backward compatibility)
        data = await state.get_data()
        character_data = data.get("character")
        
        if character_data:
            character = CharacterSheet(**character_data)
        else:
            await message.answer(UIPrompts.ERROR_NO_CHARACTER)
            return
    
    # Get or create session
    session_id = await get_or_create_session(character.id)
    
    # Load game state from World State Agent
    game_state = await world_state_agent.load_world_state(character.id)
    
    # Get history from FSM (will be migrated to DB in future)
    data = await state.get_data()
    history = data.get("history", [])
    recent_messages = [msg["content"] for msg in history[-5:] if msg["role"] == "assistant"]
    
    # Typing indicator
    typing_task = asyncio.create_task(_send_typing_indicator(message))
    
    try:
        # Process через orchestrator with DB integration
        final_message, updated_character, updated_game_state = await orchestrator.process_action(
            user_action=user_message,
            character=character,
            game_state=game_state,
            character_id=character.id,  # For memory retrieval
            session_id=session_id,  # For memory context
            recent_history=recent_messages
        )
    except Exception as e:
        logger.error(f"Error processing action: {e}", exc_info=True)
        await message.answer(UIPrompts.ERROR_GENERIC)
        return
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    # Check combat state changes
    if not game_state.get("in_combat") and updated_game_state.get("in_combat"):
        # Combat started
        final_message = f"{CombatPrompts.COMBAT_START}\n\n{final_message}"
    elif game_state.get("in_combat") and updated_game_state.get("combat_ended"):
        # Combat ended
        final_message = f"{final_message}\n\n{CombatPrompts.COMBAT_END}"
    
    # Check death
    if not updated_character.is_alive():
        final_message = f"{final_message}\n\n{CombatPrompts.PLAYER_DEATH}"
        await state.clear()  # Reset game
    
    # Save updated character to database
    await update_character(updated_character)
    
    # Update session stats
    damage_dealt = 0
    damage_taken = 0
    
    # Extract damage from enemy attacks
    enemy_attacks = updated_game_state.get("enemy_attacks", [])
    damage_taken = sum(attack.get("damage", 0) for attack in enemy_attacks)
    
    await update_session_stats(
        session_id=session_id,
        turns_increment=1,
        damage_dealt_increment=damage_dealt,
        damage_taken_increment=damage_taken
    )
    
    # Update history in FSM (temporary until we migrate to DB)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": final_message})
    
    if len(history) > 20:
        history = history[-20:]
    
    await state.update_data(history=history)
    
    # Send response with fallback for invalid Markdown
    try:
        await message.answer(final_message, parse_mode="Markdown")
    except Exception as e:
        error_msg = str(e)
        logger.warning(
            f"Markdown parsing failed: {error_msg}. "
            f"Message length: {len(final_message)} chars. "
            f"Sending as plain text."
        )
        
        # Log problematic section if byte offset is mentioned
        if "byte offset" in error_msg:
            try:
                import re
                match = re.search(r'byte offset (\d+)', error_msg)
                if match:
                    offset = int(match.group(1))
                    # Log context around the problematic byte
                    start = max(0, offset - 50)
                    end = min(len(final_message), offset + 50)
                    context = final_message[start:end]
                    logger.warning(f"Problematic section (bytes {start}-{end}): {repr(context)}")
            except Exception:
                pass
        
        # Send without Markdown parsing
        await message.answer(final_message)
        # Fallback: send as plain text without formatting
        await message.answer(final_message, parse_mode=None)


@router.message(ConversationState.idle)
async def handle_idle_state(message: Message):
    """Handler для сообщений в idle состоянии."""
    await message.answer(
        "👋 Привет! Используй /start чтобы начать приключение."
    )


async def _send_typing_indicator(message: Message):
    """Send typing indicator in loop until cancelled."""
    try:
        while True:
            if message.bot:
                await message.bot.send_chat_action(
                    chat_id=message.chat.id,
                    action="typing"
                )
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        pass
