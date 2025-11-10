"""Agent Orchestrator for coordinating multi-agent workflow."""

from typing import Any, Optional
from uuid import UUID
from app.agents.rules_arbiter import RulesArbiterAgent
from app.agents.narrative_director import NarrativeDirectorAgent
from app.agents.response_synthesizer import ResponseSynthesizerAgent
from app.agents.memory_manager import MemoryManagerAgent
from app.agents.world_state import WorldStateAgent
from app.game.character import CharacterSheet
from app.memory.episodic import episodic_memory_manager
import logging

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrator for multi-agent system (Sprint 3 version with Memory & World State).
    
    Enhanced Workflow (Sprint 3):
    1. Memory Manager — retrieve relevant context from DB
    2. Rules Arbiter — analyze intent + resolve mechanics
    3. Narrative Director — create description + detect combat state
    4. World State Agent — update game state + save to DB
    5. Response Synthesizer — build final message
    6. Save Memory — store episodic memory in DB
    """
    
    def __init__(self):
        self.memory_manager = MemoryManagerAgent()
        self.rules_arbiter = RulesArbiterAgent()
        self.narrative_director = NarrativeDirectorAgent()
        self.world_state = WorldStateAgent()
        self.response_synthesizer = ResponseSynthesizerAgent()
    
    async def process_action(
        self,
        user_action: str,
        character: CharacterSheet,
        game_state: dict,
        character_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        recent_history: Optional[list[str]] = None,
        target_ac: int = 12,
        dc: int = 15,
        user_settings: Optional[dict] = None,
    ) -> tuple[str, CharacterSheet, dict]:
        """
        Process user action through enhanced agent system (Sprint 3).
        
        Args:
            user_action: Player's action text
            character: Character sheet
            game_state: Current game state with combat info
            character_id: Character UUID in DB (for memory retrieval)
            session_id: Current session UUID (for memory context)
            recent_history: Recent conversation history
            target_ac: Target armor class for combat
            dc: Difficulty class for skill checks
            
        Returns:
            (final_message, updated_character, updated_game_state)
        """
        logger.info(f"Processing action: {user_action} | Combat: {game_state.get('in_combat')}")
        
        if recent_history is None:
            recent_history = []
        
        # Step 0: Memory Manager - retrieve relevant context (if character_id provided)
        memory_summary = ""
        if character_id:
            try:
                memory_context = {
                    "user_action": user_action,
                    "character_id": character_id,
                    "session_id": session_id,
                    "top_k": 3,
                    "recent_limit": 5,
                    "min_importance": 3
                }
                memory_output = await self.memory_manager.execute(memory_context)
                memory_summary = memory_output.get("memory_summary", "")
                logger.info(
                    f"Memory retrieval: {memory_output['total_found']} memories found"
                )
            except Exception as e:
                logger.error(f"Memory Manager error: {e}", exc_info=True)
                memory_summary = "💭 Память недоступна."
        
        # Step 1: Rules Arbiter with game_state and memory
        # Step 1: Rules Arbiter with game_state and memory
        rules_context = {
            "user_action": user_action,
            "character": character,
            "game_state": game_state,
            "memory_context": memory_summary,  # Add memory context
            "target_ac": target_ac,
            "dc": dc,
            "user_settings": user_settings or {"combat_enabled": True},
        }
        rules_output = await self.rules_arbiter.execute(rules_context)
        
        # Step 2: Narrative Director with game_state and memory
        narrative_context = {
            "user_action": user_action,
            "mechanics_result": rules_output["mechanics_result"],
            "intent": rules_output.get("intent", {}),
            "narrative_hints": rules_output.get("narrative_hints", []),
            "game_state": game_state,
            "success": rules_output["success"],
            "recent_history": recent_history,
            "memory_context": memory_summary  # Add memory context
        }
        narrative_output = await self.narrative_director.execute(narrative_context)
        
        # Step 3: World State Agent - update and persist game state
        world_state_context = {
            "character_id": character_id or character.id,
            "game_state": game_state,
            "mechanics_result": rules_output["mechanics_result"],
            "action_type": rules_output["action_type"],
            "narrative_updates": narrative_output.get("game_state_updates", {})
        }
        world_state_output = await self.world_state.execute(world_state_context)
        updated_game_state = world_state_output["updated_game_state"]
        
        logger.info(
            f"World state updated: {len(world_state_output['state_changes'])} changes, "
            f"persisted={world_state_output['persisted']}"
        )
        
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
            "game_state": updated_game_state,
            "user_settings": user_settings or {"combat_enabled": True},
        }
        synthesizer_output = await self.response_synthesizer.execute(synthesizer_context)
        
        final_message = synthesizer_output["final_message"]
        
        # Step 7: Save memory (if character_id and session_id provided)
        if character_id and session_id:
            try:
                await self._save_memory(
                    character_id=character_id,
                    session_id=session_id,
                    user_action=user_action,
                    assistant_response=final_message,
                    mechanics_result=rules_output["mechanics_result"],
                    game_state=updated_game_state
                )
            except Exception as e:
                logger.error(f"Failed to save memory: {e}", exc_info=True)
        
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
    
    async def _save_memory(
        self,
        character_id: UUID,
        session_id: UUID,
        user_action: str,
        assistant_response: str,
        mechanics_result: dict,
        game_state: dict
    ):
        """
        Save episodic memory to database.
        
        Args:
            character_id: Character UUID
            session_id: Session UUID
            user_action: Player's action
            assistant_response: GM's response
            mechanics_result: Results from Rules Arbiter
            game_state: Current game state
        """
        try:
            # Extract metadata using Memory Manager
            metadata = await self.memory_manager.extract_memory_metadata(
                user_action=user_action,
                assistant_response=assistant_response,
                mechanics_result=mechanics_result
            )
            
            # Build memory content (user action + response snippet)
            memory_content = f"{user_action} → {assistant_response[:200]}"
            
            # Get location from game_state
            location = game_state.get("location", "unknown")
            
            # Save to DB
            await episodic_memory_manager.create_memory(
                character_id=character_id,
                session_id=session_id,
                content=memory_content,
                memory_type=metadata["memory_type"],
                importance_score=metadata["importance_score"],
                entities=metadata["entities"],
                location=location
            )
            
            logger.info(
                f"Saved memory for character {character_id}: "
                f"type={metadata['memory_type']}, importance={metadata['importance_score']}"
            )
            
        except Exception as e:
            logger.error(f"Failed to save memory: {e}", exc_info=True)
