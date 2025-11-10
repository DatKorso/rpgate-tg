"""Rules Arbiter Agent for game mechanics resolution."""

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
    Agent for resolving game mechanics.
    
    Role: "Rules Lawyer" / Referee
    Task: Determine action type, execute rolls, calculate results
    """
    
    def __init__(self):
        super().__init__(
            name="RulesArbiter",
            model_config=AGENT_CONFIGS.RULES_ARBITER
        )
        self.rules_engine = RulesEngine()
        self.prompts = RulesArbiterPrompts
        self.intent_config = AGENT_CONFIGS.RULES_ARBITER_INTENT
    
    async def _analyze_intent(
        self, 
        user_action: str, 
        character: CharacterSheet, 
        game_state: dict
    ) -> dict:
        """
        Analyze user intent via LLM.
        
        Args:
            user_action: Player's action text
            character: Character sheet
            game_state: {"in_combat": bool, "enemies": list, "location": str}
            
        Returns:
            {
                "action_type": "attack" | "skill_check" | "movement" | "dialogue" | "other",
                "requires_roll": bool,
                "roll_type": "attack_roll" | "skill_check" | "saving_throw" | null,
                "skill": str | null,
                "target": str | null,
                "difficulty": "easy" | "medium" | "hard" | null,
                "reasoning": str
            }
        """
        # Build context
        context_info = []
        if game_state.get("in_combat"):
            enemies = ", ".join(game_state.get("enemies", []))
            context_info.append(f"Игрок в бою с: {enemies}")
        context_info.append(f"Локация: {game_state.get('location', 'unknown')}")
        
        context = "\n".join(context_info)
        
        # Format user prompt
        user_prompt = self.prompts.INTENT_ANALYSIS_USER.format(
            context=context,
            user_action=user_action
        )
        
        messages = [
            {"role": "system", "content": self.prompts.INTENT_ANALYSIS_SYSTEM},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            # Call LLM with intent analysis config + JSON mode
            response = await llm_client.get_completion(
                messages=messages,
                model=self.intent_config.model,
                temperature=self.intent_config.temperature,
                max_tokens=self.intent_config.max_tokens,
                response_format={"type": "json_object"}  # Enable JSON mode
            )
            
            # Parse JSON response
            intent = json.loads(response)
            return intent
        
        except json.JSONDecodeError:
            # Fallback to keyword matching if LLM failed
            self.logger.warning(f"Failed to parse LLM intent response: {response}")
            return self._fallback_keyword_detection(user_action)
        
        except Exception as e:
            self.logger.error(f"Error in intent analysis: {e}", exc_info=True)
            return self._fallback_keyword_detection(user_action)
    
    def _fallback_keyword_detection(self, user_action: str) -> dict:
        """Fallback method if LLM is unavailable."""
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
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute rules arbitration with LLM intent analysis.
        
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
        user_settings = context.get("user_settings", {"combat_enabled": True})

        # Early exit: combat disabled -> narrative-only mode
        if not user_settings.get("combat_enabled", True):
            intent = {
                "action_type": "narrative_only",
                "requires_roll": False,
                "roll_type": None,
                "skill": None,
                "target": None,
                "difficulty": None,
                "reasoning": "Combat disabled - narrative mode"
            }
            mechanics_result = {
                "message": "Combat system disabled - narrative mode active",
                "combat_disabled": True
            }
            output = {
                "action_type": "narrative_only",
                "intent": intent,
                "mechanics_result": mechanics_result,
                "success": True,
                "narrative_hints": ["narrative_only"],
            }
            self.log_execution(context, output)
            return output
        
        # Step 1: Analyze intent via LLM
        intent = await self._analyze_intent(user_action, character, game_state)
        
        self.logger.info(f"Intent analysis: {intent['action_type']}, requires_roll: {intent['requires_roll']}")
        
        # Step 2: Apply mechanics only if roll is needed
        mechanics_result = {}
        success = True
        narrative_hints = []
        
        if not intent["requires_roll"]:
            # Simple action without rolls
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
            
            # Determine DC based on difficulty
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
