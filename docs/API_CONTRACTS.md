# API Contracts - Agent Communication

> **Для AI Code Agent:** Этот документ определяет точные форматы данных для communication между агентами. Все inputs/outputs должны строго соответствовать этим схемам.

---

## Overview

В мульти-агентной системе каждый agent получает **context** (input) и возвращает **output**. Эти контракты гарантируют, что agents корректно обмениваются данными.

---

## Agent Communication Flow

```
User Input
    ↓
┌─────────────────────────────────────┐
│  AgentOrchestrator                  │
│  ┌───────────────────────────────┐  │
│  │ 1. Rules Arbiter              │  │
│  │    Input: UserActionContext   │  │
│  │    Output: RulesOutput        │  │
│  └───────────────────────────────┘  │
│           ↓                         │
│  ┌───────────────────────────────┐  │
│  │ 2. Narrative Director         │  │
│  │    Input: NarrativeContext    │  │
│  │    Output: NarrativeOutput    │  │
│  └───────────────────────────────┘  │
│           ↓                         │
│  ┌───────────────────────────────┐  │
│  │ 3. Response Synthesizer       │  │
│  │    Input: SynthesizerContext  │  │
│  │    Output: SynthesizerOutput  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
    ↓
Final Message to User
```

---

## Common Data Types

### CharacterSheet

```python
{
    "id": "uuid-string",
    "telegram_user_id": 123456789,
    "name": "Артур",
    "level": 1,
    
    # Attributes
    "strength": 16,
    "dexterity": 10,
    "constitution": 14,
    "intelligence": 10,
    "wisdom": 12,
    "charisma": 8,
    
    # Combat
    "hp": 15,
    "max_hp": 20,
    "armor_class": 12,
    
    # Inventory
    "gold": 50,
    "inventory": ["меч", "кожаная броня", "зелье лечения"],
    
    # Location
    "location": "goblin_cave",
    
    # XP
    "xp": 0
}
```

### DiceRoll

```python
# Simple roll
{
    "dice": "d20",
    "roll": 15,
    "modifier": 3,
    "total": 18,
    "is_critical": False,
    "is_fumble": False
}

# Advantage/Disadvantage
{
    "dice": "d20",
    "rolls": [12, 18],
    "chosen": 18,
    "advantage": True,
    "is_critical": False,
    "is_fumble": False
}

# Multiple dice
{
    "dice": "2d6",
    "rolls": [4, 5],
    "modifier": 2,
    "total": 11
}
```

---

## Agent #1: Rules Arbiter

### Input: UserActionContext

```python
{
    "user_action": str,          # "Я атакую гоблина мечом"
    "character": CharacterSheet, # Full character object
    "target_ac": int,            # Optional, default 12
    "dc": int,                   # Optional, default 15
}
```

**Example:**

```python
{
    "user_action": "Я атакую гоблина мечом",
    "character": {
        "telegram_user_id": 123456,
        "name": "Артур",
        "strength": 16,
        "hp": 15,
        "max_hp": 20,
        # ... full character
    },
    "target_ac": 12,
    "dc": 15
}
```

### Output: RulesOutput

```python
{
    "action_type": "attack" | "skill_check" | "spell" | "other",
    "mechanics_result": dict,    # Varies by action_type
    "success": bool,
    "narrative_hints": list[str] # ["critical_hit", "fumble", etc]
}
```

**Example for Attack:**

```python
{
    "action_type": "attack",
    "mechanics_result": {
        "action_type": "attack",
        "attack_roll": {
            "dice": "d20",
            "roll": 18,
            "modifier": 3,
            "total": 21,
            "is_critical": False,
            "is_fumble": False
        },
        "target_ac": 12,
        "hit": True,
        "damage_roll": {
            "dice": "d8",
            "roll": 7,
            "modifier": 3,
            "total": 10
        },
        "total_damage": 10,
        "is_critical": False,
        "is_fumble": False
    },
    "success": True,
    "narrative_hints": []
}
```

**Example for Critical Hit:**

```python
{
    "action_type": "attack",
    "mechanics_result": {
        "action_type": "attack",
        "attack_roll": {
            "dice": "d20",
            "roll": 20,
            "modifier": 3,
            "total": 23,
            "is_critical": True,
            "is_fumble": False
        },
        "target_ac": 12,
        "hit": True,
        "damage_roll": {
            "dice": "2d8",  # Doubled for critical
            "rolls": [6, 8],
            "modifier": 3,
            "total": 17
        },
        "total_damage": 17,
        "is_critical": True,
        "is_fumble": False
    },
    "success": True,
    "narrative_hints": ["critical_hit"]
}
```

**Example for Skill Check:**

```python
{
    "action_type": "skill_check",
    "mechanics_result": {
        "action_type": "skill_check",
        "skill": "dexterity",
        "check_roll": {
            "dice": "d20",
            "roll": 14,
            "modifier": 2,
            "total": 16,
            "is_critical": False
        },
        "dc": 15,
        "success": True,
        "is_critical": False
    },
    "success": True,
    "narrative_hints": []
}
```

**Example for Other Actions:**

```python
{
    "action_type": "other",
    "mechanics_result": {
        "message": "No mechanics required"
    },
    "success": True,
    "narrative_hints": []
}
```

---

## Agent #2: Narrative Director

### Input: NarrativeContext

```python
{
    "user_action": str,              # Original user input
    "mechanics_result": dict,        # From Rules Arbiter
    "narrative_hints": list[str],    # From Rules Arbiter
    "game_state": dict,              # {"in_combat": bool, "enemies": list, "location": str}
    "success": bool,                 # From Rules Arbiter
    "recent_history": list[str]      # Last 3-5 assistant messages
}
```

**Example:**

```python
{
    "user_action": "Я атакую гоблина мечом",
    "mechanics_result": {
        "action_type": "attack",
        "hit": True,
        "total_damage": 10,
        "is_critical": False
    },
    "narrative_hints": [],
    "game_state": {
        "in_combat": True,
        "enemies": ["гоблин", "серый волк"],
        "location": "goblin_cave"
    },
    "success": True,
    "recent_history": [
        "Ты входишь в темную пещеру.",
        "Перед тобой появляется гоблин с ржавым топором."
    ]
}
```

### Output: NarrativeOutput

```python
{
    "narrative": str,                # 2-4 предложения красивого описания
    "game_state_updates": {          # Updates to game state
        "in_combat": bool,
        "enemies": list[str],
        "combat_ended": bool,
        "enemy_attacks": [           # NEW! List of enemy attacks this round
            {
                "attacker": str,     # Enemy name
                "damage": int        # HP damage dealt
            }
        ]
    }
}
```

**Example (Player attacks, enemy counterattacks):**

```python
{
    "narrative": "Ты резко выхватываешь меч из ножен и размахиваешься в сторону гоблина. Клинок со свистом рассекает воздух и глубоко вонзается в плечо существа. Гоблин издаёт пронзительный визг, но тут же контратакует своим топором, рассекая твою руку!",
    "game_state_updates": {
        "in_combat": True,
        "enemies": ["гоблин", "серый волк"],
        "combat_ended": False,
        "enemy_attacks": [
            {
                "attacker": "гоблин",
                "damage": 5
            }
        ]
    }
}
```

**Example (Combat ends, no enemy attacks):**

```python
{
    "narrative": "Твой удар приходится точно в сердце гоблина. Он падает замертво, и тишина воцаряется в пещере.",
    "game_state_updates": {
        "in_combat": False,
        "enemies": [],
        "combat_ended": True,
        "enemy_attacks": []
    }
}
```

---

## Agent #3: Response Synthesizer

### Input: SynthesizerContext

```python
{
    "narrative": str,            # From Narrative Director
    "mechanics_result": dict,    # From Rules Arbiter
    "character": CharacterSheet, # Updated character
    "action_type": str          # "attack" | "skill_check" | etc
}
```

**Example:**

```python
{
    "narrative": "Ты резко выхватываешь меч из ножен и размахиваешься...",
    "mechanics_result": {
        "action_type": "attack",
        "attack_roll": {
            "dice": "d20",
            "roll": 18,
            "modifier": 3,
            "total": 21
        },
        "hit": True,
        "total_damage": 10,
        "is_critical": False
    },
    "character": {
        "name": "Артур",
        "hp": 15,
        "max_hp": 20,
        "location": "goblin_cave"
    },
    "action_type": "attack"
}
```

### Output: SynthesizerOutput

```python
{
    "final_message": str  # Markdown-formatted message для пользователя
}
```

**Example:**

```python
{
    "final_message": """🎲 **Атака** [🎲 18+3 = 21] ✅ Попадание!
💔 **Урон:** 10 HP

Ты резко выхватываешь меч из ножен и размахиваешься в сторону гоблина. Клинок со свистом рассекает воздух и глубоко вонзается в плечо существа. Гоблин издаёт пронзительный визг и отступает, из раны течёт тёмная кровь.

❤️ **HP:** 15/20
📍 **Локация:** goblin_cave"""
}
```

---

## Response Formatting Guide

### Emoji Legend

```python
EMOJI_MAP = {
    # Actions
    "attack": "🎲",
    "skill_check": "🎲",
    "spell": "✨",
    
    # Results
    "success": "✅",
    "failure": "❌",
    "critical": "💥",
    "fumble": "💔",
    
    # Stats
    "health": "❤️",
    "damage": "💔",
    "location": "📍",
    "inventory": "🎒",
    "gold": "💰",
    
    # Classes
    "warrior": "⚔️",
    "ranger": "🏹",
    "mage": "🔮",
    "rogue": "🗡️",
}
```

### Markdown Formatting

**Bold для важных элементов:**
- Тип действия: `**Атака**`
- Результаты: `**Попадание!**`, `**Урон:**`
- Stats: `**HP:**`, `**Локация:**`

**Inline code для чисел:**
- НЕ используем в production, только plain text для чисел

**Line breaks:**
- Одна пустая строка между sections
- Две пустые строки перед character status

---

## Orchestrator Contract

### Input: process_action()

```python
async def process_action(
    user_action: str,
    character: CharacterSheet,
    recent_history: list[str] = None,
    target_ac: int = 12,
    dc: int = 15
) -> tuple[str, CharacterSheet]:
```

**Args:**
- `user_action`: Текст действия игрока
- `character`: Character object
- `recent_history`: Последние 3-5 сообщений от assistant
- `target_ac`: Armor Class цели (для атак)
- `dc`: Difficulty Class (для skill checks)

**Returns:**
- `(final_message, updated_character)` tuple
  - `final_message`: Готовое сообщение для отправки пользователю
  - `updated_character`: Обновленный CharacterSheet

---

## Error Handling Contracts

### LLM API Errors

Если LLM API возвращает ошибку:

```python
{
    "narrative": "❌ Извини, произошла ошибка при обработке действия. Попробуй ещё раз или используй /help."
}
```

### Rate Limit Errors

```python
{
    "narrative": "⏳ Слишком много запросов. Подожди немного и попробуй снова."
}
```

### Invalid Action

Если действие не распознано и нет mechanics:

```python
{
    "action_type": "other",
    "mechanics_result": {"message": "No mechanics required"},
    "success": True,
    "narrative_hints": []
}
```

Narrative Director должен сгенерировать descriptive response без mechanics.

---

## Validation Rules

### CharacterSheet Validation

- `hp >= 0` (can be 0 for dead)
- `max_hp >= 1`
- `level >= 1 and <= 20`
- All attributes `>= 1 and <= 30`
- `armor_class >= 0`
- `gold >= 0`

### DiceRoll Validation

- `roll >= 1 and <= sides`
- `total = roll + modifier`
- `is_critical = True` only if `dice == "d20" and roll == 20`
- `is_fumble = True` only if `dice == "d20" and roll == 1`

### Narrative Validation

- Length: 2-4 предложения (approx 150-300 characters)
- Language: Russian
- Perspective: Second person ("Ты...", "Твой...")
- No meta-gaming (не упоминать mechanics в narrative)

---

## Testing Contracts

### Unit Test Format

```python
@pytest.mark.asyncio
async def test_agent_name_scenario():
    """Test specific scenario."""
    agent = AgentClass()
    
    # Arrange
    context = {
        "key": "value"
    }
    
    # Act
    output = await agent.execute(context)
    
    # Assert
    assert "expected_key" in output
    assert output["expected_key"] == expected_value
```

### Integration Test Format

```python
@pytest.mark.asyncio
async def test_orchestrator_full_flow():
    """Test complete flow через orchestrator."""
    orchestrator = AgentOrchestrator()
    character = create_test_character()
    
    message, updated_char = await orchestrator.process_action(
        user_action="test action",
        character=character
    )
    
    assert message is not None
    assert len(message) > 0
    assert isinstance(updated_char, CharacterSheet)
```

---

## Version History

- **v1.0** (Sprint 2): Initial contracts для базовых агентов (simple orchestration)
- **v1.1** (Sprint 3): Добавятся контракты для Memory Manager и World State Agent + CrewAI integration
- **v1.2** (Sprint 4): Production optimization contracts

---

## Quick Reference

### Чаще всего используемые контракты:

**Rules Arbiter Output (Attack):**
```python
{
    "action_type": "attack",
    "mechanics_result": {
        "hit": bool,
        "total_damage": int,
        "is_critical": bool
    },
    "success": bool,
    "narrative_hints": list[str]
}
```

**Narrative Director Output:**
```python
{
    "narrative": str  # 2-4 sentences
}
```

**Final Message Format:**
```markdown
🎲 **[Action Type]** [🎲 Roll] [✅/❌ Result]
💔 **Урон:** X HP (если есть)

[Narrative text - 2-4 sentences]

❤️ **HP:** current/max
📍 **Локация:** location_name
```

---

*Этот документ обновляется при добавлении новых агентов.*
