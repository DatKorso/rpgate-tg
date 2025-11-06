"""Tests for CharacterSheet model."""

import pytest
from app.game.character import CharacterSheet


def test_character_creation():
    """Test basic character creation."""
    char = CharacterSheet(telegram_user_id=12345, name="Артур")
    assert char.name == "Артур"
    assert char.level == 1
    assert char.hp == 20
    assert char.max_hp == 20


def test_strength_modifier():
    """Test strength modifier calculation."""
    char = CharacterSheet(telegram_user_id=12345, name="Test", strength=16)
    assert char.strength_mod == 3  # (16-10)//2 = 3
    
    char2 = CharacterSheet(telegram_user_id=12345, name="Test", strength=8)
    assert char2.strength_mod == -1  # (8-10)//2 = -1


def test_take_damage():
    """Test damage application."""
    char = CharacterSheet(telegram_user_id=12345, name="Test", hp=20)
    damage = char.take_damage(5)
    assert damage == 5
    assert char.hp == 15
    assert char.is_alive()


def test_death():
    """Test character death."""
    char = CharacterSheet(telegram_user_id=12345, name="Test", hp=5)
    char.take_damage(10)
    assert char.hp == 0
    assert not char.is_alive()


def test_heal():
    """Test healing."""
    char = CharacterSheet(telegram_user_id=12345, name="Test", hp=10, max_hp=20)
    healed = char.heal(7)
    assert healed == 7
    assert char.hp == 17


def test_heal_over_max():
    """Test that healing doesn't exceed max HP."""
    char = CharacterSheet(telegram_user_id=12345, name="Test", hp=18, max_hp=20)
    healed = char.heal(5)
    assert healed == 2  # Only healed up to max
    assert char.hp == 20


def test_all_modifiers():
    """Test all attribute modifiers."""
    char = CharacterSheet(
        telegram_user_id=12345,
        name="Test",
        strength=14,
        dexterity=16,
        constitution=12,
        intelligence=10,
        wisdom=8,
        charisma=18
    )
    
    assert char.strength_mod == 2
    assert char.dexterity_mod == 3
    assert char.constitution_mod == 1
    assert char.intelligence_mod == 0
    assert char.wisdom_mod == -1
    assert char.charisma_mod == 4
