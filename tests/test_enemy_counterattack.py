"""Test enemy counterattack display in final messages."""

import pytest
from unittest.mock import AsyncMock, patch
from app.agents.orchestrator import AgentOrchestrator
from app.game.character import CharacterSheet


@pytest.mark.asyncio
async def test_enemy_counterattack_shown_in_message():
    """Test that enemy counterattacks are displayed in final message."""
    
    # Setup
    orchestrator = AgentOrchestrator()
    character = CharacterSheet(
        telegram_user_id=12345,
        name="Test Hero",
        level=1,
        hp=25,
        max_hp=25,
        strength=16,
        dexterity=14,
        constitution=15,
        intelligence=10,
        wisdom=12,
        charisma=8
    )
    
    game_state = {
        "in_combat": False,
        "enemies": [],
        "location": "starting_area"
    }
    
    # Mock LLM responses to ensure enemy counterattack
    with patch("app.llm.client.llm_client.get_completion") as mock_llm:
        # Configure mock to return different responses for each call
        mock_responses = [
            # Call 1: Intent analysis (Rules Arbiter)
            """{
                "action_type": "attack",
                "requires_roll": true,
                "roll_type": "attack_roll",
                "skill": null,
                "target": "враг",
                "difficulty": null,
                "reasoning": "Атака врага"
            }""",
            
            # Call 2: Combat state (Narrative Director)
            """{
                "in_combat": true,
                "enemies": ["враг"],
                "combat_ended": false,
                "enemy_attacks": [{"attacker": "враг", "damage": 8}]
            }""",
            
            # Call 3: Narrative (Narrative Director)
            """Ты наносишь мощный удар мечом, вонзая его в плоть врага! Но враг не отступает — он отвечает яростной контратакой, его клыки впиваются в твое плечо."""
        ]
        
        # Make mock return values in sequence
        mock_llm.side_effect = mock_responses
        
        # Process action
        final_message, updated_character, updated_game_state = await orchestrator.process_action(
            user_action="Достаю из ножен меч и атакую врага",
            character=character,
            game_state=game_state,
            target_ac=12
        )
    
    # Assertions
    print("\n=== FINAL MESSAGE ===")
    print(final_message)
    print("\n=== CHARACTER HP ===")
    print(f"HP: {updated_character.hp}/{updated_character.max_hp}")
    print("\n=== GAME STATE ===")
    print(f"In combat: {updated_game_state.get('in_combat')}")
    print(f"Enemies: {updated_game_state.get('enemies')}")
    print(f"Enemy attacks: {updated_game_state.get('enemy_attacks')}")
    
    # Check that message contains counterattack information
    assert "Контратака врага" in final_message or "контратак" in final_message.lower(), \
        "Message should mention enemy counterattack"
    
    assert "8 HP" in final_message or "8HP" in final_message, \
        "Message should show enemy damage amount"
    
    assert "Враг" in final_message or "враг" in final_message, \
        "Message should name the attacking enemy"
    
    # Check that character took damage
    assert updated_character.hp < character.max_hp, \
        "Character should have taken damage from enemy"
    
    # Check combat state
    assert updated_game_state.get("in_combat") is True, \
        "Should be in combat"
    assert "враг" in updated_game_state.get("enemies", []), \
        "Enemy should be tracked in game state"


@pytest.mark.asyncio  
async def test_no_counterattack_when_not_in_combat():
    """Test that no counterattack shown when not in combat."""
    
    orchestrator = AgentOrchestrator()
    character = CharacterSheet(
        telegram_user_id=12345,
        name="Test Hero",
        level=1,
        hp=25,
        max_hp=25,
        strength=16,
        dexterity=14,
        constitution=15,
        intelligence=10,
        wisdom=12,
        charisma=8
    )
    
    game_state = {
        "in_combat": False,
        "enemies": [],
        "location": "starting_area"
    }
    
    # Mock LLM for non-combat action
    with patch("app.llm.client.llm_client.get_completion") as mock_llm:
        mock_responses = [
            # Intent: movement (no combat)
            """{
                "action_type": "movement",
                "requires_roll": false,
                "roll_type": null,
                "skill": null,
                "target": null,
                "difficulty": null,
                "reasoning": "Простое перемещение"
            }""",
            
            # Combat state: no combat
            """{
                "in_combat": false,
                "enemies": [],
                "combat_ended": false,
                "enemy_attacks": []
            }""",
            
            # Narrative
            "Ты идёшь по дороге."
        ]
        
        mock_llm.side_effect = mock_responses
        
        final_message, updated_character, updated_game_state = await orchestrator.process_action(
            user_action="Иду на север",
            character=character,
            game_state=game_state
        )
    
    # Should NOT contain counterattack
    assert "Контратака" not in final_message, \
        "Should not show counterattack when not in combat"
    
    # Character HP should be unchanged
    assert updated_character.hp == character.max_hp, \
        "Character should not take damage when not in combat"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
