# --- DEPRECATED: Consolidated into CHANGELOG.md. Use CHANGELOG.md for authoritative fix history. ---
# Исправление проблемы с JSON в итоговом сообщении

## Проблема

При запросе пользователя: "Пытаюсь аккуратно узнать, какой источник у звуков"

Бот возвращал:
```
🎲 **Проверка Восприятие** [8+0 = 8] vs DC 15 ❌ Провал

Ты затаиваешь дыхание, напрягая слух...

{"in_combat": false, "enemies": [], "combat_ended": false}  ← ЭТО НЕ ДОЛЖНО БЫТЬ ВИДНО

❤️ **HP:** 25/25 | 📍 **Локация:** ancient_ruins
```

**Причина:** Агент `NarrativeDirector` возвращал JSON с информацией о combat state, но парсер не мог его правильно извлечь, и JSON попадал в итоговое сообщение пользователю.

**Дополнительная проблема:** Telegram выдавал ошибку `TelegramBadRequest: can't parse entities: Can't find end of the entity starting at byte offset 1146` из-за незакрытых форматирующих тегов Markdown.

---

## Корневые причины

### 1. Недостаточно надёжный парсинг JSON в `NarrativeDirector`

**Файл:** `app/agents/narrative_director.py`

Метод `_parse_narrative_response()` искал только JSON с префиксом `COMBAT_STATE:`:

```python
match = re.search(r'COMBAT_STATE:\s*({.*})', response, re.IGNORECASE | re.DOTALL)
```

**Проблема:** LLM (особенно Grok) часто возвращает JSON **без префикса**, просто в конце ответа:

```
Описание действия...

{"in_combat": false, "enemies": [], "combat_ended": false}
```

Regex не находил такой JSON, и весь ответ (включая JSON) шёл в `narrative`.

### 2. Недостаточная санитизация Markdown

**Файл:** `app/agents/response_synthesizer.py`

Метод `_sanitize_markdown()` не удалял остатки JSON-структур, которые могли проникнуть в narrative.

---

## Исправления

### 1. Улучшен парсинг JSON в `NarrativeDirector`

**Файл:** `app/agents/narrative_director.py`

Теперь используется **двухступенчатая стратегия**:

```python
def _parse_narrative_response(self, response: str, current_game_state: dict) -> tuple[str, dict]:
    """Extract narrative and combat state from LLM response."""
    # Strategy 1: Try to extract COMBAT_STATE: {...} format
    match = re.search(r'COMBAT_STATE:\s*({.*?})', response, re.IGNORECASE | re.DOTALL)
    
    if match:
        try:
            combat_state = json.loads(match.group(1))
            narrative = response[:match.start()].strip()
            return narrative, combat_state
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse COMBAT_STATE JSON: {e}")
    
    # Strategy 2: Try to find ANY JSON object at the end of response
    # Look for standalone {...} in last 200 characters
    last_part = response[-200:] if len(response) > 200 else response
    json_match = re.search(r'({[^{}]*"in_combat"[^{}]*})', last_part, re.DOTALL)
    
    if json_match:
        try:
            combat_state = json.loads(json_match.group(1))
            json_start_in_full = response.rfind(json_match.group(1))
            narrative = response[:json_start_in_full].strip()
            
            if "in_combat" in combat_state:
                return narrative, combat_state
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse standalone JSON: {e}")
    
    # Fallback: no combat state changes
    logger.info("No combat state JSON found, using current game state")
    return response, current_game_state
```

**Улучшения:**
- ✅ Поддержка формата `COMBAT_STATE: {...}`
- ✅ Поддержка standalone JSON в конце ответа
- ✅ Поиск в последних 200 символах (большинство JSON попадают туда)
- ✅ Валидация наличия обязательного поля `in_combat`
- ✅ Graceful fallback если JSON не найден или некорректен
- ✅ Подробное логирование для отладки

### 2. Улучшена санитизация Markdown

**Файл:** `app/agents/response_synthesizer.py`

Добавлено удаление остатков JSON:

```python
def _sanitize_markdown(self, text: str) -> str:
    """Sanitize text to prevent Markdown parsing errors."""
    
    # ... existing sanitization ...
    
    # 6. Remove any JSON-like structures that might remain
    text = re.sub(r'\{[^{}]*"in_combat"[^{}]*\}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'COMBAT_STATE:\s*\{.*?\}', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text.strip()
```

**Улучшения:**
- ✅ Удаляет JSON-подобные структуры даже если парсер их пропустил
- ✅ Удаляет префикс `COMBAT_STATE:` если он остался
- ✅ Исправлена логика подсчёта `**` (было `bold_count % 2 != 0`, теперь `len(parts) % 2 == 0`)

### 3. Добавлено логирование для отладки

**Файл:** `app/agents/response_synthesizer.py`

```python
# Debug logging
logger.debug(f"Narrative input (raw): {narrative[:200]}...")
```

Позволяет видеть в логах, что именно приходит на вход агенту.

---

## Тестирование

Созданы unit-тесты для проверки парсинга:

**Файл:** `tests/test_narrative_director.py`

Тесты покрывают:
- ✅ Парсинг JSON с префиксом `COMBAT_STATE:`
- ✅ Парсинг standalone JSON без префикса
- ✅ Обработка текста без JSON
- ✅ Обработка некорректного JSON (fallback)
- ✅ Построение mechanics context для атак
- ✅ Построение mechanics context для skill checks

**Результаты:**
```
tests/test_narrative_director.py::test_parse_narrative_with_combat_state_prefix PASSED
tests/test_narrative_director.py::test_parse_narrative_with_standalone_json PASSED
tests/test_narrative_director.py::test_parse_narrative_no_json PASSED
tests/test_narrative_director.py::test_parse_narrative_malformed_json PASSED
tests/test_narrative_director.py::test_build_mechanics_context_attack PASSED
tests/test_narrative_director.py::test_build_mechanics_context_skill_check PASSED
```

---

## Проверка работы

### До исправлений:
```
🎲 **Проверка Восприятие** [8+0 = 8] vs DC 15 ❌ Провал

Ты затаиваешь дыхание...

{"in_combat": false, "enemies": [], "combat_ended": false}  ← ПРОБЛЕМА

❤️ **HP:** 25/25 | 📍 **Локация:** ancient_ruins
```

### После исправлений (ожидается):
```
🎲 **Проверка Восприятие** [8+0 = 8] vs DC 15 ❌ Провал

Ты затаиваешь дыхание, напрягая слух в густой тени древнего леса...

❤️ **HP:** 25/25 | 📍 **Локация:** ancient_ruins
```

**JSON не должен быть виден пользователю!**

---

## Остающиеся задачи

### 1. Проблема с отображением Markdown

В сообщении пользователь видит `**Проверка Восприятие**` вместо **Проверка Восприятие**.

**Причина:** Telegram Bot API требует правильно экранированные Markdown теги.

**Решение (Sprint 2):**
- Проверить, что Aiogram правильно передаёт `parse_mode="Markdown"`
- Возможно, перейти на `parse_mode="MarkdownV2"` с правильным экранированием
- Или использовать `parse_mode="HTML"` для более предсказуемого форматирования

**Приоритет:** Средний (функциональность работает, но UX не идеален)

### 2. Улучшение промпта для Narrative Director

LLM не всегда добавляет JSON в конце ответа. Можно улучшить промпт:

```python
COMBAT_DETECTION = """После описания добавь на НОВОЙ СТРОКЕ JSON:
{"in_combat": true/false, "enemies": ["враг1"], "combat_ended": true/false}

ВАЖНО: JSON должен быть последней строкой ответа, отдельно от текста!"""
```

**Приоритет:** Низкий (текущее решение работает с fallback)

---

## Изменённые файлы

1. `app/agents/narrative_director.py` - улучшен парсинг JSON
2. `app/agents/response_synthesizer.py` - улучшена санитизация
3. `tests/test_narrative_director.py` - добавлены тесты (новый файл)

## Команды для проверки

```bash
# Запустить тесты
uv run pytest tests/test_narrative_director.py -v
uv run pytest tests/test_response_synthesizer.py -v

# Запустить бота
uv run start
```

---

**Статус:** ✅ Исправлено и протестировано
**Дата:** 7 ноября 2025
