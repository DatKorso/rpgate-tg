"""Tests for World State Agent."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.agents.world_state import WorldStateAgent, world_state_agent


@pytest.fixture
def sample_character_id():
    """Sample character UUID."""
    return uuid4()


@pytest.fixture
def sample_game_state():
    """Sample game state."""
    return {
        "in_combat": True,
        "enemies": ["гоблин", "волк"],
        "location": "forest",
        "quests": [],
        "flags": {}
    }


@pytest.mark.asyncio
async def test_world_state_initialization():
    """Test that World State Agent initializes correctly."""
    agent = WorldStateAgent()
    
    assert agent.name == "WorldState"


@pytest.mark.asyncio
async def test_execute_updates_state(sample_character_id, sample_game_state):
    """Test that execute updates game state correctly."""
    agent = WorldStateAgent()
    
    with patch.object(agent, '_save_world_state', new=AsyncMock(return_value=True)):
        context = {
            "character_id": sample_character_id,
            "game_state": sample_game_state,
            "mechanics_result": {
                "hit": True,
                "total_damage": 10
            },
            "action_type": "attack"
        }
        
        result = await agent.execute(context)
        
        # Verify result structure
        assert "updated_game_state" in result
        assert "state_changes" in result
        assert "persisted" in result
        
        # Verify state was saved
        assert result["persisted"] is True


@pytest.mark.asyncio
async def test_execute_handles_errors(sample_character_id, sample_game_state):
    """Test that execute handles errors gracefully."""
    agent = WorldStateAgent()
    
    with patch.object(
        agent, 
        '_save_world_state', 
        new=AsyncMock(side_effect=Exception("DB error"))
    ):
        context = {
            "character_id": sample_character_id,
            "game_state": sample_game_state,
            "mechanics_result": {},
            "action_type": "other"
        }
        
        result = await agent.execute(context)
        
        # Should return unchanged state on error
        assert result["updated_game_state"] == sample_game_state
        assert result["persisted"] is False
        assert "❌" in result["state_changes"][0]


@pytest.mark.asyncio
async def test_apply_narrative_updates_combat_started():
    """Test applying narrative updates for combat start."""
    agent = WorldStateAgent()
    
    state = {"in_combat": False, "enemies": []}
    changes = []
    
    narrative_updates = {
        "in_combat": True,
        "enemies": ["гоблин"]
    }
    
    agent._apply_narrative_updates(state, narrative_updates, changes)
    
    assert state["in_combat"] is True
    assert state["enemies"] == ["гоблин"]
    assert "начался" in changes[0]


@pytest.mark.asyncio
async def test_apply_narrative_updates_combat_ended():
    """Test applying narrative updates for combat end."""
    agent = WorldStateAgent()
    
    state = {"in_combat": True, "enemies": ["гоблин"]}
    changes = []
    
    narrative_updates = {
        "combat_ended": True
    }
    
    agent._apply_narrative_updates(state, narrative_updates, changes)
    
    assert state["in_combat"] is False
    assert state["enemies"] == []
    assert "завершен" in changes[0]


@pytest.mark.asyncio
async def test_apply_narrative_updates_enemy_attacks():
    """Test applying narrative updates with enemy attacks."""
    agent = WorldStateAgent()
    
    state = {}
    changes = []
    
    narrative_updates = {
        "enemy_attacks": [
            {"attacker": "гоблин", "damage": 5},
            {"attacker": "волк", "damage": 3}
        ]
    }
    
    agent._apply_narrative_updates(state, narrative_updates, changes)
    
    assert "enemy_attacks" in state
    assert len(state["enemy_attacks"]) == 2
    assert "8 урона" in changes[0]


@pytest.mark.asyncio
async def test_handle_combat_update_enemy_defeated():
    """Test combat update when enemy is defeated."""
    agent = WorldStateAgent()
    
    state = {
        "in_combat": True,
        "enemies": ["гоблин", "волк"]
    }
    changes = []
    
    mechanics_result = {
        "hit": True,
        "total_damage": 10  # >= 7, enemy defeated
    }
    
    agent._handle_combat_update(state, mechanics_result, changes)
    
    # First enemy should be removed
    assert len(state["enemies"]) == 1
    assert "гоблин" not in state["enemies"]
    assert "волк" in state["enemies"]
    
    # Combat should still be active (more enemies)
    assert state["in_combat"] is True
    
    # Should have defeat message
    assert any("повержен" in change for change in changes)


@pytest.mark.asyncio
async def test_handle_combat_update_all_enemies_defeated():
    """Test combat update when all enemies are defeated."""
    agent = WorldStateAgent()
    
    state = {
        "in_combat": True,
        "enemies": ["гоблин"]  # Only one enemy
    }
    changes = []
    
    mechanics_result = {
        "hit": True,
        "total_damage": 10
    }
    
    agent._handle_combat_update(state, mechanics_result, changes)
    
    # All enemies defeated
    assert len(state["enemies"]) == 0
    
    # Combat should end
    assert state["in_combat"] is False
    
    # Should have combat end message
    assert any("бой завершен" in change.lower() for change in changes)


@pytest.mark.asyncio
async def test_handle_combat_update_insufficient_damage():
    """Test combat update when damage is insufficient."""
    agent = WorldStateAgent()
    
    state = {
        "in_combat": True,
        "enemies": ["гоблин"]
    }
    changes = []
    
    mechanics_result = {
        "hit": True,
        "total_damage": 3  # < 7, not enough to defeat
    }
    
    agent._handle_combat_update(state, mechanics_result, changes)
    
    # Enemy should still be alive
    assert len(state["enemies"]) == 1
    assert state["in_combat"] is True
    
    # No defeat messages
    assert not any("повержен" in change for change in changes)


@pytest.mark.asyncio
async def test_handle_combat_update_missed_attack():
    """Test combat update when attack misses."""
    agent = WorldStateAgent()
    
    state = {
        "in_combat": True,
        "enemies": ["гоблин"]
    }
    changes = []
    
    mechanics_result = {
        "hit": False,
        "total_damage": 0
    }
    
    agent._handle_combat_update(state, mechanics_result, changes)
    
    # No state changes on miss
    assert len(state["enemies"]) == 1
    assert state["in_combat"] is True
    assert len(changes) == 0


@pytest.mark.asyncio
async def test_load_world_state_existing(sample_character_id):
    """Test loading existing world state from DB."""
    agent = WorldStateAgent()
    
    mock_state = {
        "in_combat": True,
        "enemies": ["дракон"],
        "location": "cave"
    }
    
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value={"state_data": mock_state})
    mock_conn.close = AsyncMock()
    
    with patch('app.agents.world_state.get_db_connection', return_value=mock_conn):
        state = await agent.load_world_state(sample_character_id)
        
        assert state["in_combat"] is True
        assert state["enemies"] == ["дракон"]
        assert state["location"] == "cave"


@pytest.mark.asyncio
async def test_load_world_state_not_found(sample_character_id):
    """Test loading world state when not found in DB."""
    agent = WorldStateAgent()
    
    mock_conn = AsyncMock()
    mock_conn.fetchrow = AsyncMock(return_value=None)
    mock_conn.close = AsyncMock()
    
    with patch('app.agents.world_state.get_db_connection', return_value=mock_conn):
        state = await agent.load_world_state(sample_character_id)
        
        # Should return default state
        assert state["in_combat"] is False
        assert state["enemies"] == []
        assert "location" in state


@pytest.mark.asyncio
async def test_load_world_state_error(sample_character_id):
    """Test loading world state when DB error occurs."""
    agent = WorldStateAgent()
    
    with patch(
        'app.agents.world_state.get_db_connection',
        side_effect=Exception("DB connection failed")
    ):
        state = await agent.load_world_state(sample_character_id)
        
        # Should return default state on error
        assert state["in_combat"] is False
        assert state["enemies"] == []


def test_default_game_state():
    """Test default game state structure."""
    agent = WorldStateAgent()
    
    state = agent._default_game_state()
    
    assert state["in_combat"] is False
    assert state["enemies"] == []
    assert "location" in state
    assert "quests" in state
    assert "flags" in state


@pytest.mark.asyncio
async def test_global_instance():
    """Test that global instance is available."""
    from app.agents.world_state import world_state_agent
    
    assert isinstance(world_state_agent, WorldStateAgent)
    assert world_state_agent.name == "WorldState"
