# Sprint 2 Specification: Multi-Agent Foundation

> **Для AI Code Agent:** Этот документ содержит детальные спецификации для реализации Sprint 2. Следуй указаниям точно, используй типы данных как указано, пиши тесты для каждого компонента.

---

## 📋 Sprint Overview

**Цель:** Создать базовую мульти-агентную систему с игровыми механиками (dice, character sheet, combat).

**Timeframe:** 2-3 недели

**Success Criteria:**
- ✅ Бот может вести combat encounter с механиками
- ✅ Character sheet отслеживается корректно
- ✅ 3 агента работают (Rules Arbiter, Narrative Director, Response Synthesizer)
- ✅ Ответы красиво отформатированы

---

## ⚙️ Prerequisites: Prompts & Configuration System

**ВАЖНО:** Перед началом Week 1, реализуй систему управления промптами и конфигурацией моделей.

**См. документ:** `docs/SPRINT2_PROMPTS_CONFIG.md`

**Обязательные файлы для создания:**
1. `app/config/__init__.py`
2. `app/config/models.py` — конфигурация моделей (temperature, max_tokens, etc.)
3. `app/config/prompts.py` — все промпты на русском языке

**Зачем это нужно:**
- ✅ Централизованное хранение промптов (легко редактировать)
- ✅ Разные модели/температуры для разных агентов
- ✅ Полная локализация на русский для игроков
- ✅ Код и документация на английском

**Время:** 1-2 часа

---

## Week 1: Game Mechanics Foundation

### Task 1.1: Character Model

**File:** `app/game/character.py`

**Description:** Pydantic модель для Character Sheet с базовыми D&D-подобными stats.

**Requirements:**

```python
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4


class CharacterSheet(BaseModel):
    """Character sheet model для игрока."""
    
    # Identity
    id: UUID = Field(default_factory=uuid4)
    telegram_user_id: int
    name: str
    
    # Core Stats (D&D style)
    level: int = Field(default=1, ge=1, le=20)
    
    # Attributes (modifiers from -5 to +10)
    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)
    
    # Combat Stats
    hp: int = Field(default=20, ge=0)
    max_hp: int = Field(default=20, ge=1)
    armor_class: int = Field(default=10, ge=0)
    
    # Inventory
    gold: int = Field(default=50, ge=0)
    inventory: list[str] = Field(default_factory=lambda: ["меч", "кожаная броня", "зелье лечения"])
    
    # Location
    location: str = Field(default="tavern")
    
    # Experience
    xp: int = Field(default=0, ge=0)
    
    @property
    def strength_mod(self) -> int:
        """Calculate strength modifier from attribute."""
        return (self.strength - 10) // 2
    
    @property
    def dexterity_mod(self) -> int:
        return (self.dexterity - 10) // 2
    
    @property
    def constitution_mod(self) -> int:
        return (self.constitution - 10) // 2
    
    @property
    def intelligence_mod(self) -> int:
        return (self.intelligence - 10) // 2
    
    @property
    def wisdom_mod(self) -> int:
        return (self.wisdom - 10) // 2
    
    @property
    def charisma_mod(self) -> int:
        return (self.charisma - 10) // 2
    
    def is_alive(self) -> bool:
        """Check if character is alive."""
        return self.hp > 0
    
    def take_damage(self, damage: int) -> int:
        """Apply damage to character. Returns actual damage taken."""
        damage = max(0, damage)
        old_hp = self.hp
        self.hp = max(0, self.hp - damage)
        actual_damage = old_hp - self.hp
        return actual_damage
    
    def heal(self, amount: int) -> int:
        """Heal character. Returns actual HP restored."""
        amount = max(0, amount)
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        actual_healing = self.hp - old_hp
        return actual_healing
    
    def model_dump_for_storage(self) -> dict:
        """Export для хранения в FSM context или DB."""
        return self.model_dump(mode='json')
```

**Testing:** Create `tests/test_character.py`

```python
from app.game.character import CharacterSheet


def test_character_creation():
    char = CharacterSheet(telegram_user_id=12345, name="Артур")
    assert char.name == "Артур"
    assert char.level == 1
    assert char.hp == 20


def test_strength_modifier():
    char = CharacterSheet(telegram_user_id=12345, name="Test", strength=16)
    assert char.strength_mod == 3  # (16-10)//2 = 3


def test_take_damage():
    char = CharacterSheet(telegram_user_id=12345, name="Test", hp=20)
    damage = char.take_damage(5)
    assert damage == 5
    assert char.hp == 15
    assert char.is_alive()


def test_death():
    char = CharacterSheet(telegram_user_id=12345, name="Test", hp=5)
    char.take_damage(10)
    assert char.hp == 0
    assert not char.is_alive()


def test_heal():
    char = CharacterSheet(telegram_user_id=12345, name="Test", hp=10, max_hp=20)
    healed = char.heal(7)
    assert healed == 7
    assert char.hp == 17
```

---

### Task 1.2: Dice System

**File:** `app/game/dice.py`

**Description:** Система бросков кубиков (d4, d6, d8, d10, d12, d20, d100) с модификаторами.

**Requirements:**

```python
import random
from typing import Literal

DiceType = Literal["d4", "d6", "d8", "d10", "d12", "d20", "d100"]


class DiceRoller:
    """Dice rolling system для game mechanics."""
    
    DICE_SIDES = {
        "d4": 4,
        "d6": 6,
        "d8": 8,
        "d10": 10,
        "d12": 12,
        "d20": 20,
        "d100": 100,
    }
    
    @staticmethod
    def roll(dice: DiceType, modifier: int = 0) -> dict:
        """
        Roll a dice with optional modifier.
        
        Args:
            dice: Type of dice (d4, d6, etc)
            modifier: Modifier to add to roll
            
        Returns:
            {
                "dice": "d20",
                "roll": 15,
                "modifier": 3,
                "total": 18,
                "is_critical": False,
                "is_fumble": False
            }
        """
        sides = DiceRoller.DICE_SIDES[dice]
        roll = random.randint(1, sides)
        total = roll + modifier
        
        # Critical hit/fumble только для d20
        is_critical = (dice == "d20" and roll == 20)
        is_fumble = (dice == "d20" and roll == 1)
        
        return {
            "dice": dice,
            "roll": roll,
            "modifier": modifier,
            "total": total,
            "is_critical": is_critical,
            "is_fumble": is_fumble,
        }
    
    @staticmethod
    def roll_multiple(dice: DiceType, count: int, modifier: int = 0) -> dict:
        """
        Roll multiple dice and sum them.
        
        Args:
            dice: Type of dice
            count: Number of dice to roll
            modifier: Modifier to add to total
            
        Returns:
            {
                "dice": "2d6",
                "rolls": [4, 5],
                "modifier": 2,
                "total": 11
            }
        """
        sides = DiceRoller.DICE_SIDES[dice]
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        
        return {
            "dice": f"{count}{dice}",
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
        }
    
    @staticmethod
    def roll_with_advantage() -> dict:
        """
        Roll d20 with advantage (roll twice, take higher).
        D&D 5e mechanic.
        """
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        chosen = max(roll1, roll2)
        
        return {
            "dice": "d20",
            "rolls": [roll1, roll2],
            "chosen": chosen,
            "advantage": True,
            "is_critical": (chosen == 20),
            "is_fumble": (chosen == 1),
        }
    
    @staticmethod
    def roll_with_disadvantage() -> dict:
        """Roll d20 with disadvantage (roll twice, take lower)."""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        chosen = min(roll1, roll2)
        
        return {
            "dice": "d20",
            "rolls": [roll1, roll2],
            "chosen": chosen,
            "disadvantage": True,
            "is_critical": (chosen == 20),
            "is_fumble": (chosen == 1),
        }


# Convenience functions
def d4(modifier: int = 0) -> dict:
    return DiceRoller.roll("d4", modifier)

def d6(modifier: int = 0) -> dict:
    return DiceRoller.roll("d6", modifier)

def d8(modifier: int = 0) -> dict:
    return DiceRoller.roll("d8", modifier)

def d10(modifier: int = 0) -> dict:
    return DiceRoller.roll("d10", modifier)

def d12(modifier: int = 0) -> dict:
    return DiceRoller.roll("d12", modifier)

def d20(modifier: int = 0) -> dict:
    return DiceRoller.roll("d20", modifier)

def d100(modifier: int = 0) -> dict:
    return DiceRoller.roll("d100", modifier)
```

**Testing:** Create `tests/test_dice.py`

```python
from app.game.dice import DiceRoller, d20


def test_d20_roll():
    result = DiceRoller.roll("d20", modifier=3)
    assert result["dice"] == "d20"
    assert 1 <= result["roll"] <= 20
    assert result["total"] == result["roll"] + 3


def test_critical_hit():
    # Mock random для тестирования
    import random
    random.seed(42)  # Set seed для воспроизводимости
    
    # Тестируем что critical определяется корректно
    for _ in range(100):
        result = d20()
        if result["roll"] == 20:
            assert result["is_critical"]
        else:
            assert not result["is_critical"]


def test_roll_multiple():
    result = DiceRoller.roll_multiple("d6", count=2, modifier=3)
    assert result["dice"] == "2d6"
    assert len(result["rolls"]) == 2
    assert result["total"] == sum(result["rolls"]) + 3


def test_advantage():
    result = DiceRoller.roll_with_advantage()
    assert result["advantage"]
    assert len(result["rolls"]) == 2
    assert result["chosen"] == max(result["rolls"])
```

---

### Task 1.3: Rules Engine

**File:** `app/game/rules.py`

**Description:** Rules engine для разрешения игровых действий (атаки, проверки навыков).

**Requirements:**

```python
from typing import Literal
from app.game.dice import DiceRoller
from app.game.character import CharacterSheet

ActionType = Literal["attack", "skill_check", "spell", "other"]


class RulesEngine:
    """Game rules engine для разрешения действий."""
    
    # Difficulty Classes для skill checks
    DC_EASY = 10
    DC_MEDIUM = 15
    DC_HARD = 20
    DC_VERY_HARD = 25
    
    @staticmethod
    def resolve_attack(
        attacker: CharacterSheet,
        target_ac: int,
        weapon_damage_dice: str = "d8"
    ) -> dict:
        """
        Resolve melee attack.
        
        Args:
            attacker: Attacking character
            target_ac: Target's armor class
            weapon_damage_dice: Damage dice (e.g., "d8" for longsword)
            
        Returns:
            {
                "action_type": "attack",
                "attack_roll": {...},
                "hit": True/False,
                "damage_roll": {...} or None,
                "total_damage": int,
                "is_critical": bool
            }
        """
        # Attack roll: d20 + strength modifier
        attack_roll = DiceRoller.roll("d20", modifier=attacker.strength_mod)
        
        # Check if hit
        hit = attack_roll["total"] >= target_ac or attack_roll["is_critical"]
        
        # Damage roll if hit
        damage_roll = None
        total_damage = 0
        
        if hit:
            # Critical hit = double damage dice
            if attack_roll["is_critical"]:
                damage_roll = DiceRoller.roll_multiple(
                    weapon_damage_dice, 
                    count=2, 
                    modifier=attacker.strength_mod
                )
            else:
                damage_roll = DiceRoller.roll(
                    weapon_damage_dice, 
                    modifier=attacker.strength_mod
                )
            
            total_damage = damage_roll["total"]
        
        return {
            "action_type": "attack",
            "attack_roll": attack_roll,
            "target_ac": target_ac,
            "hit": hit,
            "damage_roll": damage_roll,
            "total_damage": total_damage,
            "is_critical": attack_roll["is_critical"],
            "is_fumble": attack_roll["is_fumble"],
        }
    
    @staticmethod
    def resolve_skill_check(
        character: CharacterSheet,
        skill: str,
        dc: int,
        advantage: bool = False,
        disadvantage: bool = False
    ) -> dict:
        """
        Resolve skill check.
        
        Args:
            character: Character making check
            skill: Skill name (strength, dexterity, wisdom, etc)
            dc: Difficulty Class
            advantage: Roll with advantage
            disadvantage: Roll with disadvantage
            
        Returns:
            {
                "action_type": "skill_check",
                "skill": "strength",
                "check_roll": {...},
                "dc": 15,
                "success": True/False
            }
        """
        # Get appropriate modifier
        skill_modifiers = {
            "strength": character.strength_mod,
            "dexterity": character.dexterity_mod,
            "constitution": character.constitution_mod,
            "intelligence": character.intelligence_mod,
            "wisdom": character.wisdom_mod,
            "charisma": character.charisma_mod,
        }
        
        modifier = skill_modifiers.get(skill.lower(), 0)
        
        # Roll with advantage/disadvantage
        if advantage:
            check_roll = DiceRoller.roll_with_advantage()
            check_roll["total"] = check_roll["chosen"] + modifier
        elif disadvantage:
            check_roll = DiceRoller.roll_with_disadvantage()
            check_roll["total"] = check_roll["chosen"] + modifier
        else:
            check_roll = DiceRoller.roll("d20", modifier=modifier)
        
        success = check_roll["total"] >= dc
        
        return {
            "action_type": "skill_check",
            "skill": skill,
            "check_roll": check_roll,
            "dc": dc,
            "success": success,
            "is_critical": check_roll.get("is_critical", False),
        }
    
    @staticmethod
    def detect_action_type(user_input: str) -> ActionType:
        """
        Detect action type from user input.
        Simple keyword matching для MVP.
        
        Args:
            user_input: User's action text
            
        Returns:
            ActionType ("attack", "skill_check", "spell", "other")
        """
        user_input_lower = user_input.lower()
        
        # Attack keywords
        attack_keywords = ["атак", "удар", "бью", "напада", "меч", "топор", "лук"]
        if any(keyword in user_input_lower for keyword in attack_keywords):
            return "attack"
        
        # Skill check keywords
        skill_keywords = [
            "провер", "ищу", "открыва", "взламыва", "убежда", 
            "обманыва", "прыга", "лезу", "слуша"
        ]
        if any(keyword in user_input_lower for keyword in skill_keywords):
            return "skill_check"
        
        # Spell keywords
        spell_keywords = ["заклинан", "магия", "колд", "закля"]
        if any(keyword in user_input_lower for keyword in spell_keywords):
            return "spell"
        
        return "other"
```

**Testing:** Create `tests/test_rules.py`

```python
from app.game.rules import RulesEngine
from app.game.character import CharacterSheet


def test_resolve_attack_hit():
    attacker = CharacterSheet(
        telegram_user_id=123, 
        name="Test", 
        strength=16  # +3 modifier
    )
    
    # Mock seed для воспроизводимости
    import random
    random.seed(10)
    
    result = RulesEngine.resolve_attack(
        attacker=attacker,
        target_ac=12,
        weapon_damage_dice="d8"
    )
    
    assert result["action_type"] == "attack"
    assert "attack_roll" in result
    assert "hit" in result


def test_resolve_skill_check():
    character = CharacterSheet(
        telegram_user_id=123,
        name="Test",
        dexterity=14  # +2 modifier
    )
    
    result = RulesEngine.resolve_skill_check(
        character=character,
        skill="dexterity",
        dc=15
    )
    
    assert result["action_type"] == "skill_check"
    assert result["skill"] == "dexterity"
    assert result["dc"] == 15
    assert isinstance(result["success"], bool)


def test_detect_action_type():
    assert RulesEngine.detect_action_type("Я атакую гоблина") == "attack"
    assert RulesEngine.detect_action_type("Я ищу ловушки") == "skill_check"
    assert RulesEngine.detect_action_type("Иду вперед") == "other"
```

---

## Week 2: Agent System

### Task 2.1: Base Agent Class

**File:** `app/agents/base.py`

**Description:** Базовый класс для всех агентов.

**Requirements:**

```python
from abc import ABC, abstractmethod
from typing import Any
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class для всех AI агентов."""
    
    def __init__(self, name: str, model: str = "gpt-4o-mini", temperature: float = 0.3):
        """
        Initialize agent.
        
        Args:
            name: Agent name для logging
            model: LLM model to use
            temperature: Sampling temperature
        """
        self.name = name
        self.model = model
        self.temperature = temperature
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute agent logic.
        
        Args:
            context: Input context (varies by agent)
            
        Returns:
            Agent output (varies by agent)
        """
        pass
    
    def log_execution(self, context: dict, output: dict):
        """Log agent execution для debugging."""
        self.logger.info(
            f"Agent '{self.name}' executed",
            extra={
                "agent": self.name,
                "context_keys": list(context.keys()),
                "output_keys": list(output.keys()),
            }
        )
```

---

### Task 2.2: Rules Arbiter Agent

**File:** `app/agents/rules_arbiter.py`

**Description:** Agent для разрешения game mechanics (dice rolls, combat).

**Requirements:**

```python
from typing import Any
from app.agents.base import BaseAgent
from app.game.rules import RulesEngine
from app.game.character import CharacterSheet
import logging

logger = logging.getLogger(__name__)


class RulesArbiterAgent(BaseAgent):
    """
    Agent для разрешения игровых механик.
    
    Роль: "Rules Lawyer" / Referee
    Задача: Определить тип действия, выполнить броски, вычислить результат
    """
    
    def __init__(self):
        super().__init__(
            name="RulesArbiter",
            model="gpt-4o-mini",  # Дешевая модель для structured tasks
            temperature=0.1  # Низкая для консистентности
        )
        self.rules_engine = RulesEngine()
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute rules arbitration.
        
        Args:
            context: {
                "user_action": str,
                "character": CharacterSheet,
                "target_ac": int (optional, для combat),
                "dc": int (optional, для skill checks)
            }
            
        Returns:
            {
                "action_type": "attack" | "skill_check" | "other",
                "mechanics_result": {...},  # From RulesEngine
                "success": bool,
                "narrative_hints": list[str]  # Hints для Narrative Director
            }
        """
        user_action = context["user_action"]
        character = context["character"]
        
        # Detect action type
        action_type = self.rules_engine.detect_action_type(user_action)
        
        mechanics_result = {}
        success = True
        narrative_hints = []
        
        if action_type == "attack":
            # Resolve attack
            target_ac = context.get("target_ac", 12)  # Default goblin AC
            mechanics_result = self.rules_engine.resolve_attack(
                attacker=character,
                target_ac=target_ac,
                weapon_damage_dice="d8"  # Default weapon
            )
            success = mechanics_result["hit"]
            
            if mechanics_result["is_critical"]:
                narrative_hints.append("critical_hit")
            elif mechanics_result["is_fumble"]:
                narrative_hints.append("fumble")
            
        elif action_type == "skill_check":
            # Resolve skill check
            # TODO: LLM call для определения skill и DC (или hardcode для MVP)
            skill = "dexterity"  # Default для MVP
            dc = context.get("dc", RulesEngine.DC_MEDIUM)
            
            mechanics_result = self.rules_engine.resolve_skill_check(
                character=character,
                skill=skill,
                dc=dc
            )
            success = mechanics_result["success"]
            
        else:
            # Other actions - no mechanics
            action_type = "other"
            mechanics_result = {"message": "No mechanics required"}
        
        output = {
            "action_type": action_type,
            "mechanics_result": mechanics_result,
            "success": success,
            "narrative_hints": narrative_hints,
        }
        
        self.log_execution(context, output)
        return output
```

**Testing:** Create `tests/test_rules_arbiter.py`

```python
import pytest
from app.agents.rules_arbiter import RulesArbiterAgent
from app.game.character import CharacterSheet


@pytest.mark.asyncio
async def test_rules_arbiter_attack():
    agent = RulesArbiterAgent()
    character = CharacterSheet(telegram_user_id=123, name="Test", strength=16)
    
    context = {
        "user_action": "Я атакую гоблина мечом",
        "character": character,
        "target_ac": 12
    }
    
    result = await agent.execute(context)
    
    assert result["action_type"] == "attack"
    assert "mechanics_result" in result
    assert "success" in result


@pytest.mark.asyncio
async def test_rules_arbiter_skill_check():
    agent = RulesArbiterAgent()
    character = CharacterSheet(telegram_user_id=123, name="Test")
    
    context = {
        "user_action": "Я ищу ловушки",
        "character": character,
        "dc": 15
    }
    
    result = await agent.execute(context)
    
    assert result["action_type"] == "skill_check"
```

---

### Task 2.3: Narrative Director Agent

**File:** `app/agents/narrative_director.py`

**Description:** Agent для генерации narrative описаний.

**Requirements:**

```python
from typing import Any
from app.agents.base import BaseAgent
from app.llm.client import llm_client


class NarrativeDirectorAgent(BaseAgent):
    """
    Agent для генерации narrative.
    
    Роль: "Storyteller"
    Задача: Создавать яркие, engaging описания действий
    """
    
    def __init__(self):
        super().__init__(
            name="NarrativeDirector",
            model="x-ai/grok-2",  # Качественная модель для narrative
            temperature=0.8  # Высокая для creativity
        )
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Generate narrative description.
        
        Args:
            context: {
                "user_action": str,
                "mechanics_result": dict,  # From Rules Arbiter
                "recent_history": list[str],  # Последние 3-5 сообщений
                "narrative_hints": list[str]  # ["critical_hit", "fumble", etc]
            }
            
        Returns:
            {
                "narrative": str  # Красивое описание 2-4 предложения
            }
        """
        user_action = context["user_action"]
        mechanics_result = context.get("mechanics_result", {})
        narrative_hints = context.get("narrative_hints", [])
        recent_history = context.get("recent_history", [])
        
        # Build prompt
        system_prompt = """Ты — опытный Game Master, ведущий fantasy RPG приключение.
Твоя задача — превратить игровую механику в яркое, захватывающее описание.

Правила:
- Пиши от второго лица ("Ты...", "Твой меч...")
- Используй сенсорные детали (звуки, запахи, ощущения)
- Описание должно быть 2-4 предложения
- Поддерживай epic fantasy tone
- НЕ добавляй игровую статистику (это сделает другой агент)
"""
        
        # Build context from mechanics
        mechanics_context = ""
        if mechanics_result.get("hit"):
            mechanics_context = f"Атака ПОПАЛА. Урон: {mechanics_result.get('total_damage', 0)}."
        elif mechanics_result.get("success"):
            mechanics_context = "Проверка УСПЕШНА."
        elif "hit" in mechanics_result and not mechanics_result["hit"]:
            mechanics_context = "Атака ПРОМАХНУЛАСЬ."
        elif "success" in mechanics_result and not mechanics_result["success"]:
            mechanics_context = "Проверка ПРОВАЛЕНА."
        
        # Add hints
        hints_text = ""
        if "critical_hit" in narrative_hints:
            hints_text += "Это был КРИТИЧЕСКИЙ удар! "
        if "fumble" in narrative_hints:
            hints_text += "Полный провал! "
        
        user_prompt = f"""Действие игрока: "{user_action}"

Механика: {mechanics_context}
{hints_text}

Опиши это действие ярко и захватывающе."""
        
        # Call LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        narrative = await llm_client.get_completion(
            messages=messages,
            temperature=self.temperature,
            max_tokens=300
        )
        
        output = {"narrative": narrative}
        self.log_execution(context, output)
        return output
```

---

### Task 2.4: Response Synthesizer Agent

**File:** `app/agents/response_synthesizer.py`

**Description:** Финальный agent для сборки красивого ответа.

**Requirements:**

```python
from typing import Any
from app.agents.base import BaseAgent


class ResponseSynthesizerAgent(BaseAgent):
    """
    Agent для синтеза финального ответа.
    
    Роль: "Master Narrator"
    Задача: Собрать outputs всех агентов в один красивый ответ
    """
    
    def __init__(self):
        super().__init__(
            name="ResponseSynthesizer",
            model="gpt-4o",  # Лучшая модель для финального quality
            temperature=0.3
        )
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Synthesize final response.
        
        Args:
            context: {
                "narrative": str,  # From Narrative Director
                "mechanics_result": dict,  # From Rules Arbiter
                "character": CharacterSheet,  # Updated character
                "action_type": str
            }
            
        Returns:
            {
                "final_message": str  # Готовое сообщение для игрока
            }
        """
        narrative = context.get("narrative", "")
        mechanics = context.get("mechanics_result", {})
        character = context["character"]
        action_type = context.get("action_type", "other")
        
        # Build final message
        parts = []
        
        # Add mechanics info if relevant
        if action_type == "attack":
            attack_roll = mechanics.get("attack_roll", {})
            roll_text = f"🎲 **Атака** [🎲 {attack_roll.get('roll', 0)}+{attack_roll.get('modifier', 0)} = {attack_roll.get('total', 0)}]"
            
            if mechanics.get("is_critical"):
                roll_text += " 💥 **КРИТИЧЕСКИЙ УДАР!**"
            elif mechanics.get("is_fumble"):
                roll_text += " 💔 **Промах!**"
            elif mechanics.get("hit"):
                roll_text += " ✅ Попадание!"
            else:
                roll_text += " ❌ Промах"
            
            parts.append(roll_text)
            
            if mechanics.get("hit"):
                damage = mechanics.get("total_damage", 0)
                parts.append(f"💔 **Урон:** {damage} HP")
        
        elif action_type == "skill_check":
            check_roll = mechanics.get("check_roll", {})
            skill = mechanics.get("skill", "")
            dc = mechanics.get("dc", 0)
            
            roll_value = check_roll.get("total", 0)
            success = mechanics.get("success", False)
            
            check_text = f"🎲 **Проверка {skill}** [🎲 {roll_value} vs DC {dc}]"
            if success:
                check_text += " ✅ Успех!"
            else:
                check_text += " ❌ Провал"
            
            parts.append(check_text)
        
        # Add narrative
        if narrative:
            parts.append(f"\n{narrative}")
        
        # Add character status
        hp_text = f"\n❤️ **HP:** {character.hp}/{character.max_hp}"
        parts.append(hp_text)
        
        # Add location
        if character.location:
            parts.append(f"📍 **Локация:** {character.location}")
        
        final_message = "\n".join(parts)
        
        output = {"final_message": final_message}
        self.log_execution(context, output)
        return output
```

---

### Task 2.5: Agent Orchestrator (Simple Version)

**File:** `app/agents/orchestrator.py`

**Description:** Простой orchestrator для вызова агентов в правильной последовательности. Для MVP используем простую sequential execution без CrewAI (добавим в Sprint 3).

**Requirements:**

```python
from typing import Any
from app.agents.rules_arbiter import RulesArbiterAgent
from app.agents.narrative_director import NarrativeDirectorAgent
from app.agents.response_synthesizer import ResponseSynthesizerAgent
from app.game.character import CharacterSheet
import logging

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Simple orchestrator для мульти-агентной системы.
    
    Workflow:
    1. Rules Arbiter — разрешить механики
    2. Narrative Director — создать описание
    3. Response Synthesizer — собрать финальный ответ
    """
    
    def __init__(self):
        self.rules_arbiter = RulesArbiterAgent()
        self.narrative_director = NarrativeDirectorAgent()
        self.response_synthesizer = ResponseSynthesizerAgent()
    
    async def process_action(
        self,
        user_action: str,
        character: CharacterSheet,
        recent_history: list[str] = None,
        target_ac: int = 12,
        dc: int = 15
    ) -> tuple[str, CharacterSheet]:
        """
        Process user action через агентную систему.
        
        Args:
            user_action: Действие игрока
            character: Character sheet
            recent_history: Последние сообщения для контекста
            target_ac: AC цели для атак
            dc: Difficulty Class для skill checks
            
        Returns:
            (final_message: str, updated_character: CharacterSheet)
        """
        logger.info(f"Processing action: {user_action}")
        
        if recent_history is None:
            recent_history = []
        
        # Step 1: Rules Arbiter
        rules_context = {
            "user_action": user_action,
            "character": character,
            "target_ac": target_ac,
            "dc": dc
        }
        rules_output = await self.rules_arbiter.execute(rules_context)
        
        # Step 2: Narrative Director (в параллели в production, но для MVP sequential)
        narrative_context = {
            "user_action": user_action,
            "mechanics_result": rules_output["mechanics_result"],
            "narrative_hints": rules_output.get("narrative_hints", []),
            "recent_history": recent_history
        }
        narrative_output = await self.narrative_director.execute(narrative_context)
        
        # Step 3: Update character state на основе mechanics
        updated_character = self._apply_mechanics_to_character(
            character, 
            rules_output["mechanics_result"],
            rules_output["action_type"]
        )
        
        # Step 4: Response Synthesizer
        synthesizer_context = {
            "narrative": narrative_output["narrative"],
            "mechanics_result": rules_output["mechanics_result"],
            "character": updated_character,
            "action_type": rules_output["action_type"]
        }
        synthesizer_output = await self.response_synthesizer.execute(synthesizer_context)
        
        final_message = synthesizer_output["final_message"]
        
        logger.info("Action processed successfully")
        return final_message, updated_character
    
    def _apply_mechanics_to_character(
        self, 
        character: CharacterSheet, 
        mechanics: dict,
        action_type: str
    ) -> CharacterSheet:
        """
        Apply mechanics results к character sheet.
        
        For MVP: Пока только damage tracking.
        В будущем: XP, loot, status effects, etc.
        """
        # No modifications для MVP (combat damage применяется вручную в handler)
        # В production это будет в World State Agent (Sprint 3)
        return character
```

---

## Week 3: Integration

### Task 3.1: Update Bot Handlers

**File:** `app/bot/handlers.py` (UPDATE EXISTING)

**Changes needed:**

1. Добавить character creation flow
2. Интегрировать AgentOrchestrator вместо прямого LLM вызова
3. Хранить CharacterSheet в FSM context

**Key changes:**

```python
# В начале файла добавить imports
from app.agents.orchestrator import AgentOrchestrator
from app.game.character import CharacterSheet

# Добавить orchestrator
orchestrator = AgentOrchestrator()

# Обновить handler для диалога
@router.message(
    ConversationState.in_conversation,
    F.text
)
async def handle_conversation(message: Message, state: FSMContext):
    """Main handler с агентной системой."""
    user_message = message.text
    
    # Get character from state
    data = await state.get_data()
    character_data = data.get("character")
    
    if not character_data:
        # Create new character if doesn't exist
        character = CharacterSheet(
            telegram_user_id=message.from_user.id,
            name=message.from_user.first_name or "Adventurer"
        )
    else:
        character = CharacterSheet(**character_data)
    
    # Get history
    history = data.get("history", [])
    recent_messages = [msg["content"] for msg in history[-5:] if msg["role"] == "assistant"]
    
    # Typing indicator
    typing_task = asyncio.create_task(_send_typing_indicator(message))
    
    try:
        # Process через orchestrator
        final_message, updated_character = await orchestrator.process_action(
            user_action=user_message,
            character=character,
            recent_history=recent_messages
        )
    finally:
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass
    
    # Save updated character
    await state.update_data(character=updated_character.model_dump_for_storage())
    
    # Update history (для narrative context)
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": final_message})
    
    if len(history) > 20:
        history = history[-20:]
    
    await state.update_data(history=history)
    
    # Send response
    await message.answer(final_message, parse_mode="Markdown")
```

---

### Task 3.2: Add Character Creation Flow

**File:** `app/bot/handlers.py` (ADD NEW)

**Description:** Добавить inline keyboard для создания персонажа.

**File:** `app/bot/keyboards.py` (CREATE NEW)

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Keyboard для /start команды."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Новое приключение", callback_data="new_adventure")],
        [InlineKeyboardButton(text="📊 Мой персонаж", callback_data="view_character")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])
    return keyboard


def get_class_selection_keyboard() -> InlineKeyboardMarkup:
    """Keyboard для выбора класса персонажа."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Воин", callback_data="class_warrior")],
        [InlineKeyboardButton(text="🏹 Следопыт", callback_data="class_ranger")],
        [InlineKeyboardButton(text="🔮 Маг", callback_data="class_mage")],
        [InlineKeyboardButton(text="🗡️ Плут", callback_data="class_rogue")],
    ])
    return keyboard
```

**Update handlers.py:**

```python
from aiogram import F
from aiogram.types import CallbackQuery
from app.bot.keyboards import get_start_keyboard, get_class_selection_keyboard

# Update /start command
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handler для /start с inline keyboard."""
    await state.set_state(ConversationState.idle)
    
    await message.answer(
        "🎲 **Добро пожаловать в RPGate!**\n\n"
        "Я твой AI Game Master. Выбери действие:",
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )


# Callback для "Новое приключение"
@router.callback_query(F.data == "new_adventure")
async def callback_new_adventure(callback: CallbackQuery, state: FSMContext):
    """Start character creation."""
    await callback.message.edit_text(
        "⚔️ **Создание персонажа**\n\n"
        "Выбери класс своего героя:",
        reply_markup=get_class_selection_keyboard(),
        parse_mode="Markdown"
    )


# Callbacks для классов
@router.callback_query(F.data.startswith("class_"))
async def callback_select_class(callback: CallbackQuery, state: FSMContext):
    """Handle class selection."""
    class_name = callback.data.replace("class_", "")
    
    # Create character с базовыми stats для класса
    class_stats = {
        "warrior": {"strength": 16, "constitution": 14, "hp": 25, "max_hp": 25},
        "ranger": {"dexterity": 16, "wisdom": 14, "hp": 20, "max_hp": 20},
        "mage": {"intelligence": 16, "wisdom": 14, "hp": 15, "max_hp": 15},
        "rogue": {"dexterity": 16, "charisma": 14, "hp": 18, "max_hp": 18},
    }
    
    stats = class_stats.get(class_name, {})
    
    character = CharacterSheet(
        telegram_user_id=callback.from_user.id,
        name=callback.from_user.first_name or "Adventurer",
        **stats
    )
    
    await state.update_data(character=character.model_dump_for_storage())
    await state.set_state(ConversationState.in_conversation)
    
    class_emojis = {
        "warrior": "⚔️",
        "ranger": "🏹",
        "mage": "🔮",
        "rogue": "🗡️"
    }
    
    await callback.message.edit_text(
        f"{class_emojis.get(class_name, '⚔️')} **Персонаж создан!**\n\n"
        f"**Имя:** {character.name}\n"
        f"**Класс:** {class_name.capitalize()}\n"
        f"**HP:** {character.hp}/{character.max_hp}\n"
        f"**Сила:** {character.strength} ({character.strength_mod:+d})\n"
        f"**Ловкость:** {character.dexterity} ({character.dexterity_mod:+d})\n\n"
        f"Твоё приключение начинается...\n\n"
        f"Ты стоишь у входа в темную пещеру. "
        f"Внутри слышны странные звуки. Что делаешь?",
        parse_mode="Markdown"
    )
```

---

## Testing & Documentation

### Task 4.1: Integration Tests

**File:** `tests/test_integration.py`

```python
import pytest
from app.agents.orchestrator import AgentOrchestrator
from app.game.character import CharacterSheet


@pytest.mark.asyncio
async def test_full_combat_flow():
    """Test полного combat flow через orchestrator."""
    orchestrator = AgentOrchestrator()
    
    character = CharacterSheet(
        telegram_user_id=123,
        name="TestHero",
        strength=16,
        hp=20,
        max_hp=20
    )
    
    # Simulate attack
    message, updated_char = await orchestrator.process_action(
        user_action="Я атакую гоблина мечом",
        character=character,
        target_ac=12
    )
    
    assert message is not None
    assert len(message) > 0
    assert "атак" in message.lower() or "меч" in message.lower()
```

---

### Task 4.2: Update README

**File:** `README.md` (UPDATE)

Add Sprint 2 features:

```markdown
## Features (Sprint 2)

- ✅ Multi-agent GM system (Rules Arbiter + Narrative Director + Response Synthesizer)
- ✅ Game mechanics (d20 system, combat, skill checks)
- ✅ Character creation with classes (Warrior, Ranger, Mage, Rogue)
- ✅ Character sheet tracking (HP, stats, inventory)
- ✅ Inline keyboards для UX
- ✅ Beautiful formatted responses with emojis
```

---

## Success Criteria Checklist

По завершении Sprint 2 проверь:

- [ ] Бот запускается без ошибок
- [ ] Можно создать персонажа через inline keyboard
- [ ] Команда "Я атакую гоблина" генерирует бросок d20 + урон
- [ ] Команда "Я ищу ловушки" генерирует skill check
- [ ] Ответы красиво отформатированы с эмодзи и Markdown
- [ ] Character HP отслеживается корректно
- [ ] Все unit tests проходят (`pytest tests/`)
- [ ] Integration test проходит

---

## Appendix: Для AI Code Agent

### Coding Guidelines

1. **Type hints везде:** Используй Pydantic models и type annotations
2. **Async/await:** Все agent methods должны быть async
3. **Logging:** Используй `logger.info()` для важных событий
4. **Error handling:** Wrap LLM calls в try/except
5. **Docstrings:** Добавляй docstrings к каждой функции

### File Creation Order

Рекомендуемый порядок создания файлов:

**Week 0 (Prerequisites):**
1. `app/config/__init__.py`
2. `app/config/models.py` (см. SPRINT2_PROMPTS_CONFIG.md)
3. `app/config/prompts.py` (см. SPRINT2_PROMPTS_CONFIG.md)

**Week 1:**
4. `app/game/character.py`
5. `app/game/dice.py`
6. `tests/test_dice.py` (запусти pytest)
7. `app/game/rules.py`
8. `tests/test_rules.py`

**Week 2:**
9. `app/agents/base.py` (обновленный с ModelConfig)
10. `app/agents/rules_arbiter.py` (с LLM intent analysis)
11. `app/agents/narrative_director.py` (с combat detection)
12. `app/agents/response_synthesizer.py`
13. `app/agents/orchestrator.py` (с game_state)

**Week 3:**
14. `app/bot/keyboards.py`
15. Update `app/bot/handlers.py` (с game_state и промптами)
16. Update `app/llm/client.py` (с ModelConfig support)
17. `tests/test_integration.py`
18. Update `README.md`

### Testing Commands

```bash
# Run all tests
uv run pytest tests/

# Run specific test file
uv run pytest tests/test_dice.py -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Run bot locally
uv run python -m app.main
```

---

**Ready to start? Начинай с Task 1.1!** 🚀
