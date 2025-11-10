# Sprint 2 Addition: Prompts & Model Configuration System

> **Для AI Code Agent:** Эта спецификация добавляет централизованную систему управления промптами и конфигурацией моделей.

---

## 🎯 Цели

1. **Централизованное хранение промптов** — все промпты в одном месте, легко редактировать без изменения кода
2. **Конфигурация моделей** — temperature, max_tokens, format для каждого агента отдельно
3. **Локализация** — промпты и UI на русском, код и документация на английском
4. **Версионирование промптов** — возможность A/B тестирования и rollback

---

## 📁 Структура файлов

```
app/
├── config/
│   ├── __init__.py
│   ├── prompts.py          # Все промпты для агентов
│   └── models.py           # Конфигурация моделей
├── agents/
│   ├── base.py             # BaseAgent использует config
│   └── ...
```

---

## Task 0.1: Model Configuration System

**File:** `app/config/models.py`

**Description:** Централизованная конфигурация моделей для всех агентов.

```python
from typing import Literal
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for LLM model."""
    
    model: str = Field(..., description="Model identifier (e.g., 'gpt-4o', 'x-ai/grok-2')")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=500, ge=1, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    response_format: Literal["text", "json"] = Field(default="text", description="Response format")


class AgentModelConfigs:
    """Model configurations for all agents."""
    
    # Rules Arbiter: Fast, cheap, deterministic
    RULES_ARBITER = ModelConfig(
        model="gpt-4o-mini",
        temperature=0.1,  # Низкая для consistency
        max_tokens=500,
        response_format="text"
    )
    
    # Rules Arbiter Intent Analysis: Structured output
    RULES_ARBITER_INTENT = ModelConfig(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=250,
        response_format="json"  # Для structured JSON output
    )
    
    # Narrative Director: Creative, high quality
    NARRATIVE_DIRECTOR = ModelConfig(
        model="x-ai/grok-2",  # Качественная модель для narrative
        temperature=0.8,  # Высокая для creativity
        max_tokens=400,
        frequency_penalty=0.3,  # Избегать повторений
        presence_penalty=0.2,
        response_format="text"
    )
    
    # Response Synthesizer: Balanced quality
    RESPONSE_SYNTHESIZER = ModelConfig(
        model="gpt-4o",
        temperature=0.3,
        max_tokens=600,
        response_format="text"
    )
    
    # Memory Manager (Sprint 3): Fast retrieval
    MEMORY_MANAGER = ModelConfig(
        model="gpt-4o-mini",
        temperature=0.2,
        max_tokens=300,
        response_format="text"
    )
    
    # World State Agent (Sprint 3): Structured tracking
    WORLD_STATE = ModelConfig(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=400,
        response_format="json"
    )


# Export для удобства
AGENT_CONFIGS = AgentModelConfigs()
```

---

## Task 0.2: Prompts System

**File:** `app/config/prompts.py`

**Description:** Централизованное хранение всех промптов на русском языке.

```python
from typing import Dict, Any


class BasePromptTemplate:
    """Base class for prompt templates with variable substitution."""
    
    def __init__(self, template: str):
        self.template = template
    
    def format(self, **kwargs) -> str:
        """Format template with provided variables."""
        return self.template.format(**kwargs)


class RulesArbiterPrompts:
    """Prompts for Rules Arbiter Agent (Russian)."""
    
    # Intent Analysis System Prompt
    INTENT_ANALYSIS_SYSTEM = """Ты — Rules Analyzer для D&D-подобной RPG игры.
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
- Определяй сложность на основе контекста и опыта персонажа

Ответь ТОЛЬКО в JSON формате, без дополнительного текста."""
    
    # Intent Analysis User Prompt Template
    INTENT_ANALYSIS_USER = BasePromptTemplate("""Контекст:
{context}

Действие игрока: "{user_action}"

Проанализируй и верни JSON:
{{
    "action_type": "attack|skill_check|movement|dialogue|spell|other",
    "requires_roll": true/false,
    "roll_type": "attack_roll|skill_check|saving_throw|null",
    "skill": "strength|dexterity|perception|stealth|persuasion|etc или null",
    "target": "название цели или null",
    "difficulty": "easy|medium|hard|very_hard|null",
    "reasoning": "краткое объяснение на русском"
}}""")


class NarrativeDirectorPrompts:
    """Prompts for Narrative Director Agent (Russian)."""
    
    # Main System Prompt
    SYSTEM = """Ты — опытный Game Master, ведущий фэнтезийное RPG приключение в духе D&D и Pathfinder.
Твоя задача — превратить игровую механику в яркое, захватывающее описание действий персонажа.

Стиль повествования:
- Пиши от второго лица ("Ты...", "Твой меч...", "Перед тобой...")
- Используй сенсорные детали (звуки, запахи, ощущения, визуальные образы)
- Описание должно быть 2-4 предложения
- Поддерживай epic fantasy tone (героический, атмосферный)
- Добавляй драматизм в важные моменты (критические удары, провалы)

Правила:
- НЕ добавляй игровую статистику (HP, урон, броски) — это сделает другой агент
- НЕ говори за игрока (не добавляй его мысли или диалоги без запроса)
- Описывай РЕЗУЛЬТАТ действия, не только попытку
- При критических успехах/провалах усиливай эмоциональность

Атмосфера: Тёмное фэнтези с элементами героики. Мир опасен, но полон возможностей."""
    
    # User Prompt Template
    USER = BasePromptTemplate("""Действие игрока: "{user_action}"

Результат механики: {mechanics_context}
{hints_text}
{combat_context}

Опиши это действие ярко и захватывающе (2-4 предложения).

{combat_detection_instruction}""")
    
    # Combat Detection Instruction
    COMBAT_DETECTION = """После описания добавь JSON для отслеживания боевого состояния:
COMBAT_STATE: {{"in_combat": true/false, "enemies": ["враг1", "враг2"], "combat_ended": true/false}}

Правила:
- in_combat: true если игрок в активном бою
- enemies: список врагов (пустой если бой закончен)
- combat_ended: true если бой только что завершился (все враги побеждены)"""


class ResponseSynthesizerPrompts:
    """Prompts for Response Synthesizer Agent (Russian)."""
    
    # System prompt (если нужен LLM call для особо сложных случаев)
    SYSTEM = """Ты — Master Narrator, собирающий финальный ответ для игрока в RPG.
Твоя задача — объединить narrative описание с игровой механикой в один красивый, читаемый ответ.

Формат вывода:
1. Броски кубиков (если были) с эмодзи и понятными обозначениями
2. Результаты механики (урон, успех/провал)
3. Narrative описание действия
4. Статус персонажа (HP, локация)

Правила:
- Используй эмодзи для визуального разделения (🎲 ⚔️ ❤️ 📍)
- Markdown для форматирования (**жирный** для важного)
- Все тексты на русском языке
- Краткость и ясность — игрок должен сразу понять что произошло"""


class UIPrompts:
    """UI text prompts (Russian)."""
    
    # Start command
    WELCOME = """🎲 **Добро пожаловать в RPGate!**

Я твой AI Game Master, готовый провести тебя через захватывающее фэнтезийное приключение.

Выбери действие:"""
    
    # Character creation
    CHARACTER_CREATION = """⚔️ **Создание персонажа**

Выбери класс своего героя. Каждый класс имеет уникальные сильные стороны:

• **Воин** — мастер ближнего боя, высокая сила и выносливость
• **Следопыт** — ловкий стрелок, эксперт выживания
• **Маг** — владеет разрушительной магией, хрупок но опасен
• **Плут** — скрытный и хитрый, мастер засад"""
    
    # Character sheet template
    CHARACTER_SHEET = BasePromptTemplate("""{emoji} **Персонаж создан!**

**Имя:** {name}
**Класс:** {class_name}
**HP:** {hp}/{max_hp}
**Сила:** {strength} ({strength_mod:+d})
**Ловкость:** {dexterity} ({dexterity_mod:+d})
**Телосложение:** {constitution} ({constitution_mod:+d})
**Интеллект:** {intelligence} ({intelligence_mod:+d})
**Мудрость:** {wisdom} ({wisdom_mod:+d})
**Харизма:** {charisma} ({charisma_mod:+d})

Твоё приключение начинается...

{intro_scene}""")
    
    # Intro scenes by class
    INTRO_SCENES = {
        "warrior": "Ты стоишь у входа в древний форт, рука на рукояти меча. Внутри слышны подозрительные звуки. Что делаешь?",
        "ranger": "Ты следуешь по следам в лесу. Они ведут к пещере, из которой доносится странный запах. Что делаешь?",
        "mage": "Ты изучаешь древний манускрипт в библиотеке, когда замечаешь тайную дверь за книжным стеллажом. Что делаешь?",
        "rogue": "Ты крадёшься по тёмному переулку. Впереди видишь охраняемый вход в подземелье. Что делаешь?"
    }
    
    # Help text
    HELP = """ℹ️ **Как играть**

**Описывай свои действия естественным языком:**
• "Я атакую гоблина мечом"
• "Ищу ловушки в комнате"
• "Пытаюсь убедить стражника пропустить меня"
• "Иду на север"

**Механики:**
• Броски кубиков происходят автоматически
• d20 для атак и проверок навыков
• Критический успех на 20, критический провал на 1

**Команды:**
• /start — главное меню
• /character — посмотреть персонажа
• /help — эта справка

Просто опиши что ты хочешь сделать, остальное сделает GM!"""
    
    # Error messages
    ERROR_GENERIC = "❌ Произошла ошибка. Попробуй ещё раз или используй /start для перезапуска."
    ERROR_NO_CHARACTER = "❌ У тебя ещё нет персонажа. Используй /start чтобы создать его."
    ERROR_LLM_TIMEOUT = "⏱️ Ответ занимает слишком много времени. Попробуй переформулировать действие."


class CombatPrompts:
    """Combat-specific prompts (Russian)."""
    
    # Combat start notification
    COMBAT_START = "⚔️ **БОЙ НАЧАЛСЯ!**"
    
    # Combat end notification
    COMBAT_END = "✅ **Бой окончен!**"
    
    # Death message
    PLAYER_DEATH = """💀 **Ты пал в бою...**

Твоё приключение закончилось. Но смерть — не конец для истинного героя!

Используй /start чтобы начать новое приключение."""


# Export для удобства
PROMPTS = {
    "rules_arbiter": RulesArbiterPrompts,
    "narrative_director": NarrativeDirectorPrompts,
    "response_synthesizer": ResponseSynthesizerPrompts,
    "ui": UIPrompts,
    "combat": CombatPrompts,
}
```

---

## Task 0.3: Update Base Agent

**File:** `app/agents/base.py` (UPDATE)

**Changes:** Интегрировать ModelConfig.

```python
from abc import ABC, abstractmethod
from typing import Any, Optional
import logging
from app.config.models import ModelConfig

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class для всех AI агентов."""
    
    def __init__(
        self, 
        name: str, 
        config: Optional[ModelConfig] = None,
        # Backward compatibility с старым API
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Initialize agent.
        
        Args:
            name: Agent name для logging
            config: ModelConfig object (preferred)
            model: Model identifier (deprecated, use config)
            temperature: Temperature (deprecated, use config)
        """
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        
        # Use config if provided, otherwise create from legacy params
        if config is not None:
            self.config = config
        else:
            # Legacy fallback
            self.config = ModelConfig(
                model=model or "gpt-4o-mini",
                temperature=temperature or 0.3
            )
        
        self.logger.info(
            f"Agent '{name}' initialized",
            extra={
                "model": self.config.model,
                "temperature": self.config.temperature
            }
        )
    
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

## Task 0.4: Update LLM Client

**File:** `app/llm/client.py` (UPDATE)

**Changes:** Добавить support для ModelConfig.

```python
from typing import Optional
from app.config.models import ModelConfig
import httpx
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Client для работы с OpenRouter API."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def get_completion(
        self,
        messages: list[dict[str, str]],
        config: Optional[ModelConfig] = None,
        # Legacy parameters для backward compatibility
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get completion from LLM.
        
        Args:
            messages: List of messages [{"role": "user", "content": "..."}]
            config: ModelConfig object (preferred)
            model: Model name (legacy, use config instead)
            temperature: Temperature (legacy, use config instead)
            max_tokens: Max tokens (legacy, use config instead)
            
        Returns:
            Generated text
        """
        # Use config if provided, otherwise legacy params
        if config is not None:
            model_name = config.model
            temp = config.temperature
            max_tok = config.max_tokens
            response_format = config.response_format
        else:
            model_name = model or "gpt-4o-mini"
            temp = temperature or 0.7
            max_tok = max_tokens or 500
            response_format = "text"
        
        try:
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temp,
                "max_tokens": max_tok,
            }
            
            # Add response_format if JSON
            if response_format == "json":
                payload["response_format"] = {"type": "json_object"}
            
            logger.debug(f"LLM request: model={model_name}, temp={temp}, max_tokens={max_tok}")
            
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
            
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            
            logger.debug(f"LLM response: {len(content)} chars")
            return content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


# Global instance
llm_client: Optional[LLMClient] = None


def init_llm_client(api_key: str, base_url: str):
    """Initialize global LLM client."""
    global llm_client
    llm_client = LLMClient(api_key, base_url)


async def cleanup_llm_client():
    """Cleanup global LLM client."""
    global llm_client
    if llm_client:
        await llm_client.close()
```

---

## Task 0.5: Update Rules Arbiter with Prompts & Config

**File:** `app/agents/rules_arbiter.py` (UPDATE)

**Changes:** Использовать централизованные промпты и конфиг.

```python
from typing import Any
from app.agents.base import BaseAgent
from app.game.rules import RulesEngine
from app.game.character import CharacterSheet
from app.config.models import AGENT_CONFIGS
from app.config.prompts import RulesArbiterPrompts
from app.llm.client import llm_client
import logging
import json

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
            config=AGENT_CONFIGS.RULES_ARBITER
        )
        self.rules_engine = RulesEngine()
        self.intent_config = AGENT_CONFIGS.RULES_ARBITER_INTENT
        self.prompts = RulesArbiterPrompts
    
    async def _analyze_intent(
        self, 
        user_action: str, 
        character: CharacterSheet, 
        game_state: dict
    ) -> dict:
        """
        Analyze user intent через LLM.
        
        Args:
            user_action: Текст действия игрока
            character: Character sheet
            game_state: {"in_combat": bool, "enemies": list, "location": str}
            
        Returns:
            {
                "action_type": "attack" | "skill_check" | "movement" | "dialogue" | "spell" | "other",
                "requires_roll": bool,
                "roll_type": "attack_roll" | "skill_check" | "saving_throw" | null,
                "skill": str | null,
                "target": str | null,
                "difficulty": "easy" | "medium" | "hard" | "very_hard" | null,
                "reasoning": str
            }
        """
        # Build context
        context_info = []
        if game_state.get("in_combat"):
            enemies = ", ".join(game_state.get("enemies", []))
            context_info.append(f"Игрок в бою с: {enemies}")
        context_info.append(f"Локация: {game_state.get('location', 'неизвестно')}")
        context_info.append(f"Уровень персонажа: {character.level}")
        
        context_str = "\n".join(context_info)
        
        # Format user prompt
        user_prompt = self.prompts.INTENT_ANALYSIS_USER.format(
            context=context_str,
            user_action=user_action
        )
        
        messages = [
            {"role": "system", "content": self.prompts.INTENT_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Call LLM with JSON response format
            response = await llm_client.get_completion(
                messages=messages,
                config=self.intent_config
            )
            
            # Parse JSON
            intent = json.loads(response)
            
            self.logger.info(f"Intent analyzed: {intent['action_type']}, requires_roll: {intent['requires_roll']}")
            return intent
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse LLM intent response: {response[:100]}... Error: {e}")
            return self._fallback_keyword_detection(user_action)
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            return self._fallback_keyword_detection(user_action)
    
    def _fallback_keyword_detection(self, user_action: str) -> dict:
        """Fallback метод если LLM недоступен (keyword matching)."""
        action_type = self.rules_engine.detect_action_type(user_action)
        
        self.logger.info(f"Using fallback keyword detection: {action_type}")
        
        return {
            "action_type": action_type,
            "requires_roll": action_type in ["attack", "skill_check"],
            "roll_type": "attack_roll" if action_type == "attack" else "skill_check",
            "skill": "dexterity" if action_type == "skill_check" else None,
            "target": None,
            "difficulty": "medium",
            "reasoning": "Fallback keyword detection (LLM недоступен)"
        }
    
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
            
        Returns:
            {
                "action_type": str,
                "intent": dict,
                "mechanics_result": dict,
                "success": bool,
                "narrative_hints": list[str]
            }
        """
        user_action = context["user_action"]
        character = context["character"]
        game_state = context.get("game_state", {})
        
        # Step 1: Analyze intent через LLM
        intent = await self._analyze_intent(user_action, character, game_state)
        
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
            "intent": intent,
            "mechanics_result": mechanics_result,
            "success": success,
            "narrative_hints": narrative_hints,
        }
        
        self.log_execution(context, output)
        return output
```

---

## Task 0.6: Update Narrative Director with Prompts & Config

**File:** `app/agents/narrative_director.py` (UPDATE)

```python
from typing import Any
from app.agents.base import BaseAgent
from app.config.models import AGENT_CONFIGS
from app.config.prompts import NarrativeDirectorPrompts
from app.llm.client import llm_client
import logging
import json
import re

logger = logging.getLogger(__name__)


class NarrativeDirectorAgent(BaseAgent):
    """
    Agent для генерации narrative.
    
    Роль: "Storyteller"
    Задача: Создавать яркие, engaging описания действий
    """
    
    def __init__(self):
        super().__init__(
            name="NarrativeDirector",
            config=AGENT_CONFIGS.NARRATIVE_DIRECTOR
        )
        self.prompts = NarrativeDirectorPrompts
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Generate narrative description + detect combat state changes.
        
        Args:
            context: {
                "user_action": str,
                "mechanics_result": dict,
                "intent": dict,
                "success": bool,
                "narrative_hints": list[str],
                "game_state": dict,
                "recent_history": list[str]
            }
            
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
        success = context.get("success", True)
        narrative_hints = context.get("narrative_hints", [])
        
        # Build mechanics context на русском
        mechanics_context = self._build_mechanics_context(mechanics_result, success)
        
        # Build hints text
        hints_text = ""
        if "critical_hit" in narrative_hints:
            hints_text += "Это был КРИТИЧЕСКИЙ удар! "
        if "fumble" in narrative_hints:
            hints_text += "Полный провал! "
        
        # Build combat context
        combat_context = ""
        if game_state.get("in_combat"):
            enemies = ", ".join(game_state.get("enemies", []))
            combat_context = f"\n\nТЕКУЩИЙ БОЙ: Игрок сражается с {enemies}"
        
        # Decide if we need combat detection
        combat_detection_instruction = ""
        if intent.get("action_type") in ["attack", "spell", "movement"]:
            combat_detection_instruction = self.prompts.COMBAT_DETECTION
        
        # Format user prompt
        user_prompt = self.prompts.USER.format(
            user_action=user_action,
            mechanics_context=mechanics_context,
            hints_text=hints_text,
            combat_context=combat_context,
            combat_detection_instruction=combat_detection_instruction
        )
        
        messages = [
            {"role": "system", "content": self.prompts.SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        # Call LLM
        response = await llm_client.get_completion(
            messages=messages,
            config=self.config
        )
        
        # Parse narrative and combat state
        narrative, game_state_updates = self._parse_narrative_response(response, game_state)
        
        output = {
            "narrative": narrative,
            "game_state_updates": game_state_updates
        }
        
        self.log_execution(context, output)
        return output
    
    def _build_mechanics_context(self, mechanics: dict, success: bool) -> str:
        """Build mechanics context string на русском."""
        if mechanics.get("hit"):
            return f"Атака ПОПАЛА. Урон: {mechanics.get('total_damage', 0)}."
        elif mechanics.get("success"):
            return "Проверка УСПЕШНА."
        elif "hit" in mechanics and not mechanics["hit"]:
            return "Атака ПРОМАХНУЛАСЬ."
        elif "success" in mechanics and not mechanics["success"]:
            return "Проверка ПРОВАЛЕНА."
        else:
            return "Простое действие (без бросков)."
    
    def _parse_narrative_response(self, response: str, current_game_state: dict) -> tuple[str, dict]:
        """Extract narrative and combat state from LLM response."""
        # Try to extract COMBAT_STATE JSON
        match = re.search(r'COMBAT_STATE:\s*({.*?})', response, re.IGNORECASE | re.DOTALL)
        
        if match:
            try:
                combat_state = json.loads(match.group(1))
                # Remove JSON from narrative
                narrative = response[:match.start()].strip()
                
                logger.info(f"Combat state detected: in_combat={combat_state.get('in_combat')}")
                return narrative, combat_state
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse COMBAT_STATE JSON: {e}")
        
        # Fallback: no combat state changes
        return response, current_game_state
```

---

## Task 0.7: Update Orchestrator with game_state

**File:** `app/agents/orchestrator.py` (UPDATE)

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
    Orchestrator для мульти-агентной системы.
    
    Workflow:
    1. Rules Arbiter — analyze intent + resolve mechanics
    2. Narrative Director — create description + detect combat state
    3. Response Synthesizer — build final message
    """
    
    def __init__(self):
        self.rules_arbiter = RulesArbiterAgent()
        self.narrative_director = NarrativeDirectorAgent()
        self.response_synthesizer = ResponseSynthesizerAgent()
    
    async def process_action(
        self,
        user_action: str,
        character: CharacterSheet,
        game_state: dict,
        recent_history: list[str] = None,
        target_ac: int = 12,
        dc: int = 15
    ) -> tuple[str, CharacterSheet, dict]:
        """
        Process user action через агентную систему.
        
        Args:
            user_action: Действие игрока
            character: Character sheet
            game_state: {"in_combat": bool, "enemies": list, "location": str}
            recent_history: Последние сообщения для контекста
            target_ac: AC цели для атак
            dc: Difficulty Class для skill checks (fallback)
            
        Returns:
            (final_message, updated_character, updated_game_state)
        """
        logger.info(
            f"Processing action: '{user_action[:50]}...' | "
            f"Combat: {game_state.get('in_combat')} | "
            f"Location: {game_state.get('location')}"
        )
        
        if recent_history is None:
            recent_history = []
        
        # Step 1: Rules Arbiter (intent + mechanics)
        rules_context = {
            "user_action": user_action,
            "character": character,
            "game_state": game_state,
            "target_ac": target_ac,
            "dc": dc
        }
        rules_output = await self.rules_arbiter.execute(rules_context)
        
        # Step 2: Narrative Director (description + combat detection)
        narrative_context = {
            "user_action": user_action,
            "mechanics_result": rules_output["mechanics_result"],
            "intent": rules_output.get("intent", {}),
            "narrative_hints": rules_output.get("narrative_hints", []),
            "game_state": game_state,
            "success": rules_output["success"],
            "recent_history": recent_history
        }
        narrative_output = await self.narrative_director.execute(narrative_context)
        
        # Step 3: Update game state
        updated_game_state = {
            **game_state, 
            **narrative_output.get("game_state_updates", {})
        }
        
        # Step 4: Update character (apply damage, etc.)
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
            "game_state": updated_game_state
        }
        synthesizer_output = await self.response_synthesizer.execute(synthesizer_context)
        
        final_message = synthesizer_output["final_message"]
        
        logger.info(
            f"Action processed | "
            f"New combat state: {updated_game_state.get('in_combat')} | "
            f"Character HP: {updated_character.hp}/{updated_character.max_hp}"
        )
        
        return final_message, updated_character, updated_game_state
    
    def _apply_mechanics_to_character(
        self, 
        character: CharacterSheet, 
        mechanics: dict,
        action_type: str
    ) -> CharacterSheet:
        """
        Apply mechanics results к character sheet.
        
        For MVP: No modifications (damage tracking будет в handlers)
        В production: World State Agent (Sprint 3)
        """
        return character
```

---

## Task 0.8: Update Bot Handlers with game_state

**File:** `app/bot/handlers.py` (UPDATE imports and handler)

**Add these imports:**

```python
from app.config.prompts import UIPrompts, CombatPrompts
```

**Update handle_conversation:**

```python
@router.message(ConversationState.in_conversation, F.text)
async def handle_conversation(message: Message, state: FSMContext):
    """Main handler с агентной системой и game state tracking."""
    user_message = message.text
    
    # Get data from state
    data = await state.get_data()
    character_data = data.get("character")
    
    if not character_data:
        await message.answer(UIPrompts.ERROR_NO_CHARACTER)
        return
    
    character = CharacterSheet(**character_data)
    
    # Get game state (initialize если не существует)
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
            game_state=game_state,
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
    
    # Save updated data
    await state.update_data(
        character=updated_character.model_dump_for_storage(),
        game_state=updated_game_state
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

## Task 0.9: Update Character Creation with Prompts

**File:** `app/bot/handlers.py` (UPDATE character creation callbacks)

```python
from app.config.prompts import UIPrompts

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handler для /start с inline keyboard."""
    await state.set_state(ConversationState.idle)
    
    await message.answer(
        UIPrompts.WELCOME,
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "new_adventure")
async def callback_new_adventure(callback: CallbackQuery, state: FSMContext):
    """Start character creation."""
    await callback.message.edit_text(
        UIPrompts.CHARACTER_CREATION,
        reply_markup=get_class_selection_keyboard(),
        parse_mode="Markdown"
    )


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
        name=callback.from_user.first_name or "Искатель Приключений",
        **stats
    )
    
    # Initialize game_state
    game_state = {
        "in_combat": False,
        "enemies": [],
        "location": character.location
    }
    
    await state.update_data(
        character=character.model_dump_for_storage(),
        game_state=game_state
    )
    await state.set_state(ConversationState.in_conversation)
    
    class_emojis = {
        "warrior": "⚔️",
        "ranger": "🏹",
        "mage": "🔮",
        "rogue": "🗡️"
    }
    
    class_names_ru = {
        "warrior": "Воин",
        "ranger": "Следопыт",
        "mage": "Маг",
        "rogue": "Плут"
    }
    
    intro_scene = UIPrompts.INTRO_SCENES.get(class_name, "Твоё приключение начинается...")
    
    message_text = UIPrompts.CHARACTER_SHEET.format(
        emoji=class_emojis.get(class_name, "⚔️"),
        name=character.name,
        class_name=class_names_ru.get(class_name, class_name),
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
    
    await callback.message.edit_text(message_text, parse_mode="Markdown")
```

---

## Success Criteria

После реализации этой системы:

- ✅ Все промпты хранятся в `app/config/prompts.py` (легко редактировать)
- ✅ Все конфигурации моделей в `app/config/models.py` (централизованное управление)
- ✅ Все UI тексты на русском языке
- ✅ Все narrative на русском языке
- ✅ Код и документация на английском
- ✅ Легко A/B тестировать промпты (просто заменить в файле)
- ✅ Game state tracking работает корректно
- ✅ Combat detection автоматический

---

## Benefits

**Для разработки:**
- 📝 Промпты легко редактировать без изменения кода
- 🔧 Конфигурация моделей в одном месте
- 🧪 Простое A/B тестирование промптов
- 📊 Centralized logging и monitoring

**Для игроков:**
- 🇷🇺 Полная локализация на русский
- 🎭 Качественное narrative (благодаря продуманным промптам)
- ⚡ Оптимальная производительность (правильные температуры)
- 💰 Оптимизация стоимости (разные модели для разных задач)

---

**Ready to implement? Начинай с Task 0.1!** 🚀
