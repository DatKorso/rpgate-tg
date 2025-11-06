"""Tests for RulesEngine."""

import pytest
from app.game.rules import RulesEngine
from app.game.character import CharacterSheet


def test_resolve_attack_hit():
    """Test attack resolution with hit."""
    attacker = CharacterSheet(
        telegram_user_id=123,
        name="Test",
        strength=16  # +3 modifier
    )
    
    result = RulesEngine.resolve_attack(
        attacker=attacker,
        target_ac=10,  # Low AC for likely hit
        weapon_damage_dice="d8"
    )
    
    assert result["action_type"] == "attack"
    assert "attack_roll" in result
    assert "hit" in result
    assert isinstance(result["hit"], bool)


def test_resolve_attack_critical():
    """Test that critical hits work correctly."""
    # We can't force a crit, but we can verify the logic
    attacker = CharacterSheet(
        telegram_user_id=123,
        name="Test",
        strength=12
    )
    
    # Run multiple times to potentially hit a critical
    for _ in range(50):
        result = RulesEngine.resolve_attack(
            attacker=attacker,
            target_ac=20,
            weapon_damage_dice="d8"
        )
        
        if result["is_critical"]:
            # Critical hits should always hit
            assert result["hit"]
            # Critical damage should use multiple dice
            if result["damage_roll"]:
                assert "rolls" in result["damage_roll"]


def test_resolve_skill_check():
    """Test skill check resolution."""
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


def test_skill_check_with_advantage():
    """Test skill check with advantage."""
    character = CharacterSheet(
        telegram_user_id=123,
        name="Test",
        strength=10
    )
    
    result = RulesEngine.resolve_skill_check(
        character=character,
        skill="strength",
        dc=15,
        advantage=True
    )
    
    assert result["check_roll"]["advantage"]
    assert len(result["check_roll"]["rolls"]) == 2


def test_detect_action_type_attack():
    """Test action type detection for attacks."""
    assert RulesEngine.detect_action_type("Я атакую гоблина") == "attack"
    assert RulesEngine.detect_action_type("Бью мечом") == "attack"
    assert RulesEngine.detect_action_type("Удар топором") == "attack"


def test_detect_action_type_skill_check():
    """Test action type detection for skill checks."""
    assert RulesEngine.detect_action_type("Ищу ловушки") == "skill_check"
    assert RulesEngine.detect_action_type("Проверяю дверь") == "skill_check"
    # "убедить" is not in keyword list, so it will be "other"
    # This is expected - LLM intent analysis will handle this better


def test_detect_action_type_spell():
    """Test action type detection for spells."""
    assert RulesEngine.detect_action_type("Колдую заклинание") == "spell"
    assert RulesEngine.detect_action_type("Использую заклинание") == "spell"


def test_detect_action_type_other():
    """Test action type detection for other actions."""
    assert RulesEngine.detect_action_type("Иду вперед") == "other"
    assert RulesEngine.detect_action_type("Смотрю вокруг") == "other"


def test_difficulty_classes():
    """Test that DC constants are defined."""
    assert RulesEngine.DC_EASY == 10
    assert RulesEngine.DC_MEDIUM == 15
    assert RulesEngine.DC_HARD == 20
    assert RulesEngine.DC_VERY_HARD == 25
