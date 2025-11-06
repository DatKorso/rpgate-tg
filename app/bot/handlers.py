"""
Telegram bot handlers для обработки сообщений пользователя.
"""
import asyncio
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states import ConversationState
from app.llm.client import llm_client


# Router для всех handlers
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """
    Handler для команды /start - инициализация бота.
    """
    await state.set_state(ConversationState.in_conversation)
    await message.answer(
        "🎲 Welcome, adventurer! I am your AI Game Master.\n\n"
        "Tell me what you want to do, and I'll narrate your story.\n"
        "Type /help for available commands."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """
    Handler для команды /help - показать доступные команды.
    """
    help_text = (
        "🎮 **Available Commands:**\n\n"
        "/start - Start or restart conversation\n"
        "/help - Show this help message\n"
        "/reset - Clear conversation history\n"
        "/ping - Check bot status\n\n"
        "Just send me a message to continue your adventure!"
    )
    await message.answer(help_text, parse_mode="Markdown")


@router.message(Command("ping"))
async def cmd_ping(message: Message):
    """
    Handler для команды /ping - проверка работоспособности бота.
    """
    await message.answer("🟢 Bot is online and ready!")



@router.message(Command("reset"))
async def cmd_reset(message: Message, state: FSMContext):
    """
    Handler для команды /reset - очистка истории и сброс состояния.
    """
    await state.clear()
    await state.set_state(ConversationState.idle)
    await message.answer("✨ Conversation reset! Use /start to begin a new adventure.")


@router.message(
    ConversationState.in_conversation,
    F.text  # Только текстовые сообщения
)
async def handle_conversation(message: Message, state: FSMContext):
    """
    Main handler для диалога с игроком в активном состоянии.
    Отправляет сообщение пользователя в LLM и возвращает ответ.
    """
    user_message = message.text
    
    # Получаем историю из FSM context (пока простая реализация)
    data = await state.get_data()
    conversation_history = data.get("history", [])
    
    # Добавляем системный промпт (базовый для MVP)
    if not conversation_history:
        conversation_history.append({
            "role": "system",
            "content": (
                "Вы опытный гейм-мастер, управляющий фэнтезийной ролевой игрой."
                "Рассказывайте историю живо, реагируйте на действия игроков и создавайте захватывающие сценарии."
                "Пусть ваши ответы будут лаконичными (максимум 2–3 абзаца)."
            )
        })
    
    # Добавляем сообщение пользователя
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Запускаем typing indicator в фоне
    typing_task = asyncio.create_task(
        _send_typing_indicator(message)
    )
    
    try:
        # Получаем ответ от LLM
        gm_response = await llm_client.get_completion(
            messages=conversation_history,
            temperature=0.8,  # Creativity для narrative
            max_tokens=600,
        )
    finally:
        # Останавливаем typing indicator
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    # Добавляем ответ GM в историю
    conversation_history.append({
        "role": "assistant",
        "content": gm_response
    })
    
    # Сохраняем обновленную историю (ограничение: последние 10 сообщений)
    if len(conversation_history) > 21:  # system + 10 pairs
        conversation_history = [conversation_history[0]] + conversation_history[-20:]
    
    await state.update_data(history=conversation_history)
    
    # Отправляем ответ игроку
    await message.answer(gm_response)


@router.message(ConversationState.idle)
async def handle_idle_state(message: Message):
    """
    Handler для сообщений в idle состоянии.
    Предлагает пользователю начать с /start.
    """
    await message.answer(
        "👋 Hey there! Use /start to begin your adventure, "
        "or /help to see available commands."
    )


async def _send_typing_indicator(message: Message):
    """
    Вспомогательная функция для отправки typing indicator в цикле.
    Запускается как фоновая задача и отменяется после получения ответа от LLM.
    """
    try:
        while True:
            await message.bot.send_chat_action(
                chat_id=message.chat.id,
                action="typing"
            )
            # Typing indicator живет ~5 секунд, обновляем каждые 4 секунды
            await asyncio.sleep(4)
    except asyncio.CancelledError:
        # Нормальное завершение при отмене задачи
        pass
