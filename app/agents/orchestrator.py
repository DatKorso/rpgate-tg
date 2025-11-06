"""Agent Orchestrator for coordinating multi-agent workflow."""

from typing import Any
from app.agents.rules_arbiter import RulesArbiterAgent
from app.agents.narrative_director import NarrativeDirectorAgent
from app.agents.response_synthesizer import ResponseSynthesizerAgent
from app.game.character import CharacterSheet
import logging

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrator for multi-agent system.
    
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
        Process user action through agent system.
        
        Args:
            user_action: Player's action text
            character: Character sheet
            game_state: Current game state with combat info
            recent_history: Recent conversation history
            target_ac: Target armor class for combat
            dc: Difficulty class for skill checks
            
        Returns:
            (final_message, updated_character, updated_game_state)
        """
        logger.info(f"Processing action: {user_action} | Combat: {game_state.get('in_combat')}")
        
        if recent_history is None:
            recent_history = []
        
        # Step 1: Rules Arbiter with game_state
        rules_context = {
            "user_action": user_action,
            "character": character,
            "game_state": game_state,
            "target_ac": target_ac,
            "dc": dc
        }
        rules_output = await self.rules_arbiter.execute(rules_context)
        
        # Step 2: Narrative Director with game_state
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
        updated_game_state = {**game_state, **narrative_output.get("game_state_updates", {})}
        
        # Step 4: Apply enemy attacks to character (if any)
        enemy_attacks = updated_game_state.get("enemy_attacks", [])
        updated_character = self._apply_enemy_damage(character, enemy_attacks)
        
        # Step 5: Apply other mechanics to character (healing, buffs, etc.)
        updated_character = self._apply_mechanics_to_character(
            updated_character, 
            rules_output["mechanics_result"],
            rules_output["action_type"]
        )
        
        # Step 6: Response Synthesizer
        synthesizer_context = {
            "narrative": narrative_output["narrative"],
            "mechanics_result": rules_output["mechanics_result"],
            "character": updated_character,
            "action_type": rules_output["action_type"],
            "game_state": updated_game_state
        }
        synthesizer_output = await self.response_synthesizer.execute(synthesizer_context)
        
        final_message = synthesizer_output["final_message"]
        
        logger.info(f"Action processed | New combat state: {updated_game_state.get('in_combat')}")
        return final_message, updated_character, updated_game_state
    
    def _apply_mechanics_to_character(
        self, 
        character: CharacterSheet, 
        mechanics: dict,
        action_type: str
    ) -> CharacterSheet:
        """
        Apply mechanics results to character (damage, healing, etc).
        
        This is intentionally minimal - we don't apply player's damage to enemies here
        because enemies are narrative entities in Sprint 2, not separate CharacterSheet objects.
        
        In Sprint 3, this will be expanded when we add persistent enemy tracking.
        """
        # Note: Character damage from enemies is applied in process_action via game_state_updates
        # This method is reserved for future features like status effects, buffs, etc.
        return character
    
    def _apply_enemy_damage(
        self,
        character: CharacterSheet,
        enemy_attacks: list[dict]
    ) -> CharacterSheet:
        """
        Apply damage from enemy attacks to character.
        
        Args:
            character: Player's character sheet
            enemy_attacks: List of enemy attack dicts [{"attacker": str, "damage": int}, ...]
            
        Returns:
            Updated character with reduced HP
        """
        if not enemy_attacks:
            return character
        
        for attack in enemy_attacks:
            damage = attack.get("damage", 0)
            attacker = attack.get("attacker", "unknown enemy")
            
            if damage > 0:
                actual_damage = character.take_damage(damage)
                logger.info(f"{attacker} dealt {actual_damage} damage to player. HP: {character.hp}/{character.max_hp}")
        
        return character
