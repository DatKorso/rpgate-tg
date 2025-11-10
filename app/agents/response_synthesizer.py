"""Response Synthesizer Agent for final message formatting."""

import re
from typing import Any
from app.agents.base import BaseAgent
from app.config.models import AGENT_CONFIGS
from app.config.prompts import ResponseSynthesizerPrompts
from app.game.character import CharacterSheet
import logging

logger = logging.getLogger(__name__)


class ResponseSynthesizerAgent(BaseAgent):
    """
    Agent for synthesizing final response.
    
    Role: "Master Narrator"
    Task: Combine mechanics and narrative into beautiful formatted message
    """
    
    def __init__(self):
        super().__init__(
            name="ResponseSynthesizer",
            model_config=AGENT_CONFIGS.RESPONSE_SYNTHESIZER
        )
        self.prompts = ResponseSynthesizerPrompts
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Synthesize final response from narrative and mechanics.
        
        Args:
            context: {
                "narrative": str,
                "mechanics_result": dict,
                "character": CharacterSheet,
                "action_type": str,
                "game_state": dict
            }
            
        Returns:
            {
                "final_message": str  # Markdown formatted message
            }
        """
        narrative = context["narrative"]
        mechanics = context.get("mechanics_result", {})
        character = context["character"]
        action_type = context.get("action_type", "other")
        game_state = context.get("game_state", {})
        
        # Debug logging
        logger.debug(f"Narrative input (raw): {narrative[:200]}...")
        
        # Build message parts
        parts = []
        
        # 1. Dice rolls and mechanics (if any)
        if mechanics and mechanics.get("action_type"):
            mechanics_text = self._format_mechanics(mechanics, action_type)
            if mechanics_text:
                parts.append(mechanics_text)
        
        # 2. Narrative description
        # Sanitize narrative to fix common Markdown issues
        narrative_sanitized = self._sanitize_markdown(narrative)
        logger.debug(f"Narrative sanitized length: {len(narrative_sanitized)}, original: {len(narrative)}")
        parts.append(narrative_sanitized)
        
        # 3. Enemy attacks (if any)
        enemy_attacks_text = self._format_enemy_attacks(game_state)
        if enemy_attacks_text:
            parts.append(enemy_attacks_text)
        
        # 3. Character status
        status_text = self._format_character_status(character, game_state)
        parts.append(status_text)
        
        # Combine all parts
        final_message = "\n\n".join(parts)
        
        output = {
            "final_message": final_message
        }
        
        self.log_execution(context, output)
        return output
    
    def _sanitize_markdown(self, text: str) -> str:
        """
        Sanitize text to prevent Markdown parsing errors.
        
        Fixes common issues:
        - Unclosed bold/italic markers
        - Unpaired square brackets
        - JSON remnants
        - Special characters in wrong positions
        """
        if not text:
            return ""
        
        # 1. Remove any JSON-like structures that might remain
        text = re.sub(r'\{[^{}]*"in_combat"[^{}]*\}', '', text, flags=re.IGNORECASE)
        text = re.sub(r'COMBAT_STATE:.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r'\{[^{}]*"enemies"[^{}]*\}', '', text, flags=re.IGNORECASE)
        
        # 2. Fix unbalanced ** (bold) - must be in pairs
        # Count ** as single unit (not individual asterisks)
        parts = text.split("**")
        if len(parts) % 2 == 0:
            # Even number of parts = odd number of ** = unbalanced
            # Remove last ** by joining without it
            text = "**".join(parts[:-1]) + parts[-1]
        
        # 3. Fix unbalanced __ (underline)
        parts = text.split("__")
        if len(parts) % 2 == 0:
            text = "__".join(parts[:-1]) + parts[-1]
        
        # 4. Fix unbalanced single * (italic) - after handling **
        # Replace ** temporarily to count single asterisks
        temp_text = text.replace("**", "")
        if temp_text.count("*") % 2 != 0:
            # Escape all single asterisks (not part of **)
            text = text.replace("**", "⚡BOLD⚡")
            text = text.replace("*", r"\*")
            text = text.replace("⚡BOLD⚡", "**")
        
        # 5. Fix unbalanced single _ (underline) - after handling __
        temp_text = text.replace("__", "")
        if temp_text.count("_") % 2 != 0:
            text = text.replace("__", "⚡UNDERLINE⚡")
            text = text.replace("_", r"\_")
            text = text.replace("⚡UNDERLINE⚡", "__")
        
        # 6. Fix unbalanced [ ] (links/references)
        open_count = text.count("[")
        close_count = text.count("]")
        if open_count != close_count:
            # Escape all brackets to be safe
            text = text.replace("[", r"\[").replace("]", r"\]")
        
        # 7. Fix unbalanced backticks `
        if text.count("`") % 2 != 0:
            # Remove last backtick or escape all
            last_idx = text.rfind("`")
            if last_idx != -1:
                text = text[:last_idx] + text[last_idx+1:]
        
        # 8. Escape special Telegram Markdown characters at line start
        # Telegram MarkdownV2 has issues with certain characters
        lines = text.split("\n")
        sanitized_lines = []
        for line in lines:
            line = line.strip()
            # Don't escape if line starts with emoji (common pattern)
            if line and not line[0].isalpha() and line[0] not in "🎲💥💀❤️🩹📍⚔️✅❌💔":
                # Check for problematic characters
                if line[0] in "-+.!#":
                    line = "\\" + line
            sanitized_lines.append(line)
        
        text = "\n".join(sanitized_lines)
        
        return text.strip()
    
    def _format_mechanics(self, mechanics: dict, action_type: str) -> str:
        """Format mechanics results with emojis and markdown."""
        action_type = mechanics.get("action_type", action_type)
        
        if action_type == "attack":
            return self._format_attack(mechanics)
        elif action_type == "skill_check":
            return self._format_skill_check(mechanics)
        
        return ""
    
    def _format_attack(self, mechanics: dict) -> str:
        """Format attack roll results."""
        attack_roll = mechanics.get("attack_roll", {})
        hit = mechanics.get("hit", False)
        damage = mechanics.get("total_damage", 0)
        is_critical = mechanics.get("is_critical", False)
        is_fumble = mechanics.get("is_fumble", False)
        
        roll_value = attack_roll.get("roll", 0)
        modifier = attack_roll.get("modifier", 0)
        total = attack_roll.get("total", 0)
        target_ac = mechanics.get("target_ac", 0)
        
        # Build roll text
        if is_critical:
            emoji = "💥"
            result_emoji = "✅"
            result_text = "КРИТИЧЕСКОЕ ПОПАДАНИЕ!"
        elif is_fumble:
            emoji = "💀"
            result_emoji = "❌"
            result_text = "Критический провал!"
        elif hit:
            emoji = "🎲"
            result_emoji = "✅"
            result_text = "Попадание!"
        else:
            emoji = "🎲"
            result_emoji = "❌"
            result_text = "Промах"
        
        lines = []
        lines.append(f"{emoji} **Атака** [🎲 {roll_value}{modifier:+d} = {total}] vs AC {target_ac} {result_emoji} {result_text}")
        
        if hit and damage > 0:
            damage_roll = mechanics.get("damage_roll", {})
            if "rolls" in damage_roll:
                # Multiple dice (critical)
                dice_text = "+".join(str(r) for r in damage_roll["rolls"])
                lines.append(f"💔 **Урон:** [{dice_text}{damage_roll.get('modifier', 0):+d}] = **{damage} HP**")
            else:
                lines.append(f"💔 **Урон:** **{damage} HP**")
        
        return "\n".join(lines)
    
    def _format_skill_check(self, mechanics: dict) -> str:
        """Format skill check results."""
        check_roll = mechanics.get("check_roll", {})
        skill = mechanics.get("skill", "unknown")
        dc = mechanics.get("dc", 0)
        success = mechanics.get("success", False)
        
        # Get roll value
        if "chosen" in check_roll:
            # Advantage/disadvantage
            roll_value = check_roll["chosen"]
            rolls = check_roll.get("rolls", [])
            roll_text = f"[{rolls[0]}, {rolls[1]}]"
            if check_roll.get("advantage"):
                roll_text += " (преимущество)"
            elif check_roll.get("disadvantage"):
                roll_text += " (помеха)"
        else:
            roll_value = check_roll.get("roll", 0)
            roll_text = str(roll_value)
        
        modifier = check_roll.get("modifier", 0)
        total = check_roll.get("total", 0)
        
        emoji = "🎲"
        result_emoji = "✅" if success else "❌"
        result_text = "Успех!" if success else "Провал"
        
        skill_name_ru = {
            "strength": "Сила",
            "dexterity": "Ловкость",
            "constitution": "Телосложение",
            "intelligence": "Интеллект",
            "wisdom": "Мудрость",
            "charisma": "Харизма",
            "perception": "Восприятие",
            "stealth": "Скрытность",
            "persuasion": "Убеждение"
        }.get(skill, skill)
        
        return f"{emoji} **Проверка {skill_name_ru}** [{roll_text}{modifier:+d} = {total}] vs DC {dc} {result_emoji} {result_text}"
    
    def _format_enemy_attacks(self, game_state: dict) -> str:
        """
        Format enemy counter-attacks.
        
        Args:
            game_state: Must contain "enemy_attacks" list
            
        Returns:
            Formatted text or empty string
        """
        enemy_attacks = game_state.get("enemy_attacks", [])
        
        if not enemy_attacks:
            return ""
        
        lines = []
        lines.append("⚔️ **Контратака врага:**")
        
        for attack in enemy_attacks:
            attacker = attack.get("attacker", "Враг")
            damage = attack.get("damage", 0)
            
            # Capitalize first letter of enemy name
            attacker_capitalized = attacker.capitalize()
            
            lines.append(f"💔 **{attacker_capitalized}** наносит **{damage} HP** урона!")
        
        return "\n".join(lines)
    
    def _format_character_status(self, character: CharacterSheet, game_state: dict) -> str:
        """Format character status line."""
        hp_emoji = "❤️" if character.hp > character.max_hp // 2 else "🩹"
        location_emoji = "📍"
        
        status_parts = [
            f"{hp_emoji} **HP:** {character.hp}/{character.max_hp}",
            f"{location_emoji} **Локация:** {game_state.get('location', character.location)}"
        ]
        
        return " | ".join(status_parts)
