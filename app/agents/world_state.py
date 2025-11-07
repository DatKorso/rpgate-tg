"""World State Agent - World Simulator.

Агент для управления состоянием мира и его персистентности в database.
Отслеживает игровое состояние (combat, enemies, location) и сохраняет в DB.
"""

from typing import Any, List, Optional
from uuid import UUID
import logging

from app.agents.base import BaseAgent
from app.config.models import AGENT_CONFIGS
from app.db.supabase import get_db_connection

logger = logging.getLogger(__name__)


class WorldStateAgent(BaseAgent):
    """
    Agent для управления состоянием мира.
    
    Роль: "World Simulator"
    Задача: Обновить world state на основе действий игрока и сохранить в DB
    
    Workflow:
    1. Анализирует результаты действия (mechanics_result)
    2. Обновляет game state (enemies, combat status, location, etc.)
    3. Сохраняет изменения в database
    4. Возвращает обновленное состояние
    """
    
    def __init__(self):
        """Initialize World State Agent."""
        super().__init__(
            name="WorldState",
            model_config=AGENT_CONFIGS.WORLD_STATE,
        )
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Update world state based on action results.
        
        Args:
            context: {
                "character_id": UUID - Character ID
                "game_state": dict - Current game state
                "mechanics_result": dict - Results from Rules Arbiter
                "action_type": str - Type of action
                "narrative_updates": dict (optional) - Updates from Narrative Director
            }
            
        Returns:
            {
                "updated_game_state": dict - New game state
                "state_changes": List[str] - Human-readable changes
                "persisted": bool - Whether state was saved to DB
            }
        """
        try:
            character_id: UUID = context["character_id"]
            game_state = context.get("game_state", {})
            mechanics_result = context.get("mechanics_result", {})
            action_type = context.get("action_type", "other")
            narrative_updates = context.get("narrative_updates", {})
            
            self.logger.info(
                f"Updating world state for character {character_id}, "
                f"action_type={action_type}"
            )
            
            # Deep copy game state to avoid mutations
            updated_state = dict(game_state)
            state_changes: List[str] = []
            
            self.logger.debug(f"Initial state: in_combat={updated_state.get('in_combat')}, enemies={updated_state.get('enemies', [])}")
            
            # Apply narrative updates first (priority)
            if narrative_updates:
                self._apply_narrative_updates(
                    updated_state, 
                    narrative_updates, 
                    state_changes
                )
                self.logger.debug(f"After narrative updates: in_combat={updated_state.get('in_combat')}, enemies={updated_state.get('enemies', [])}")
            
            # Apply mechanics-based updates
            if action_type == "attack":
                self._handle_combat_update(
                    updated_state,
                    mechanics_result,
                    state_changes
                )
                self.logger.debug(f"After combat updates: in_combat={updated_state.get('in_combat')}, enemies={updated_state.get('enemies', [])}")
            
            # Save to database
            persisted = await self._save_world_state(character_id, updated_state)
            
            output = {
                "updated_game_state": updated_state,
                "state_changes": state_changes,
                "persisted": persisted
            }
            
            self.log_execution(context, output)
            return output
            
        except Exception as e:
            self.logger.error(f"World state update failed: {e}", exc_info=True)
            # Return unchanged state on error
            return {
                "updated_game_state": context.get("game_state", {}),
                "state_changes": ["❌ Ошибка обновления состояния мира"],
                "persisted": False
            }
    
    def _apply_narrative_updates(
        self,
        state: dict,
        narrative_updates: dict,
        changes: List[str]
    ):
        """
        Apply updates from Narrative Director to game state.
        
        Narrative Director может обновлять:
        - in_combat
        - enemies
        - combat_ended
        - enemy_attacks
        - location (future)
        """
        # Combat status
        if "in_combat" in narrative_updates:
            old_status = state.get("in_combat", False)
            new_status = narrative_updates["in_combat"]
            
            if old_status != new_status:
                state["in_combat"] = new_status
                status_text = "начался" if new_status else "завершен"
                changes.append(f"Бой {status_text}")
        
        # Enemies list
        if "enemies" in narrative_updates:
            state["enemies"] = narrative_updates["enemies"]
        
        # Combat ended flag
        if narrative_updates.get("combat_ended"):
            state["in_combat"] = False
            state["enemies"] = []
            changes.append("Бой завершен")
        
        # Enemy attacks (for damage application)
        if "enemy_attacks" in narrative_updates:
            state["enemy_attacks"] = narrative_updates["enemy_attacks"]
            
            # Track enemy damage dealt
            total_enemy_damage = sum(
                attack.get("damage", 0) 
                for attack in narrative_updates["enemy_attacks"]
            )
            
            if total_enemy_damage > 0:
                changes.append(
                    f"Враги нанесли {total_enemy_damage} урона"
                )
    
    def _handle_combat_update(
        self,
        state: dict,
        mechanics_result: dict,
        changes: List[str]
    ):
        """
        Handle combat-specific state updates.
        
        NOTE: Combat state (in_combat, enemies, combat_ended) управляется 
        ТОЛЬКО Narrative Director через game_state_updates.
        
        Этот метод оставлен для будущих механик (например, tracking enemy HP в БД).
        В текущей версии НЕ модифицирует combat state напрямую.
        """
        # Логика убийства врагов ОТКЛЮЧЕНА - это делает Narrative Director
        # В будущем здесь может быть отслеживание HP врагов в БД
        pass
    
    async def _save_world_state(
        self,
        character_id: UUID,
        state_data: dict
    ) -> bool:
        """
        Save world state to database.
        
        Args:
            character_id: Character UUID
            state_data: Game state dict to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            conn = await get_db_connection()
            
            try:
                # Convert dict to JSONB
                import json
                state_json = json.dumps(state_data)
                
                await conn.execute(
                    """
                    INSERT INTO world_state (character_id, state_data, version)
                    VALUES ($1, $2::jsonb, 1)
                    ON CONFLICT (character_id) 
                    DO UPDATE SET 
                        state_data = $2::jsonb,
                        version = world_state.version + 1,
                        updated_at = NOW()
                    """,
                    character_id,
                    state_json
                )
                
                self.logger.debug(
                    f"Saved world state for character {character_id}"
                )
                return True
                
            finally:
                await conn.close()
                
        except Exception as e:
            self.logger.error(
                f"Failed to save world state: {e}",
                exc_info=True
            )
            return False
    
    async def load_world_state(self, character_id: UUID) -> dict:
        """
        Load world state from database.
        
        Args:
            character_id: Character UUID
            
        Returns:
            Game state dict, or default state if not found
        """
        try:
            conn = await get_db_connection()
            
            try:
                row = await conn.fetchrow(
                    "SELECT state_data FROM world_state WHERE character_id = $1",
                    character_id
                )
                
                if row and row["state_data"]:
                    # asyncpg may return JSONB as string, parse it
                    state_data = row["state_data"]
                    if isinstance(state_data, str):
                        import json
                        state_data = json.loads(state_data)
                    return dict(state_data)
                else:
                    # Default state for new characters
                    return self._default_game_state()
                    
            finally:
                await conn.close()
                
        except Exception as e:
            self.logger.error(
                f"Failed to load world state: {e}",
                exc_info=True
            )
            return self._default_game_state()
    
    def _default_game_state(self) -> dict:
        """Return default game state for new characters."""
        return {
            "in_combat": False,
            "enemies": [],
            "location": "starting_area",
            "quests": [],
            "flags": {}
        }


# Global instance
world_state_agent = WorldStateAgent()
