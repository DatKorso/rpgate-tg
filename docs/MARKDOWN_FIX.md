# Markdown Parsing Fix

## Проблема

При отправке текстовых сообщений боту возникала ошибка:

```
TelegramBadRequest: Telegram server says - Bad Request: can't parse entities: 
Can't find end of the entity starting at byte offset 1146
```

**Причина:** Narrative Director генерирует текст через LLM, который может вернуть невалидный Markdown (незакрытые `**`, `_`, `[`, специальные символы и т.д.). Telegram не может распарсить такой текст.

## Решение

### 1. Sanitization в Response Synthesizer (`app/agents/response_synthesizer.py`)

Добавлена функция `_sanitize_markdown()`, которая исправляет типичные проблемы:

- **Незакрытые `**` (bold):** Удаляет лишний маркер, если их нечётное количество
- **Незакрытые `_` (italic/underline):** Экранирует все, если количество нечётное
- **Незакрытые `[` или `]` (ссылки):** Экранирует все скобки при дисбалансе
- **Незакрытые `` ` `` (код):** Экранирует, если количество нечётное
- **Одиночные `*`:** Экранирует, чтобы не конфликтовали с `**`

**Код:**
```python
def _sanitize_markdown(self, text: str) -> str:
    """Sanitize text to prevent Markdown parsing errors."""
    # Fixes for bold, italic, brackets, backticks
    # See implementation in response_synthesizer.py
```

Метод вызывается автоматически перед добавлением narrative в финальное сообщение.

### 2. Fallback в Handler (`app/bot/handlers.py`)

Добавлен try-except блок с fallback на plain text:

```python
try:
    await message.answer(final_message, parse_mode="Markdown")
except Exception as e:
    logger.warning(f"Markdown parsing failed: {e}. Sending as plain text.")
    await message.answer(final_message, parse_mode=None)
```

**Логика:**
1. Пытаемся отправить с Markdown
2. Если Telegram отклоняет (невалидный Markdown) → отправляем как plain text
3. Логируем предупреждение для отладки

## Тестирование

### Добавлены тесты (`tests/test_response_synthesizer.py`)

8 новых тестов покрывают:
- ✅ Незакрытые bold (`**`)
- ✅ Незакрытые brackets (`[`, `]`)
- ✅ Незакрытые underscores (`_`)
- ✅ Валидный Markdown проходит без изменений
- ✅ Форматирование статуса персонажа
- ✅ Форматирование критического удара
- ✅ Форматирование skill check
- ✅ Форматирование skill check с advantage

**Все тесты проходят:** 30/30 passed

## Что дальше

### Рекомендации по тестированию бота

1. **Протестируй различные narrative сценарии:**
   - Длинные описания с кавычками и спецсимволами
   - Тексты с множественными **bold** и _italic_
   - Сообщения с эмодзи и unicode

2. **Проверь edge cases:**
   - Очень длинные ответы (>4096 символов - лимит Telegram)
   - Пустые ответы от LLM
   - Ответы только с эмодзи

3. **Мониторинг логов:**
   Если видишь предупреждения `Markdown parsing failed` - это значит sanitization не сработал идеально. Надо:
   - Посмотреть, какой текст вызвал ошибку
   - Добавить дополнительные правила в `_sanitize_markdown()`

### Возможные улучшения (Sprint 3+)

1. **Использовать HTML вместо Markdown:**
   - HTML более предсказуем в Telegram
   - Легче экранировать: `html.escape(text)`
   - Меньше edge cases с nested форматированием

2. **Добавить post-processing в LLM промпты:**
   ```python
   system_prompt += "\n\nIMPORTANT: Always close Markdown tags (**bold**, *italic*). 
   Avoid using square brackets unless for links."
   ```

3. **Валидация длины сообщения:**
   ```python
   MAX_MESSAGE_LENGTH = 4096
   if len(final_message) > MAX_MESSAGE_LENGTH:
       # Split into chunks
   ```

## Файлы изменены

- ✅ `app/agents/response_synthesizer.py` - добавлен `_sanitize_markdown()`
- ✅ `app/bot/handlers.py` - добавлен fallback и logger
- ✅ `tests/test_response_synthesizer.py` - новый файл с тестами

## Использование

Изменения работают автоматически:
1. Narrative Director генерирует текст
2. Response Synthesizer автоматически sanitize-ит его
3. Handler отправляет с Markdown
4. Если ошибка → fallback на plain text

**Никаких дополнительных действий от разработчика не требуется.**
