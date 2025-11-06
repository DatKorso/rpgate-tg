"""Rules engine for resolving game actions."""

from typing import Literal
from app.game.dice import DiceRoller, DiceType
from app.game.character import CharacterSheet

ActionType = Literal["attack", "skill_check", "spell", "other"]


class RulesEngine:
    """Game rules engine for resolving actions."""
    
    # Difficulty Classes for skill checks
    DC_EASY = 10
    DC_MEDIUM = 15
    DC_HARD = 20
    DC_VERY_HARD = 25
    
    @staticmethod
    def resolve_attack(
        attacker: CharacterSheet,
        target_ac: int,
        weapon_damage_dice: DiceType = "d8"
    ) -> dict:
        """
        Resolve melee attack.
        
        Args:
            attacker: Attacking character
            target_ac: Target's armor class
            weapon_damage_dice: Damage dice (e.g., "d8" for longsword)
            
        Returns:
            {
                "action_type": "attack",
                "attack_roll": {...},
                "hit": True/False,
                "damage_roll": {...} or None,
                "total_damage": int,
                "is_critical": bool,
                "is_fumble": bool
            }
        """
        # Attack roll: d20 + strength modifier
        attack_roll = DiceRoller.roll("d20", modifier=attacker.strength_mod)
        
        # Check if hit
        hit = attack_roll["total"] >= target_ac or attack_roll["is_critical"]
        
        # Damage roll if hit
        damage_roll = None
        total_damage = 0
        
        if hit:
            # Critical hit = double damage dice
            if attack_roll["is_critical"]:
                damage_roll = DiceRoller.roll_multiple(
                    weapon_damage_dice, 
                    count=2, 
                    modifier=attacker.strength_mod
                )
            else:
                damage_roll = DiceRoller.roll(
                    weapon_damage_dice, 
                    modifier=attacker.strength_mod
                )
            
            total_damage = damage_roll["total"]
        
        return {
            "action_type": "attack",
            "attack_roll": attack_roll,
            "target_ac": target_ac,
            "hit": hit,
            "damage_roll": damage_roll,
            "total_damage": total_damage,
            "is_critical": attack_roll["is_critical"],
            "is_fumble": attack_roll["is_fumble"],
        }
    
    @staticmethod
    def resolve_skill_check(
        character: CharacterSheet,
        skill: str,
        dc: int,
        advantage: bool = False,
        disadvantage: bool = False
    ) -> dict:
        """
        Resolve skill check.
        
        Args:
            character: Character making check
            skill: Skill name (strength, dexterity, wisdom, etc)
            dc: Difficulty Class
            advantage: Roll with advantage
            disadvantage: Roll with disadvantage
            
        Returns:
            {
                "action_type": "skill_check",
                "skill": "strength",
                "check_roll": {...},
                "dc": 15,
                "success": True/False
            }
        """
        # Get appropriate modifier
        skill_modifiers = {
            "strength": character.strength_mod,
            "dexterity": character.dexterity_mod,
            "constitution": character.constitution_mod,
            "intelligence": character.intelligence_mod,
            "wisdom": character.wisdom_mod,
            "charisma": character.charisma_mod,
        }
        
        modifier = skill_modifiers.get(skill.lower(), 0)
        
        # Roll with advantage/disadvantage
        if advantage:
            check_roll = DiceRoller.roll_with_advantage()
            check_roll["total"] = check_roll["chosen"] + modifier
            check_roll["modifier"] = modifier
        elif disadvantage:
            check_roll = DiceRoller.roll_with_disadvantage()
            check_roll["total"] = check_roll["chosen"] + modifier
            check_roll["modifier"] = modifier
        else:
            check_roll = DiceRoller.roll("d20", modifier=modifier)
        
        success = check_roll["total"] >= dc
        
        return {
            "action_type": "skill_check",
            "skill": skill,
            "check_roll": check_roll,
            "dc": dc,
            "success": success,
            "is_critical": check_roll.get("is_critical", False),
        }
    
    @staticmethod
    def detect_action_type(user_input: str) -> ActionType:
        """
        Detect action type from user input.
        Simple keyword matching for MVP.
        
        Args:
            user_input: User's action text
            
        Returns:
            ActionType ("attack", "skill_check", "spell", "other")
        """
        user_input_lower = user_input.lower()
        
        # Attack keywords (Russian)
        attack_keywords = ["атак", "удар", "бью", "напада", "меч", "топор", "лук"]
        if any(keyword in user_input_lower for keyword in attack_keywords):
            return "attack"
        
        # Skill check keywords (Russian)
        skill_keywords = [
            "провер", "ищу", "открыва", "взламыва", "убежда", 
            "обманыва", "прыга", "лезу", "слуша"
        ]
        if any(keyword in user_input_lower for keyword in skill_keywords):
            return "skill_check"
        
        # Spell keywords (Russian)
        spell_keywords = ["заклинан", "магия", "колд", "закля"]
        if any(keyword in user_input_lower for keyword in spell_keywords):
            return "spell"
        
        return "other"
