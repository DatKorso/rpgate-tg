# Sprint 2 Improvements: Intent Detection & Combat State

> **Для AI Code Agent:** Эти улучшения решают проблему определения действий игрока и combat state management.

---

## 🎯 Проблема

**Текущий подход (Sprint 2 базовый):**
- Keyword matching для определения типа действия
- Нет понимания контекста (в бою / вне боя)
- Не ясно когда бросать кубики

**Нужно:**
- ✅ LLM-based intent detection
- ✅ Combat state tracking
- ✅ Умное определение когда применять механики

---

## 🔧 Решение 1: LLM Intent Analyzer

### Добавить в Rules Arbiter Agent

**File:** `app/agents/rules_arbiter.py` (УЛУЧШЕННАЯ ВЕРСИЯ)

**Новый метод для анализа намерения:**

```python
from app.llm.client import llm_client

class RulesArbiterAgent(BaseAgent):
    """Enhanced Rules Arbiter с LLM-based intent detection."""
    
    async def _analyze_intent(self, user_action: str, character: CharacterSheet, game_state: dict) -> dict:
        """
        Analyze user intent через LLM.
        
        Args:
            user_action: Текст действия игрока
            character: Character sheet
            game_state: {"in_combat": bool, "enemies": list, "location": str}
            
        Returns:
            {
                "action_type": "attack" | "skill_check" | "movement" | "dialogue" | "other",
                "requires_roll": bool,
                "roll_type": "attack_roll" | "skill_check" | "saving_throw" | null,
                "skill": str | null,  # Для skill checks: "dexterity", "perception", etc
                "target": str | null,  # "goblin", "door", "trap", etc
                "difficulty": "easy" | "medium" | "hard" | null,
                "reasoning": str  # Почему LLM принял это решение
            }
        """
        
        # Build context
        context_info = []
        if game_state.get("in_combat"):
            enemies = ", ".join(game_state.get("enemies", []))
            context_info.append(f"Игрок в бою с: {enemies}")
        context_info.append(f"Локация: {game_state.get('location', 'unknown')}")
        
        system_prompt = """Ты — Rules Analyzer для D&D-подобной RPG игры.
Твоя задача — проанализировать действие игрока и определить:
1. Тип действия (атака, проверка навыка, перемещение, диалог, другое)
2. Нужен ли бросок кубика?
3. Если нужен — какой тип броска и какой навык?
4. Сложность действия (если применимо)

Правила:
- Атака ВСЕГДА требует броска атаки (d20)
- Проверки навыков требуют броска если действие имеет риск провала
- Простые действия ("иду вперед", "говорю с NPC") НЕ требуют броска
- В бою большинство действий требуют бросков

Ответь ТОЛЬКО в JSON формате, без дополнительного текста."""

        user_prompt = f"""Контекст:
{chr(10).join(context_info)}

Действие игрока: "{user_action}"

Проанализируй и верни JSON:
{{
    "action_type": "attack|skill_check|movement|dialogue|other",
    "requires_roll": true/false,
    "roll_type": "attack_roll|skill_check|saving_throw|null",
    "skill": "strength|dexterity|perception|stealth|etc или null",
    "target": "название цели или null",
    "difficulty": "easy|medium|hard|null",
    "reasoning": "краткое объяснение"
}}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call LLM with low temperature for consistency
        response = await llm_client.get_completion(
            messages=messages,
            temperature=0.1,  # Low temperature для детерминированности
            max_tokens=250
        )
        
        # Parse JSON response
        import json
        try:
            intent = json.loads(response)
            return intent
        except json.JSONDecodeError:
            # Fallback к keyword matching если LLM failed
            self.logger.warning(f"Failed to parse LLM intent response: {response}")
            return self._fallback_keyword_detection(user_action)
    
    def _fallback_keyword_detection(self, user_action: str) -> dict:
        """Fallback метод если LLM недоступен."""
        action_type = self.rules_engine.detect_action_type(user_action)
        
        return {
            "action_type": action_type,
            "requires_roll": action_type in ["attack", "skill_check"],
            "roll_type": "attack_roll" if action_type == "attack" else "skill_check",
            "skill": "dexterity" if action_type == "skill_check" else None,
            "target": None,
            "difficulty": "medium",
            "reasoning": "Fallback keyword detection"
        }
```

**Обновленный execute() метод:**

```python
async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
    """
    Execute rules arbitration с LLM intent analysis.
    
    Args:
        context: {
            "user_action": str,
            "character": CharacterSheet,
            "game_state": {
                "in_combat": bool,
                "enemies": list[str],
                "location": str
            },
            "target_ac": int (optional),
            "dc": int (optional)
        }
    """
    user_action = context["user_action"]
    character = context["character"]
    game_state = context.get("game_state", {})
    
    # Step 1: Analyze intent через LLM
    intent = await self._analyze_intent(user_action, character, game_state)
    
    self.logger.info(f"Intent analysis: {intent['action_type']}, requires_roll: {intent['requires_roll']}")
    
    # Step 2: Apply mechanics только если нужен бросок
    mechanics_result = {}
    success = True
    narrative_hints = []
    
    if not intent["requires_roll"]:
        # Простое действие без бросков
        mechanics_result = {
            "message": "No roll required",
            "intent": intent
        }
        
    elif intent["action_type"] == "attack" or intent["roll_type"] == "attack_roll":
        # Combat roll
        target_ac = context.get("target_ac", 12)
        mechanics_result = self.rules_engine.resolve_attack(
            attacker=character,
            target_ac=target_ac,
            weapon_damage_dice="d8"
        )
        success = mechanics_result["hit"]
        
        if mechanics_result["is_critical"]:
            narrative_hints.append("critical_hit")
        elif mechanics_result["is_fumble"]:
            narrative_hints.append("fumble")
    
    elif intent["roll_type"] == "skill_check":
        # Skill check
        skill = intent.get("skill", "dexterity")
        
        # Determine DC на основе difficulty
        difficulty_to_dc = {
            "easy": RulesEngine.DC_EASY,
            "medium": RulesEngine.DC_MEDIUM,
            "hard": RulesEngine.DC_HARD,
            "very_hard": RulesEngine.DC_VERY_HARD
        }
        dc = difficulty_to_dc.get(intent.get("difficulty", "medium"), RulesEngine.DC_MEDIUM)
        
        mechanics_result = self.rules_engine.resolve_skill_check(
            character=character,
            skill=skill,
            dc=dc
        )
        success = mechanics_result["success"]
    
    output = {
        "action_type": intent["action_type"],
        "intent": intent,  # Добавляем full intent для других агентов
        "mechanics_result": mechanics_result,
        "success": success,
        "narrative_hints": narrative_hints,
    }
    
    self.log_execution(context, output)
    return output
```

---

## 🔧 Решение 2: Combat State Management

### Добавить Game State в FSM Context

**File:** `app/bot/handlers.py` (ОБНОВИТЬ)

**Добавить tracking combat state:**

```python
@router.message(ConversationState.in_conversation, F.text)
async def handle_conversation(message: Message, state: FSMContext):
    """Main handler с combat state tracking."""
    user_message = message.text
    
    # Get data from state
    data = await state.get_data()
    character_data = data.get("character")
    
    if not character_data:
        character = CharacterSheet(
            telegram_user_id=message.from_user.id,
            name=message.from_user.first_name or "Adventurer"
        )
    else:
        character = CharacterSheet(**character_data)
    
    # Get game state
    game_state = data.get("game_state", {
        "in_combat": False,
        "enemies": [],
        "location": character.location
    })
    
    # Get history
    history = data.get("history", [])
    recent_messages = [msg["content"] for msg in history[-5:] if msg["role"] == "assistant"]
    
    # Typing indicator
    typing_task = asyncio.create_task(_send_typing_indicator(message))
    
    try:
        # Process через orchestrator с game_state
        final_message, updated_character, updated_game_state = await orchestrator.process_action(
            user_action=user_message,
            character=character,
            game_state=game_state,  # Передаем game state
            recent_history=recent_messages
        )
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    # Save updated data
    await state.update_data(
        character=updated_character.model_dump_for_storage(),
        game_state=updated_game_state  # Сохраняем обновленный game state
    )
    
    # Update history
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": final_message})
    
    if len(history) > 20:
        history = history[-20:]
    
    await state.update_data(history=history)
    
    # Send response
    await message.answer(final_message, parse_mode="Markdown")
```

---

## 🔧 Решение 3: Combat Detection в Narrative Director

**File:** `app/agents/narrative_director.py` (ОБНОВИТЬ)

**Добавить логику для автоматического определения начала/конца боя:**

```python
async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
    """
    Generate narrative + detect combat state changes.
    
    Returns:
        {
            "narrative": str,
            "game_state_updates": {
                "in_combat": bool,
                "enemies": list[str],
                "combat_ended": bool
            }
        }
    """
    user_action = context["user_action"]
    mechanics_result = context.get("mechanics_result", {})
    intent = context.get("intent", {})
    game_state = context.get("game_state", {})
    
    # Build narrative prompt
    system_prompt = """Ты — опытный Game Master, ведущий fantasy RPG приключение.
Твоя задача — превратить игровую механику в яркое, захватывающее описание.

ВАЖНО: В конце описания укажи в JSON:
- Начался ли бой? (если игрок встретил врага)
- Список врагов (если есть)
- Бой закончился? (если все враги повержены)

Правила:
- Пиши от второго лица ("Ты...", "Твой меч...")
- Используй сенсорные детали (звуки, запахи, ощущения)
- Описание должно быть 2-4 предложения
- Поддерживай epic fantasy tone
- НЕ добавляй игровую статистику"""

    # Add combat context
    combat_context = ""
    if game_state.get("in_combat"):
        enemies = ", ".join(game_state.get("enemies", []))
        combat_context = f"\n\nТЕКУЩИЙ БОЙ: Игрок сражается с {enemies}"
    
    user_prompt = f"""Действие игрока: "{user_action}"

Тип действия: {intent.get('action_type')}
Результат: {"Успех" if context.get('success') else "Провал"}
{combat_context}

Опиши это действие ярко и захватывающе.

После описания добавь JSON в формате:
COMBAT_STATE: {{"in_combat": true/false, "enemies": ["враг1", "враг2"], "combat_ended": false}}"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response = await llm_client.get_completion(
        messages=messages,
        temperature=self.temperature,
        max_tokens=350
    )
    
    # Parse narrative and combat state
    narrative, game_state_updates = self._parse_narrative_response(response, game_state)
    
    output = {
        "narrative": narrative,
        "game_state_updates": game_state_updates
    }
    
    self.log_execution(context, output)
    return output

def _parse_narrative_response(self, response: str, current_game_state: dict) -> tuple[str, dict]:
    """Extract narrative and combat state from LLM response."""
    import json
    import re
    
    # Try to extract COMBAT_STATE JSON
    match = re.search(r'COMBAT_STATE:\s*({.*})', response, re.IGNORECASE | re.DOTALL)
    
    if match:
        try:
            combat_state = json.loads(match.group(1))
            # Remove JSON from narrative
            narrative = response[:match.start()].strip()
            
            return narrative, combat_state
        except json.JSONDecodeError:
            pass
    
    # Fallback: no combat state changes
    return response, current_game_state
```

---

## 🔧 Решение 4: Update Orchestrator

**File:** `app/agents/orchestrator.py` (ОБНОВИТЬ)

**Добавить game_state management:**

```python
async def process_action(
    self,
    user_action: str,
    character: CharacterSheet,
    game_state: dict,  # NEW
    recent_history: list[str] = None,
    target_ac: int = 12,
    dc: int = 15
) -> tuple[str, CharacterSheet, dict]:  # Возвращаем также updated game_state
    """
    Process user action через агентную систему.
    
    Returns:
        (final_message, updated_character, updated_game_state)
    """
    logger.info(f"Processing action: {user_action} | Combat: {game_state.get('in_combat')}")
    
    if recent_history is None:
        recent_history = []
    
    # Step 1: Rules Arbiter с game_state
    rules_context = {
        "user_action": user_action,
        "character": character,
        "game_state": game_state,  # Передаем game state
        "target_ac": target_ac,
        "dc": dc
    }
    rules_output = await self.rules_arbiter.execute(rules_context)
    
    # Step 2: Narrative Director с game_state
    narrative_context = {
        "user_action": user_action,
        "mechanics_result": rules_output["mechanics_result"],
        "intent": rules_output.get("intent", {}),
        "narrative_hints": rules_output.get("narrative_hints", []),
        "game_state": game_state,  # Передаем для контекста
        "success": rules_output["success"],
        "recent_history": recent_history
    }
    narrative_output = await self.narrative_director.execute(narrative_context)
    
    # Step 3: Update game state
    updated_game_state = {**game_state, **narrative_output.get("game_state_updates", {})}
    
    # Step 4: Update character
    updated_character = self._apply_mechanics_to_character(
        character, 
        rules_output["mechanics_result"],
        rules_output["action_type"]
    )
    
    # Step 5: Response Synthesizer
    synthesizer_context = {
        "narrative": narrative_output["narrative"],
        "mechanics_result": rules_output["mechanics_result"],
        "character": updated_character,
        "action_type": rules_output["action_type"],
        "game_state": updated_game_state  # Для отображения combat status
    }
    synthesizer_output = await self.response_synthesizer.execute(synthesizer_context)
    
    final_message = synthesizer_output["final_message"]
    
    logger.info(f"Action processed | New combat state: {updated_game_state.get('in_combat')}")
    return final_message, updated_character, updated_game_state
```

---

## 📊 Примеры работы улучшенной системы

### Пример 1: Начало боя

**User:** "Я вхожу в пещеру"

**Intent Analysis:**
```json
{
    "action_type": "movement",
    "requires_roll": false,
    "roll_type": null,
    "reasoning": "Простое перемещение без риска"
}
```

**Narrative Director:**
```
Ты входишь в темную пещеру. Факел освещает каменные стены, покрытые мхом. 
Внезапно из тени выпрыгивает гоблин с ржавым топором!

COMBAT_STATE: {"in_combat": true, "enemies": ["гоблин"], "combat_ended": false}
```

**Game State обновлен:** `in_combat: true, enemies: ["гоблин"]`

---

### Пример 2: Атака в бою

**User:** "Атакую гоблина"

**Game State:** `{in_combat: true, enemies: ["гоблин"]}`

**Intent Analysis:**
```json
{
    "action_type": "attack",
    "requires_roll": true,
    "roll_type": "attack_roll",
    "target": "гоблин",
    "reasoning": "Игрок в бою, явная атака"
}
```

**Rules Arbiter:**
- Бросок d20+3 = 18 vs AC 12 → HIT
- Урон: d8+3 = 7 HP

**Narrative:**
```
Ты размахиваешься мечом! Клинок пронзает грудь гоблина. 
Он падает замертво.

COMBAT_STATE: {"in_combat": false, "enemies": [], "combat_ended": true}
```

---

### Пример 3: Действие без боя

**User:** "Я осматриваю комнату в поисках сокровищ"

**Game State:** `{in_combat: false}`

**Intent Analysis:**
```json
{
    "action_type": "skill_check",
    "requires_roll": true,
    "roll_type": "skill_check",
    "skill": "perception",
    "difficulty": "medium",
    "reasoning": "Поиск требует проверки Восприятия"
}
```

**Rules Arbiter:**
- Skill check: d20+1 = 14 vs DC 15 → FAIL

**Narrative:**
```
Ты внимательно осматриваешь комнату, но не находишь ничего интересного.
Похоже, здесь уже кто-то побывал до тебя.

COMBAT_STATE: {"in_combat": false, "enemies": [], "combat_ended": false}
```

---

## ✅ Checklist для реализации

### Обязательные изменения (для правильной работы):

- [ ] **Task 2.2+**: Добавить `_analyze_intent()` метод в Rules Arbiter
- [ ] **Task 2.2+**: Обновить `execute()` для использования intent
- [ ] **Task 2.3+**: Добавить combat state detection в Narrative Director
- [ ] **Task 2.5+**: Обновить Orchestrator для game_state management
- [ ] **Task 3.1+**: Обновить bot handlers для хранения game_state

### Опциональные улучшения:

- [ ] Добавить команду `/combat_status` для просмотра боевой ситуации
- [ ] Добавить автоматическое завершение боя при 0 HP
- [ ] Добавить difficulty adjustment на основе уровня персонажа

---

## 🎯 Итоговый Flow

```
User: "Я атакую гоблина"
    ↓
Rules Arbiter:
    1. LLM Intent: "attack" + requires_roll=true
    2. Check game_state: in_combat=true
    3. Roll d20+STR vs AC
    4. Roll damage if hit
    ↓
Narrative Director:
    1. Generate combat description
    2. Detect: combat_ended=true (goblin dead)
    ↓
Response Synthesizer:
    1. Format: dice rolls + narrative + HP
    ↓
Orchestrator:
    1. Update game_state: in_combat=false
    2. Return (message, character, game_state)
    ↓
Bot Handler:
    1. Save updated game_state в FSM
    2. Send message to user
```

---

## 💰 Cost Impact

**Дополнительные LLM вызовы:**
- Intent Analysis: ~150 tokens → $0.0002 за запрос
- Combat State Detection: уже в Narrative Director (без доп. cost)

**Total added cost:** ~$0.0002 за ход
**New cost per turn:** ~$0.0102 (было $0.01)

**Benefit:** Гораздо более точное определение действий и контекста.

---

**Готов к улучшениям? Начинай с Task 2.2+!** 🚀
