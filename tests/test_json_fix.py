"""Tests for JSON syntax fixing in Narrative Director."""

import pytest
import json
from app.agents.narrative_director import NarrativeDirectorAgent


def test_fix_missing_comma_between_fields():
    """Test fixing missing comma between JSON fields."""
    agent = NarrativeDirectorAgent()
    
    # Missing comma before "enemies"
    broken_json = '{"in_combat": true "enemies": ["wolf"]}'
    fixed = agent._fix_json_syntax(broken_json)
    
    # Should be parseable now
    result = json.loads(fixed)
    assert result["in_combat"] is True
    assert result["enemies"] == ["wolf"]


def test_fix_missing_comma_after_number():
    """Test fixing missing comma after number value."""
    agent = NarrativeDirectorAgent()
    
    broken_json = '{"damage": 9 "attacker": "wolf"}'
    fixed = agent._fix_json_syntax(broken_json)
    
    result = json.loads(fixed)
    assert result["damage"] == 9
    assert result["attacker"] == "wolf"


def test_fix_trailing_comma():
    """Test removing trailing commas."""
    agent = NarrativeDirectorAgent()
    
    broken_json = '{"in_combat": true, "enemies": ["wolf",],}'
    fixed = agent._fix_json_syntax(broken_json)
    
    result = json.loads(fixed)
    assert result["in_combat"] is True
    assert result["enemies"] == ["wolf"]


def test_fix_complex_combat_state():
    """Test fixing realistic broken combat state JSON."""
    agent = NarrativeDirectorAgent()
    
    # Typical LLM error - missing comma before "combat_ended"
    broken_json = '{"in_combat": true, "enemies": ["dark entity"] "combat_ended": false, "enemy_attacks": []}'
    fixed = agent._fix_json_syntax(broken_json)
    
    result = json.loads(fixed)
    assert result["in_combat"] is True
    assert result["enemies"] == ["dark entity"]
    assert result["combat_ended"] is False
    assert result["enemy_attacks"] == []


def test_fix_with_enemy_attacks():
    """Test fixing JSON with enemy_attacks array."""
    agent = NarrativeDirectorAgent()
    
    # Missing comma before "damage"
    broken_json = '{"in_combat": true, "enemies": ["wolf"], "combat_ended": false, "enemy_attacks": [{"attacker": "wolf" "damage": 9}]}'
    fixed = agent._fix_json_syntax(broken_json)
    
    result = json.loads(fixed)
    assert result["enemy_attacks"][0]["attacker"] == "wolf"
    assert result["enemy_attacks"][0]["damage"] == 9


def test_parse_narrative_with_broken_json():
    """Test full narrative parsing with broken JSON that can be fixed."""
    agent = NarrativeDirectorAgent()
    
    # Simulate LLM response with broken JSON
    response = """Тёмная сущность атакует тебя из теней!

COMBAT_STATE: {"in_combat": true, "enemies": ["dark entity"] "combat_ended": false, "enemy_attacks": [{"attacker": "dark entity" "damage": 8}]}"""
    
    current_game_state = {"in_combat": True, "enemies": ["dark entity"], "location": "ruins"}
    
    narrative, game_state = agent._parse_narrative_response(response, current_game_state)
    
    # Should successfully parse after fixing
    assert "Тёмная сущность атакует" in narrative
    assert game_state["in_combat"] is True
    assert game_state["enemies"] == ["dark entity"]
    assert len(game_state["enemy_attacks"]) == 1
    assert game_state["enemy_attacks"][0]["damage"] == 8


def test_parse_narrative_unfixable_json():
    """Test that unfixable JSON falls back to current game state."""
    agent = NarrativeDirectorAgent()
    
    # Completely broken JSON
    response = """Some narrative text.

COMBAT_STATE: {this is not json at all!!!}"""
    
    current_game_state = {"in_combat": True, "enemies": ["wolf"]}
    
    narrative, game_state = agent._parse_narrative_response(response, current_game_state)
    
    # Should fallback to current state
    assert game_state == current_game_state
    assert "Some narrative text" in narrative or narrative == response


def test_valid_json_passes_through():
    """Test that already valid JSON is not broken by fixing."""
    agent = NarrativeDirectorAgent()
    
    valid_json = '{"in_combat": true, "enemies": ["wolf"], "combat_ended": false, "enemy_attacks": [{"attacker": "wolf", "damage": 9}]}'
    fixed = agent._fix_json_syntax(valid_json)
    
    # Should parse successfully
    original = json.loads(valid_json)
    result = json.loads(fixed)
    
    assert original == result
