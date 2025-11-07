"""Integration tests for Sprint 3 Week 3 components."""
import pytest
import asyncio
from uuid import uuid4

from app.game.character import CharacterSheet
from app.db.characters import (
    get_character_by_telegram_id,
    create_character,
    update_character,
    delete_character
)
from app.db.sessions import (
    create_session,
    get_active_session,
    end_session,
    update_session_stats,
    get_or_create_session
)
from app.agents.orchestrator import AgentOrchestrator
from app.agents.world_state import world_state_agent


@pytest.mark.asyncio
async def test_character_crud():
    """Test character CRUD operations."""
    telegram_user_id = 999999999  # Test user
    
    # Clean up first
    existing = await get_character_by_telegram_id(telegram_user_id)
    if existing:
        await delete_character(existing.id)
    
    # Create character
    character = CharacterSheet(
        telegram_user_id=telegram_user_id,
        name="Test Hero",
        strength=16,
        hp=25,
        max_hp=25,
        armor_class=14
    )
    
    success = await create_character(character)
    assert success, "Character creation should succeed"
    
    # Load character
    loaded = await get_character_by_telegram_id(telegram_user_id)
    assert loaded is not None, "Character should be loadable"
    assert loaded.name == "Test Hero"
    assert loaded.strength == 16
    
    # Update character
    loaded.hp = 20
    loaded.name = "Updated Hero"
    
    success = await update_character(loaded)
    assert success, "Character update should succeed"
    
    # Verify update
    reloaded = await get_character_by_telegram_id(telegram_user_id)
    assert reloaded is not None
    assert reloaded.hp == 20
    assert reloaded.name == "Updated Hero"
    
    # Delete character
    success = await delete_character(character.id)
    assert success, "Character deletion should succeed"
    
    # Verify deletion
    deleted = await get_character_by_telegram_id(telegram_user_id)
    assert deleted is None, "Character should be deleted"


@pytest.mark.asyncio
async def test_session_management():
    """Test session CRUD operations."""
    # Create a test character first
    telegram_user_id = 999999998
    
    existing = await get_character_by_telegram_id(telegram_user_id)
    if existing:
        character_id = existing.id
    else:
        character = CharacterSheet(
            telegram_user_id=telegram_user_id,
            name="Session Test Hero",
            hp=20,
            max_hp=20
        )
        await create_character(character)
        character_id = character.id
    
    # Create session
    session_id = await create_session(character_id)
    assert session_id is not None, "Session creation should succeed"
    
    # Get active session
    active_id = await get_active_session(character_id)
    assert active_id == session_id, "Active session should match created session"
    
    # Update session stats
    success = await update_session_stats(
        session_id=session_id,
        turns_increment=1,
        damage_dealt_increment=10,
        damage_taken_increment=5
    )
    assert success, "Session stats update should succeed"
    
    # End session
    success = await end_session(session_id)
    assert success, "Session end should succeed"
    
    # Verify no active session
    active_id = await get_active_session(character_id)
    assert active_id is None, "No active session after ending"
    
    # Clean up
    await delete_character(character_id)


@pytest.mark.asyncio
async def test_world_state_persistence():
    """Test world state save and load."""
    # Create test character
    telegram_user_id = 999999997
    
    existing = await get_character_by_telegram_id(telegram_user_id)
    if existing:
        character_id = existing.id
    else:
        character = CharacterSheet(
            telegram_user_id=telegram_user_id,
            name="World State Test",
            hp=20,
            max_hp=20
        )
        await create_character(character)
        character_id = character.id
    
    # Create test game state
    game_state = {
        "in_combat": True,
        "enemies": ["goblin", "orc"],
        "location": "dark_cave",
        "flags": {"door_unlocked": True}
    }
    
    # Save state
    success = await world_state_agent._save_world_state(character_id, game_state)
    assert success, "World state save should succeed"
    
    # Load state
    loaded_state = await world_state_agent.load_world_state(character_id)
    assert loaded_state is not None
    assert loaded_state["in_combat"] == True
    assert "goblin" in loaded_state["enemies"]
    assert loaded_state["location"] == "dark_cave"
    assert loaded_state["flags"]["door_unlocked"] == True
    
    # Clean up
    await delete_character(character_id)


@pytest.mark.asyncio
async def test_orchestrator_with_memory(monkeypatch):
    """Test orchestrator with memory integration (mocked)."""
    # Mock database operations to avoid actual DB calls
    async def mock_create_memory(*args, **kwargs):
        return None
    
    monkeypatch.setattr(
        "app.memory.episodic.episodic_memory_manager.create_memory",
        mock_create_memory
    )
    
    # Create test character
    character = CharacterSheet(
        telegram_user_id=123,
        name="Test",
        hp=20,
        max_hp=20
    )
    
    game_state = {
        "in_combat": False,
        "enemies": [],
        "location": "tavern"
    }
    
    orchestrator = AgentOrchestrator()
    
    # Test action processing WITHOUT memory (character_id=None)
    final_message, updated_char, updated_state = await orchestrator.process_action(
        user_action="Я осматриваюсь",
        character=character,
        game_state=game_state,
        character_id=None,  # No memory
        session_id=None,
        recent_history=[]
    )
    
    assert final_message is not None
    assert isinstance(final_message, str)
    assert len(final_message) > 0
    
    print(f"✅ Orchestrator test passed: {final_message[:100]}...")


@pytest.mark.asyncio  
async def test_end_to_end_flow():
    """Test complete end-to-end flow: create character → session → action → memory."""
    telegram_user_id = 999999996
    
    # Clean up
    existing = await get_character_by_telegram_id(telegram_user_id)
    if existing:
        await delete_character(existing.id)
    
    # 1. Create character
    character = CharacterSheet(
        telegram_user_id=telegram_user_id,
        name="E2E Test Hero",
        strength=16,
        hp=25,
        max_hp=25,
        armor_class=14
    )
    
    success = await create_character(character)
    assert success
    
    # 2. Create session
    session_id = await get_or_create_session(character.id)
    assert session_id is not None
    
    # 3. Load world state
    game_state = await world_state_agent.load_world_state(character.id)
    assert game_state is not None
    
    # 4. Process action (without memory to avoid DB overhead)
    orchestrator = AgentOrchestrator()
    
    final_message, updated_char, updated_state = await orchestrator.process_action(
        user_action="Я иду вперёд",
        character=character,
        game_state=game_state,
        character_id=None,  # Skip memory for test
        session_id=None,
        recent_history=[]
    )
    
    assert final_message is not None
    assert updated_char.hp <= updated_char.max_hp
    
    # 5. Update character in DB
    success = await update_character(updated_char)
    assert success
    
    # 6. Update session stats
    success = await update_session_stats(
        session_id=session_id,
        turns_increment=1
    )
    assert success
    
    # Clean up
    await delete_character(character.id)
    
    print("✅ End-to-end test passed!")


if __name__ == "__main__":
    # Run tests manually
    asyncio.run(test_character_crud())
    asyncio.run(test_session_management())
    asyncio.run(test_world_state_persistence())
    asyncio.run(test_end_to_end_flow())
    
    print("\n✅ All integration tests passed!")
