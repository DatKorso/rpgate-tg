"""Tests for Response Synthesizer Agent."""

import pytest
from app.agents.response_synthesizer import ResponseSynthesizerAgent
from app.game.character import CharacterSheet


def test_sanitize_markdown_unbalanced_bold():
    """Test that unbalanced ** is fixed."""
    agent = ResponseSynthesizerAgent()
    
    # Unbalanced bold - odd number of **
    text = "This is **bold text and another **bold but unclosed"
    sanitized = agent._sanitize_markdown(text)
    
    # Should not have odd number of **
    assert sanitized.count("**") % 2 == 0


def test_sanitize_markdown_unbalanced_brackets():
    """Test that unbalanced brackets are escaped."""
    agent = ResponseSynthesizerAgent()
    
    # Unbalanced brackets
    text = "You see [a mysterious door but it's not closed properly"
    sanitized = agent._sanitize_markdown(text)
    
    # Should have escaped brackets OR no raw brackets
    # Check that there are no unescaped brackets
    assert r"\[" in sanitized or ("[" not in sanitized)


def test_sanitize_markdown_unbalanced_underscores():
    """Test that unbalanced underscores are escaped."""
    agent = ResponseSynthesizerAgent()
    
    # Unbalanced underscores
    text = "The treasure_chest has a weird_name"
    sanitized = agent._sanitize_markdown(text)
    
    # Should have balanced or escaped underscores
    assert sanitized.count("_") % 2 == 0 or r"\_" in sanitized


def test_sanitize_markdown_valid_text():
    """Test that valid Markdown passes through mostly unchanged."""
    agent = ResponseSynthesizerAgent()
    
    # Valid Markdown
    text = "This is **bold** and this is normal text."
    sanitized = agent._sanitize_markdown(text)
    
    # Should keep the bold markers
    assert "**bold**" in sanitized


def test_format_character_status():
    """Test character status formatting."""
    agent = ResponseSynthesizerAgent()
    
    character = CharacterSheet(
        telegram_user_id=12345,
        name="Test Hero",
        hp=15,
        max_hp=20,
        location="test_dungeon"
    )
    
    game_state = {"location": "dark_cave"}
    
    status = agent._format_character_status(character, game_state)
    
    # Should contain HP and location
    assert "15/20" in status
    assert "dark_cave" in status


def test_format_attack_critical():
    """Test critical hit formatting."""
    agent = ResponseSynthesizerAgent()
    
    mechanics = {
        "action_type": "attack",
        "attack_roll": {"roll": 20, "modifier": 3, "total": 23},
        "hit": True,
        "is_critical": True,
        "total_damage": 18,
        "target_ac": 15,
        "damage_roll": {"rolls": [8, 7], "modifier": 3}
    }
    
    formatted = agent._format_attack(mechanics)
    
    # Should indicate critical
    assert "💥" in formatted or "КРИТИЧЕСК" in formatted
    assert "18 HP" in formatted


def test_format_skill_check_success():
    """Test skill check success formatting."""
    agent = ResponseSynthesizerAgent()
    
    mechanics = {
        "action_type": "skill_check",
        "skill": "perception",
        "check_roll": {"roll": 15, "modifier": 2, "total": 17},
        "dc": 15,
        "success": True
    }
    
    formatted = agent._format_skill_check(mechanics)
    
    # Should show success
    assert "✅" in formatted or "Успех" in formatted
    assert "17" in formatted


def test_format_skill_check_with_advantage():
    """Test skill check with advantage formatting."""
    agent = ResponseSynthesizerAgent()
    
    mechanics = {
        "action_type": "skill_check",
        "skill": "stealth",
        "check_roll": {
            "rolls": [8, 15],
            "chosen": 15,
            "advantage": True,
            "modifier": 3,
            "total": 18
        },
        "dc": 14,
        "success": True
    }
    
    formatted = agent._format_skill_check(mechanics)
    
    # Should show advantage and both rolls
    assert "преимущество" in formatted
    assert "[8, 15]" in formatted
