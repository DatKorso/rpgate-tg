"""Tests for enemy damage application system."""

import pytest
from app.agents.orchestrator import AgentOrchestrator
from app.game.character import CharacterSheet


def create_test_character() -> CharacterSheet:
    """Create test character with predictable stats."""
    return CharacterSheet(
        telegram_user_id=12345,
        name="Test Hero",
        strength=16,
        dexterity=12,
        hp=25,
        max_hp=25,
        armor_class=12,
        location="test_arena"
    )


@pytest.mark.asyncio
async def test_enemy_damage_applied_to_player():
    """Test that enemy attacks reduce player HP via direct method call."""
    orchestrator = AgentOrchestrator()
    character = create_test_character()
    
    # Initial HP
    initial_hp = character.hp
    assert initial_hp == 25
    
    # Test direct damage application method
    test_enemy_attacks = [
        {"attacker": "test_wolf", "damage": 9}
    ]
    
    damaged_character = orchestrator._apply_enemy_damage(character, test_enemy_attacks)
    
    # Check HP reduced
    assert damaged_character.hp == 16  # 25 - 9 = 16
    assert damaged_character.is_alive()


@pytest.mark.asyncio
async def test_multiple_enemy_attacks():
    """Test that multiple enemies can attack in one round."""
    orchestrator = AgentOrchestrator()
    character = create_test_character()
    
    enemy_attacks = [
        {"attacker": "wolf_1", "damage": 5},
        {"attacker": "wolf_2", "damage": 7},
    ]
    
    damaged_character = orchestrator._apply_enemy_damage(character, enemy_attacks)
    
    # Total damage: 5 + 7 = 12
    assert damaged_character.hp == 13  # 25 - 12 = 13


@pytest.mark.asyncio
async def test_enemy_damage_cannot_reduce_below_zero():
    """Test that HP doesn't go below 0."""
    orchestrator = AgentOrchestrator()
    character = create_test_character()
    
    # Massive damage
    enemy_attacks = [
        {"attacker": "dragon", "damage": 100}
    ]
    
    damaged_character = orchestrator._apply_enemy_damage(character, enemy_attacks)
    
    assert damaged_character.hp == 0  # Not negative
    assert not damaged_character.is_alive()


@pytest.mark.asyncio
async def test_zero_damage_attack():
    """Test that 0 damage attack doesn't change HP."""
    orchestrator = AgentOrchestrator()
    character = create_test_character()
    
    enemy_attacks = [
        {"attacker": "weak_goblin", "damage": 0}
    ]
    
    damaged_character = orchestrator._apply_enemy_damage(character, enemy_attacks)
    
    assert damaged_character.hp == 25  # Unchanged


@pytest.mark.asyncio
async def test_empty_enemy_attacks_list():
    """Test that empty enemy_attacks list doesn't affect character."""
    orchestrator = AgentOrchestrator()
    character = create_test_character()
    
    damaged_character = orchestrator._apply_enemy_damage(character, [])
    
    assert damaged_character.hp == 25
    assert damaged_character is character  # Should return same object


@pytest.mark.asyncio
async def test_missing_damage_field():
    """Test handling of malformed enemy attack data."""
    orchestrator = AgentOrchestrator()
    character = create_test_character()
    
    # Malformed attack without damage field
    enemy_attacks = [
        {"attacker": "glitched_enemy"}  # No damage field
    ]
    
    damaged_character = orchestrator._apply_enemy_damage(character, enemy_attacks)
    
    # Should default to 0 damage
    assert damaged_character.hp == 25
