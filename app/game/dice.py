"""Dice rolling system for game mechanics."""

import random
from typing import Literal

DiceType = Literal["d4", "d6", "d8", "d10", "d12", "d20", "d100"]


class DiceRoller:
    """Dice rolling system for game mechanics."""
    
    DICE_SIDES = {
        "d4": 4,
        "d6": 6,
        "d8": 8,
        "d10": 10,
        "d12": 12,
        "d20": 20,
        "d100": 100,
    }
    
    @staticmethod
    def roll(dice: DiceType, modifier: int = 0) -> dict:
        """
        Roll a dice with optional modifier.
        
        Args:
            dice: Type of dice (d4, d6, etc)
            modifier: Modifier to add to roll
            
        Returns:
            {
                "dice": "d20",
                "roll": 15,
                "modifier": 3,
                "total": 18,
                "is_critical": False,
                "is_fumble": False
            }
        """
        sides = DiceRoller.DICE_SIDES[dice]
        roll = random.randint(1, sides)
        total = roll + modifier
        
        # Critical hit/fumble only for d20
        is_critical = (dice == "d20" and roll == 20)
        is_fumble = (dice == "d20" and roll == 1)
        
        return {
            "dice": dice,
            "roll": roll,
            "modifier": modifier,
            "total": total,
            "is_critical": is_critical,
            "is_fumble": is_fumble,
        }
    
    @staticmethod
    def roll_multiple(dice: DiceType, count: int, modifier: int = 0) -> dict:
        """
        Roll multiple dice and sum them.
        
        Args:
            dice: Type of dice
            count: Number of dice to roll
            modifier: Modifier to add to total
            
        Returns:
            {
                "dice": "2d6",
                "rolls": [4, 5],
                "modifier": 2,
                "total": 11
            }
        """
        sides = DiceRoller.DICE_SIDES[dice]
        rolls = [random.randint(1, sides) for _ in range(count)]
        total = sum(rolls) + modifier
        
        return {
            "dice": f"{count}{dice}",
            "rolls": rolls,
            "modifier": modifier,
            "total": total,
        }
    
    @staticmethod
    def roll_with_advantage() -> dict:
        """
        Roll d20 with advantage (roll twice, take higher).
        D&D 5e mechanic.
        """
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        chosen = max(roll1, roll2)
        
        return {
            "dice": "d20",
            "rolls": [roll1, roll2],
            "chosen": chosen,
            "advantage": True,
            "is_critical": (chosen == 20),
            "is_fumble": (chosen == 1),
        }
    
    @staticmethod
    def roll_with_disadvantage() -> dict:
        """Roll d20 with disadvantage (roll twice, take lower)."""
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        chosen = min(roll1, roll2)
        
        return {
            "dice": "d20",
            "rolls": [roll1, roll2],
            "chosen": chosen,
            "disadvantage": True,
            "is_critical": (chosen == 20),
            "is_fumble": (chosen == 1),
        }


# Convenience functions
def d4(modifier: int = 0) -> dict:
    """Roll d4 with optional modifier."""
    return DiceRoller.roll("d4", modifier)

def d6(modifier: int = 0) -> dict:
    """Roll d6 with optional modifier."""
    return DiceRoller.roll("d6", modifier)

def d8(modifier: int = 0) -> dict:
    """Roll d8 with optional modifier."""
    return DiceRoller.roll("d8", modifier)

def d10(modifier: int = 0) -> dict:
    """Roll d10 with optional modifier."""
    return DiceRoller.roll("d10", modifier)

def d12(modifier: int = 0) -> dict:
    """Roll d12 with optional modifier."""
    return DiceRoller.roll("d12", modifier)

def d20(modifier: int = 0) -> dict:
    """Roll d20 with optional modifier."""
    return DiceRoller.roll("d20", modifier)

def d100(modifier: int = 0) -> dict:
    """Roll d100 with optional modifier."""
    return DiceRoller.roll("d100", modifier)
