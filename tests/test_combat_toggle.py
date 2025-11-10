import pytest

from app.agents.orchestrator import AgentOrchestrator
from app.game.character import CharacterSheet


@pytest.mark.asyncio
async def test_combat_disabled_narrative_only():
    orchestrator = AgentOrchestrator()
    character = CharacterSheet(
        telegram_user_id=999,
        name="Тест",
        strength=16,
        dexterity=12,
        constitution=14,
        intelligence=10,
        wisdom=10,
        charisma=10,
        hp=20,
        max_hp=20,
        armor_class=14,
        location="test_location",
    )
    game_state = {"in_combat": False, "enemies": ["гоблин"], "location": "test_location", "combat_ended": False}
    final_message, updated_character, updated_game_state = await orchestrator.process_action(
        user_action="Я атакую гоблина мечом",
        character=character,
        game_state=game_state,
        character_id=None,
        session_id=None,
        recent_history=[],
        user_settings={"combat_enabled": False},
    )
    assert "🎲 **Атака**" not in final_message
    assert "Урон" not in final_message
    assert ("HP" in final_message or "HP:" in final_message)


@pytest.mark.asyncio
async def test_combat_enabled_shows_mechanics():
    orchestrator = AgentOrchestrator()
    character = CharacterSheet(
        telegram_user_id=1000,
        name="Тест2",
        strength=16,
        dexterity=12,
        constitution=14,
        intelligence=10,
        wisdom=10,
        charisma=10,
        hp=20,
        max_hp=20,
        armor_class=14,
        location="test_location",
    )
    game_state = {"in_combat": True, "enemies": ["гоблин"], "location": "test_location", "combat_ended": False}
    final_message, updated_character, updated_game_state = await orchestrator.process_action(
        user_action="Я атакую гоблина мечом",
        character=character,
        game_state=game_state,
        character_id=None,
        session_id=None,
        recent_history=[],
        user_settings={"combat_enabled": True},
    )
    # Mechanics should include attack formatting (dice or attack line)
    assert ("🎲 **Атака**" in final_message) or ("Атака" in final_message)
    # Allow critical fumble case without damage text
    assert ("Урон" in final_message) or ("Попадание" in final_message) or ("Промах" in final_message) or ("Критичес" in final_message)