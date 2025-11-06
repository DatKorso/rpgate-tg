"""Narrative Director Agent for story generation."""

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
    Agent for generating narrative.
    
    Role: "Storyteller"
    Task: Create vivid, engaging descriptions of actions
    """
    
    def __init__(self):
        super().__init__(
            name="NarrativeDirector",
            model_config=AGENT_CONFIGS.NARRATIVE_DIRECTOR
        )
        self.prompts = NarrativeDirectorPrompts
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Generate narrative with combat state detection.
        
        Args:
            context: {
                "user_action": str,
                "mechanics_result": dict,
                "intent": dict,
                "narrative_hints": list[str],
                "game_state": dict,
                "success": bool,
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
        narrative_hints = context.get("narrative_hints", [])
        game_state = context.get("game_state", {})
        success = context.get("success", True)
        
        # Build mechanics context string
        mechanics_context = self._build_mechanics_context(mechanics_result, success)
        
        # Build hints text
        hints_text = ""
        if narrative_hints:
            hints_text = f"\nОсобые эффекты: {', '.join(narrative_hints)}"
        
        # Build combat context
        combat_context = ""
        if game_state.get("in_combat"):
            enemies = ", ".join(game_state.get("enemies", []))
            combat_context = f"\n\nТЕКУЩИЙ БОЙ: Игрок сражается с {enemies}"
        
        # Combat detection instruction
        # NOTE: Combat state is now generated via separate JSON mode call
        # No need to include it in narrative prompt
        
        # Format user prompt WITHOUT combat detection (handled separately)
        user_prompt = f"""Действие игрока: "{user_action}"

Результат механики: {mechanics_context}
{hints_text}
{combat_context}

Опиши это действие ярко и захватывающе (2-4 предложения)."""
        
        messages = [
            {"role": "system", "content": self.prompts.SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Step 1: Generate narrative text
            response = await llm_client.get_completion(
                messages=messages,
                model=self.model,
                temperature=self.temperature,
                max_tokens=self.model_config.max_tokens,
                frequency_penalty=self.model_config.frequency_penalty,
                presence_penalty=self.model_config.presence_penalty
            )
            
            # Step 2: Generate combat state as separate JSON call (more reliable)
            game_state_updates = await self._generate_combat_state(
                user_action, 
                game_state, 
                mechanics_result, 
                success
            )
            
            narrative = response.strip()
            
        except Exception as e:
            logger.error(f"Error generating narrative: {e}", exc_info=True)
            # Fallback simple narrative
            narrative = f"Ты {user_action}. " + ("Успех!" if success else "Неудача.")
            game_state_updates = game_state
        
        output = {
            "narrative": narrative,
            "game_state_updates": game_state_updates
        }
        
        self.log_execution(context, output)
        return output
    
    async def _generate_combat_state(
        self,
        user_action: str,
        current_game_state: dict,
        mechanics_result: dict,
        success: bool
    ) -> dict:
        """
        Generate combat state update using JSON mode for reliability.
        
        Separate call ensures valid JSON without narrative text interference.
        """
        # Detect if combat should start (heuristic)
        action_type = mechanics_result.get("action_type", "other")
        is_attack = action_type == "attack"
        
        # Build context for combat state decision
        current_enemies = current_game_state.get("enemies", [])
        in_combat = current_game_state.get("in_combat", False)
        
        combat_prompt = f"""Ты Game Master D&D игры. Определи состояние боя после действия игрока.

Действие игрока: "{user_action}"
Тип действия: {action_type}
Результат: {"Успех (попадание)" if success else "Провал (промах)"}
Текущие враги: {current_enemies if current_enemies else "нет"}
Бой активен: {"да" if in_combat else "нет"}

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:

1. НАЧАЛО БОЯ:
   - Если игрок АТАКУЕТ существо/врага → БОЙ НАЧИНАЕТСЯ (in_combat: true)
   - Ключевые слова атаки: "атак", "бью", "напал", "меч", "удар", "убить"
   - Определи имя врага из текста действия (например: "волк", "гоблин", "орк", "сущность")

2. ВРАГИ В БОЮ:
   - Если бой начался → добавь врага в список enemies
   - Враг остаётся в списке пока не побеждён
   - Если игрок нанёс КРИТИЧЕСКИЙ урон (>15 HP) → враг может быть убит

3. КОНТРАТАКИ ВРАГОВ (enemy_attacks):
   ВАЖНО: В D&D враги атакуют в свой ход, НЕ как реакция!
   
   - Если игрок УСПЕШНО атакует → враг НЕ контратакует (только 20% вероятность)
   - Если игрок ПРОМАХНУЛСЯ → враг использует момент слабости и контратакует (80% вероятность)
   - Если игрок делает НЕ атаку (перемещение, лечение) → враг атакует (90% вероятность)
   - Урон врага: 5-12 HP (зависит от типа врага)
   - Формат: [{{"attacker": "имя врага", "damage": число}}]
   - Если бой закончен → enemy_attacks = []

4. КОНЕЦ БОЯ:
   - Бой заканчивается ТОЛЬКО когда ВСЕ враги побеждены
   - Тогда: in_combat: false, enemies: [], combat_ended: true

Примеры:

Пример 1 - НАЧАЛО БОЯ, успешная атака игрока:
Действие: "Напал на волка с мечом", Результат: ПОПАДАНИЕ
{{
  "in_combat": true,
  "enemies": ["серый волк"],
  "combat_ended": false,
  "enemy_attacks": []
}}
(Враг НЕ контратакует, так как игрок успешно атаковал)

Пример 2 - БОЙ ПРОДОЛЖАЕТСЯ, промах игрока:
Действие: "Атакую гоблина", Результат: ПРОМАХ
{{
  "in_combat": true,
  "enemies": ["гоблин"],
  "combat_ended": false,
  "enemy_attacks": [{{"attacker": "гоблин", "damage": 9}}]
}}
(Враг использует момент слабости и контратакует)

Пример 3 - Игрок перемещается/лечится:
Действие: "Отступаю назад", Бой активен
{{
  "in_combat": true,
  "enemies": ["орк"],
  "combat_ended": false,
  "enemy_attacks": [{{"attacker": "орк", "damage": 11}}]
}}
(Враг атакует, так как игрок не атаковал)

Пример 4 - КОНЕЦ БОЯ (враг убит):
Действие: "Атакую", Результат: попадание, критический урон
{{
  "in_combat": false,
  "enemies": [],
  "combat_ended": true,
  "enemy_attacks": []
}}

Верни ТОЛЬКО JSON, без комментариев."""

        messages = [
            {"role": "system", "content": "Ты Game Master, управляющий боевой системой D&D. Возвращай ТОЛЬКО валидный JSON."},
            {"role": "user", "content": combat_prompt}
        ]
        
        try:
            response = await llm_client.get_completion(
                messages=messages,
                model=self.model,
                temperature=0.3,  # Lower temperature for more consistent JSON
                max_tokens=250,
                response_format={"type": "json_object"}  # JSON mode
            )
            
            combat_state = json.loads(response)
            
            # Ensure all required fields exist
            if "enemy_attacks" not in combat_state:
                combat_state["enemy_attacks"] = []
            if "in_combat" not in combat_state:
                # Fallback heuristic: if attack action, start combat
                combat_state["in_combat"] = is_attack or in_combat
            if "enemies" not in combat_state:
                combat_state["enemies"] = current_enemies
            if "combat_ended" not in combat_state:
                combat_state["combat_ended"] = False
            
            # Heuristic fix: If attack detected but no combat started, fix it
            if is_attack and not combat_state["in_combat"] and not combat_state["combat_ended"]:
                logger.warning("LLM didn't start combat on attack - applying heuristic fix")
                combat_state["in_combat"] = True
                # Try to extract enemy name from action
                if not combat_state["enemies"]:
                    enemy_name = self._extract_enemy_name(user_action)
                    if enemy_name:
                        combat_state["enemies"] = [enemy_name]
                        # Add enemy attack
                        import random
                        combat_state["enemy_attacks"] = [{
                            "attacker": enemy_name,
                            "damage": random.randint(5, 12)
                        }]
            
            logger.info(f"Generated combat state: in_combat={combat_state['in_combat']}, enemies={len(combat_state['enemies'])}, attacks={len(combat_state['enemy_attacks'])}")
            
            return combat_state
            
        except Exception as e:
            logger.error(f"Failed to generate combat state: {e}", exc_info=True)
            
            # Fallback: if attack action, assume combat started
            if is_attack and not in_combat:
                logger.warning("Combat state generation failed - using attack heuristic")
                enemy_name = self._extract_enemy_name(user_action)
                import random
                
                # Enemy counter-attacks only if player missed
                enemy_attacks = []
                if not success:  # Player missed
                    enemy_attacks = [{
                        "attacker": enemy_name or "unknown enemy",
                        "damage": random.randint(5, 12)
                    }]
                
                return {
                    "in_combat": True,
                    "enemies": [enemy_name or "unknown enemy"],
                    "combat_ended": False,
                    "enemy_attacks": enemy_attacks
                }
            
            # Otherwise keep current state
            return current_game_state
    
    def _extract_enemy_name(self, user_action: str) -> str | None:
        """Extract enemy name from user action using simple heuristics."""
        user_action_lower = user_action.lower()
        
        # Common enemy names
        enemies = [
            "волк", "гоблин", "орк", "дракон", "скелет", "зомби",
            "троль", "огр", "сущность", "монстр", "чудовище",
            "тень", "призрак", "вампир", "оборотень", "василиск"
        ]
        
        for enemy in enemies:
            if enemy in user_action_lower:
                return enemy
        
        # Try to extract "на <noun>" pattern
        import re
        match = re.search(r'на\s+([а-яё]+)', user_action_lower)
        if match:
            return match.group(1)
        
        return None
    
    def _build_mechanics_context(self, mechanics: dict, success: bool) -> str:
        """Build mechanics context string in Russian."""
        if not mechanics:
            return "Простое действие"
        
        action_type = mechanics.get("action_type", "other")
        
        if action_type == "attack":
            attack_roll = mechanics.get("attack_roll", {})
            hit = mechanics.get("hit", False)
            damage = mechanics.get("total_damage", 0)
            
            result = f"Атака: d20={attack_roll.get('roll', 0)} "
            if hit:
                result += f"→ ПОПАДАНИЕ! Урон: {damage} HP"
            else:
                result += "→ ПРОМАХ"
            
            return result
        
        elif action_type == "skill_check":
            check_roll = mechanics.get("check_roll", {})
            dc = mechanics.get("dc", 0)
            skill = mechanics.get("skill", "unknown")
            
            result = f"Проверка {skill}: d20={check_roll.get('roll', 0)} vs DC {dc} "
            result += "→ УСПЕХ" if success else "→ ПРОВАЛ"
            
            return result
        
        return "Результат: " + ("Успех" if success else "Провал")
    
    def _fix_json_syntax(self, json_str: str) -> str:
        """
        Attempt to fix common JSON syntax errors from LLM output.
        
        Common LLM mistakes:
        - Missing commas between fields
        - Trailing commas
        - Single quotes instead of double quotes
        """
        # Replace single quotes with double quotes (simple heuristic)
        fixed = json_str.replace("'", '"')
        
        # Fix missing commas: look for patterns where a value is followed by a key
        # Pattern 1: } or ] followed by " without comma
        fixed = re.sub(r'}\s*"', '}, "', fixed)
        fixed = re.sub(r']\s*"', '], "', fixed)
        
        # Pattern 2: boolean/number followed by " without comma
        fixed = re.sub(r'(?<=true)\s+"', ', "', fixed)
        fixed = re.sub(r'(?<=false)\s+"', ', "', fixed)
        fixed = re.sub(r'(\d)\s+"', r'\1, "', fixed)  # number followed by "
        
        # Pattern 3: closing quote followed by opening quote (likely missing comma)
        # e.g., "wolf" "damage" should be "wolf", "damage"
        fixed = re.sub(r'"\s+"', '", "', fixed)
        
        # Remove trailing commas before ] or }
        fixed = re.sub(r',\s*}', '}', fixed)
        fixed = re.sub(r',\s*]', ']', fixed)
        
        return fixed
    
    def _extract_json_object(self, text: str, start_pos: int) -> str | None:
        """
        Extract a complete JSON object starting from start_pos.
        Handles nested braces correctly.
        """
        if start_pos >= len(text) or text[start_pos] != '{':
            return None
        
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i in range(start_pos, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        return text[start_pos:i+1]
        
        return None
    
    def _parse_narrative_response(self, response: str, current_game_state: dict) -> tuple[str, dict]:
        """Extract narrative and combat state from LLM response."""
        # Strategy 1: Try to extract COMBAT_STATE: {...} format
        match = re.search(r'COMBAT_STATE:\s*', response, re.IGNORECASE)
        
        if match:
            # Extract complete JSON object starting after "COMBAT_STATE:"
            json_start = match.end()
            json_str = self._extract_json_object(response, json_start)
            
            if json_str:
                # Try parsing original JSON first
                try:
                    combat_state = json.loads(json_str)
                    narrative = response[:match.start()].strip()
                    
                    if "enemy_attacks" not in combat_state:
                        combat_state["enemy_attacks"] = []
                    
                    logger.info(f"Parsed COMBAT_STATE: in_combat={combat_state.get('in_combat')}, enemies={combat_state.get('enemies')}, enemy_attacks={len(combat_state.get('enemy_attacks', []))}")
                    
                    return narrative, combat_state
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse COMBAT_STATE JSON: {e}")
                    
                    # Try to fix common JSON errors
                    fixed_json = self._fix_json_syntax(json_str)
                    try:
                        combat_state = json.loads(fixed_json)
                        narrative = response[:match.start()].strip()
                        
                        if "enemy_attacks" not in combat_state:
                            combat_state["enemy_attacks"] = []
                        
                        logger.info(f"Parsed COMBAT_STATE (after fix): in_combat={combat_state.get('in_combat')}, enemy_attacks={len(combat_state.get('enemy_attacks', []))}")
                        
                        return narrative, combat_state
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Failed to parse even after JSON fix: {e2}")
                        logger.debug(f"Original JSON: {json_str[:200]}")
                        logger.debug(f"Fixed JSON: {fixed_json[:200]}")
        
        # Strategy 2: Try to find ANY JSON object at the end of response
        last_part = response[-300:] if len(response) > 300 else response
        json_match = re.search(r'({[^{}]*"in_combat"[^{}]*})', last_part, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            
            # Try original first
            try:
                combat_state = json.loads(json_str)
                json_start_in_full = response.rfind(json_str)
                narrative = response[:json_start_in_full].strip()
                
                if "enemy_attacks" not in combat_state:
                    combat_state["enemy_attacks"] = []
                
                if "in_combat" in combat_state:
                    logger.info(f"Parsed standalone JSON: in_combat={combat_state.get('in_combat')}, enemy_attacks={len(combat_state.get('enemy_attacks', []))}")
                    return narrative, combat_state
            except json.JSONDecodeError:
                # Try fixing
                fixed_json = self._fix_json_syntax(json_str)
                try:
                    combat_state = json.loads(fixed_json)
                    json_start_in_full = response.rfind(json_str)
                    narrative = response[:json_start_in_full].strip()
                    
                    if "enemy_attacks" not in combat_state:
                        combat_state["enemy_attacks"] = []
                    
                    if "in_combat" in combat_state:
                        logger.info(f"Parsed standalone JSON (after fix): enemy_attacks={len(combat_state.get('enemy_attacks', []))}")
                        return narrative, combat_state
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse standalone JSON even after fix: {e}")
        
        # Fallback: no combat state changes, return full response as narrative
        logger.warning("No valid combat state JSON found in LLM response, using current game state")
        logger.debug(f"Full response (first 500 chars): {response[:500]}")
        return response, current_game_state
