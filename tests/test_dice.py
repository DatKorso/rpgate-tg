"""Tests for DiceRoller system."""

import pytest
from app.game.dice import DiceRoller, d20


def test_d20_roll():
    """Test basic d20 roll."""
    result = DiceRoller.roll("d20", modifier=3)
    assert result["dice"] == "d20"
    assert 1 <= result["roll"] <= 20
    assert result["total"] == result["roll"] + 3
    assert "is_critical" in result
    assert "is_fumble" in result


def test_critical_hit_detection():
    """Test that nat 20 is detected as critical."""
    # We can't guarantee a nat 20, but we can test the logic
    for _ in range(100):
        result = d20()
        if result["roll"] == 20:
            assert result["is_critical"]
            assert not result["is_fumble"]
        elif result["roll"] == 1:
            assert result["is_fumble"]
            assert not result["is_critical"]
        else:
            assert not result["is_critical"]
            assert not result["is_fumble"]


def test_roll_multiple():
    """Test rolling multiple dice."""
    result = DiceRoller.roll_multiple("d6", count=2, modifier=3)
    assert result["dice"] == "2d6"
    assert len(result["rolls"]) == 2
    assert all(1 <= r <= 6 for r in result["rolls"])
    assert result["total"] == sum(result["rolls"]) + 3


def test_advantage():
    """Test advantage mechanic."""
    result = DiceRoller.roll_with_advantage()
    assert result["advantage"]
    assert len(result["rolls"]) == 2
    assert result["chosen"] == max(result["rolls"])


def test_disadvantage():
    """Test disadvantage mechanic."""
    result = DiceRoller.roll_with_disadvantage()
    assert result["disadvantage"]
    assert len(result["rolls"]) == 2
    assert result["chosen"] == min(result["rolls"])


def test_all_dice_types():
    """Test that all dice types work."""
    from app.game.dice import d4, d6, d8, d10, d12, d100
    
    dice_funcs = [d4, d6, d8, d10, d12, d20, d100]
    expected_sides = [4, 6, 8, 10, 12, 20, 100]
    
    for dice_func, sides in zip(dice_funcs, expected_sides):
        result = dice_func()
        assert 1 <= result["roll"] <= sides
