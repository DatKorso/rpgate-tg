#!/usr/bin/env python3
"""
Скрипт для проверки настройки проекта перед запуском бота.
"""
import sys
from pathlib import Path


def check_env_file():
    """Проверка наличия и корректности .env файла."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ Файл .env не найден!")
        print("   Создайте его: cp .env.example .env")
        return False
    
    with open(env_path) as f:
        content = f.read()
    
    if "your_telegram_bot_token_here" in content:
        print("❌ TELEGRAM_BOT_TOKEN не настроен в .env")
        print("   Получите токен у @BotFather и замените значение в .env")
        return False
    
    if "your_openrouter_api_key_here" in content:
        print("❌ OPENROUTER_API_KEY не настроен в .env")
        print("   Получите ключ на https://openrouter.ai/keys и замените значение в .env")
        return False
    
    print("✅ Файл .env настроен")
    return True


def check_dependencies():
    """Проверка установки зависимостей."""
    try:
        import aiogram
        import openai
        import pydantic_settings
        print("✅ Все зависимости установлены")
        return True
    except ImportError as e:
        print(f"❌ Не установлены зависимости: {e}")
        print("   Запустите: uv sync")
        return False


def check_modules():
    """Проверка импорта модулей приложения."""
    try:
        from app.config import settings
        from app.llm.client import llm_client
        from app.bot.states import ConversationState
        from app.bot.handlers import router
        from app.main import main, async_main
        print("✅ Все модули приложения работают")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта модулей: {e}")
        return False


def main():
    """Основная функция проверки."""
    print("🔍 Проверка настройки проекта rpgate-tg\n")
    
    checks = [
        ("Файл .env", check_env_file),
        ("Зависимости", check_dependencies),
        ("Модули приложения", check_modules),
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\nПроверка: {name}")
        if not check_func():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✅ Все проверки пройдены! Бот готов к запуску.")
        print("\nЗапустите бота:")
        print("  uv run python -m app.main")
        print("  или")
        print("  uv run start")
        return 0
    else:
        print("❌ Некоторые проверки не пройдены.")
        print("\nИсправьте ошибки и запустите проверку снова:")
        print("  uv run python check_setup.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
