"""JSON schemas for structured LLM outputs."""

from typing import TypedDict


# Rules Arbiter Intent Analysis Schema
INTENT_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "action_type": {
            "type": "string",
            "enum": ["attack", "skill_check", "movement", "dialogue", "spell", "other"],
            "description": "Type of player action"
        },
        "requires_roll": {
            "type": "boolean",
            "description": "Whether action requires dice roll"
        },
        "roll_type": {
            "type": ["string", "null"],
            "enum": ["attack_roll", "skill_check", "saving_throw", None],
            "description": "Type of roll needed"
        },
        "skill": {
            "type": ["string", "null"],
            "description": "Skill name if skill check (strength, dexterity, etc)"
        },
        "target": {
            "type": ["string", "null"],
            "description": "Target of action if applicable"
        },
        "difficulty": {
            "type": ["string", "null"],
            "enum": ["easy", "medium", "hard", "very_hard", None],
            "description": "Difficulty level for skill checks"
        },
        "reasoning": {
            "type": "string",
            "description": "Brief explanation in Russian"
        }
    },
    "required": ["action_type", "requires_roll", "reasoning"],
    "additionalProperties": False
}


# Narrative Director Combat State Schema
COMBAT_STATE_SCHEMA = {
    "type": "object",
    "properties": {
        "in_combat": {
            "type": "boolean",
            "description": "Whether player is currently in active combat"
        },
        "enemies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of enemy names (empty if combat ended)"
        },
        "combat_ended": {
            "type": "boolean",
            "description": "True if combat just ended (all enemies defeated)"
        },
        "enemy_attacks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "attacker": {
                        "type": "string",
                        "description": "Name of attacking enemy"
                    },
                    "damage": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "HP damage dealt"
                    }
                },
                "required": ["attacker", "damage"]
            },
            "description": "Enemy attacks this round (empty if no attacks)"
        }
    },
    "required": ["in_combat", "enemies", "combat_ended", "enemy_attacks"],
    "additionalProperties": False
}


# World State Update Schema (Sprint 3)
WORLD_STATE_SCHEMA = {
    "type": "object",
    "properties": {
        "location_changes": {
            "type": "object",
            "properties": {
                "new_location": {"type": ["string", "null"]},
                "discovered_areas": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "inventory_changes": {
            "type": "object",
            "properties": {
                "added_items": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "removed_items": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "gold_change": {"type": "integer"}
            }
        },
        "quest_updates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quest_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["started", "updated", "completed", "failed"]
                    },
                    "description": {"type": "string"}
                }
            }
        },
        "npc_relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "npc_name": {"type": "string"},
                    "relationship_change": {
                        "type": "integer",
                        "minimum": -10,
                        "maximum": 10
                    }
                }
            }
        }
    }
}


# Type hints for Python
class IntentAnalysis(TypedDict):
    """Type hint for intent analysis output."""
    action_type: str
    requires_roll: bool
    roll_type: str | None
    skill: str | None
    target: str | None
    difficulty: str | None
    reasoning: str


class EnemyAttack(TypedDict):
    """Type hint for single enemy attack."""
    attacker: str
    damage: int


class CombatState(TypedDict):
    """Type hint for combat state output."""
    in_combat: bool
    enemies: list[str]
    combat_ended: bool
    enemy_attacks: list[EnemyAttack]
