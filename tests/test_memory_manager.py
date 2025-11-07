"""Tests for Memory Manager Agent."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from app.agents.memory_manager import MemoryManagerAgent, memory_manager_agent
from app.db.models import EpisodicMemoryDB


@pytest.fixture
def sample_character_id():
    """Sample character UUID."""
    return uuid4()


@pytest.fixture
def sample_session_id():
    """Sample session UUID."""
    return uuid4()


@pytest.fixture
def sample_relevant_memories():
    """Sample relevant memories with similarity scores."""
    character_id = uuid4()
    return [
        (
            EpisodicMemoryDB(
                id=uuid4(),
                character_id=character_id,
                session_id=uuid4(),
                content="Ты победил гоблина в пещере",
                memory_type="combat",
                importance_score=7,
                entities=["гоблин", "пещера"],
                location="goblin_cave",
                created_at=datetime.now()
            ),
            0.85  # similarity score
        ),
        (
            EpisodicMemoryDB(
                id=uuid4(),
                character_id=character_id,
                session_id=uuid4(),
                content="Ты нашёл волшебный меч в сокровищнице",
                memory_type="discovery",
                importance_score=9,
                entities=["меч", "сокровищница"],
                location="treasure_room",
                created_at=datetime.now()
            ),
            0.72  # similarity score
        ),
    ]


@pytest.fixture
def sample_recent_memories():
    """Sample recent memories."""
    character_id = uuid4()
    return [
        EpisodicMemoryDB(
            id=uuid4(),
            character_id=character_id,
            session_id=uuid4(),
            content="Ты вошёл в таверну и заказал эль",
            memory_type="event",
            importance_score=4,
            entities=["таверна", "эль"],
            location="tavern",
            created_at=datetime.now()
        ),
        EpisodicMemoryDB(
            id=uuid4(),
            character_id=character_id,
            session_id=uuid4(),
            content="Бармен рассказал тебе о пещере гоблинов",
            memory_type="dialogue",
            importance_score=6,
            entities=["бармен", "пещера", "гоблин"],
            location="tavern",
            created_at=datetime.now()
        ),
    ]


@pytest.mark.asyncio
async def test_memory_manager_initialization():
    """Test that Memory Manager initializes correctly."""
    agent = MemoryManagerAgent()
    
    assert agent.name == "MemoryManager"
    assert agent.top_k_default == 3
    assert agent.recent_limit_default == 5
    assert agent.min_importance_default == 3


@pytest.mark.asyncio
async def test_execute_retrieves_memories(
    sample_character_id,
    sample_session_id,
    sample_relevant_memories,
    sample_recent_memories
):
    """Test that execute retrieves both relevant and recent memories."""
    agent = MemoryManagerAgent()
    
    # Mock episodic memory manager methods
    with patch('app.agents.memory_manager.episodic_memory_manager') as mock_memory:
        mock_memory.search_memories = AsyncMock(return_value=sample_relevant_memories)
        mock_memory.get_recent_memories = AsyncMock(return_value=sample_recent_memories)
        
        context = {
            "user_action": "Я атакую гоблина",
            "character_id": sample_character_id,
            "session_id": sample_session_id
        }
        
        result = await agent.execute(context)
        
        # Verify calls
        mock_memory.search_memories.assert_called_once()
        mock_memory.get_recent_memories.assert_called_once()
        
        # Verify result structure
        assert "relevant_memories" in result
        assert "recent_memories" in result
        assert "memory_summary" in result
        assert "total_found" in result
        
        # Verify content
        assert len(result["relevant_memories"]) == 2
        assert len(result["recent_memories"]) == 2
        assert result["total_found"] == 4


@pytest.mark.asyncio
async def test_execute_with_custom_parameters(sample_character_id):
    """Test execute with custom top_k and limits."""
    agent = MemoryManagerAgent()
    
    with patch('app.agents.memory_manager.episodic_memory_manager') as mock_memory:
        mock_memory.search_memories = AsyncMock(return_value=[])
        mock_memory.get_recent_memories = AsyncMock(return_value=[])
        
        context = {
            "user_action": "Тестовое действие",
            "character_id": sample_character_id,
            "top_k": 5,
            "recent_limit": 10,
            "min_importance": 7
        }
        
        await agent.execute(context)
        
        # Verify custom parameters were used
        call_kwargs = mock_memory.search_memories.call_args.kwargs
        assert call_kwargs["limit"] == 5
        assert call_kwargs["min_importance"] == 7
        
        call_kwargs = mock_memory.get_recent_memories.call_args.kwargs
        assert call_kwargs["limit"] == 10


@pytest.mark.asyncio
async def test_execute_handles_errors(sample_character_id):
    """Test that execute handles errors gracefully."""
    agent = MemoryManagerAgent()
    
    with patch('app.agents.memory_manager.episodic_memory_manager') as mock_memory:
        # Simulate error
        mock_memory.search_memories = AsyncMock(side_effect=Exception("DB error"))
        
        context = {
            "user_action": "Действие",
            "character_id": sample_character_id
        }
        
        result = await agent.execute(context)
        
        # Should return empty result on error
        assert result["relevant_memories"] == []
        assert result["recent_memories"] == []
        assert result["total_found"] == 0
        assert "❌" in result["memory_summary"]


def test_build_memory_summary_with_memories(
    sample_relevant_memories,
    sample_recent_memories
):
    """Test memory summary generation with data."""
    agent = MemoryManagerAgent()
    
    summary = agent._build_memory_summary(
        sample_relevant_memories,
        sample_recent_memories
    )
    
    # Should contain both sections
    assert "📚 **Релевантные воспоминания:**" in summary
    assert "📅 **Недавние события:**" in summary
    
    # Should contain memory content
    assert "гоблин" in summary.lower()
    assert "таверну" in summary.lower()
    
    # Should contain similarity percentage
    assert "85%" in summary or "72%" in summary
    
    # Should contain importance stars
    assert "⭐" in summary


def test_build_memory_summary_empty():
    """Test memory summary with no memories."""
    agent = MemoryManagerAgent()
    
    summary = agent._build_memory_summary([], [])
    
    assert "💭 Нет доступных воспоминаний" in summary
    assert "новый персонаж" in summary


def test_build_memory_summary_only_relevant(sample_relevant_memories):
    """Test memory summary with only relevant memories."""
    agent = MemoryManagerAgent()
    
    summary = agent._build_memory_summary(sample_relevant_memories, [])
    
    assert "📚 **Релевантные воспоминания:**" in summary
    assert "📅 **Недавние события:**" not in summary


def test_build_memory_summary_only_recent(sample_recent_memories):
    """Test memory summary with only recent memories."""
    agent = MemoryManagerAgent()
    
    summary = agent._build_memory_summary([], sample_recent_memories)
    
    assert "📚 **Релевантные воспоминания:**" not in summary
    assert "📅 **Недавние события:**" in summary


@pytest.mark.asyncio
async def test_extract_memory_metadata_combat():
    """Test metadata extraction for combat action."""
    agent = MemoryManagerAgent()
    
    mechanics_result = {
        "action_type": "attack",
        "success": True,
        "mechanics_result": {
            "is_critical": True,
            "total_damage": 15
        }
    }
    
    metadata = await agent.extract_memory_metadata(
        user_action="Я атакую гоблина мечом",
        assistant_response="Твой удар критичен! Гоблин падает.",
        mechanics_result=mechanics_result
    )
    
    assert metadata["memory_type"] == "combat"
    assert metadata["importance_score"] == 8  # Critical hit = high importance
    assert "гоблин" in metadata["entities"]
    assert "меч" in metadata["entities"]


@pytest.mark.asyncio
async def test_extract_memory_metadata_dialogue():
    """Test metadata extraction for dialogue."""
    agent = MemoryManagerAgent()
    
    mechanics_result = {
        "action_type": "other",
        "success": True
    }
    
    metadata = await agent.extract_memory_metadata(
        user_action="Я спрашиваю у бармена о пещере",
        assistant_response="Бармен говорит о гоблинах в пещере",
        mechanics_result=mechanics_result
    )
    
    assert metadata["memory_type"] == "dialogue"
    assert metadata["importance_score"] >= 5


@pytest.mark.asyncio
async def test_extract_memory_metadata_discovery():
    """Test metadata extraction for discovery."""
    agent = MemoryManagerAgent()
    
    mechanics_result = {
        "action_type": "skill_check",
        "success": True
    }
    
    metadata = await agent.extract_memory_metadata(
        user_action="Я ищу тайные двери",
        assistant_response="Ты обнаружил скрытый проход в стене!",
        mechanics_result=mechanics_result
    )
    
    assert metadata["memory_type"] == "discovery"
    assert metadata["importance_score"] == 7  # Discoveries are important


def test_extract_entities():
    """Test entity extraction from text."""
    agent = MemoryManagerAgent()
    
    text = "Ты атакуешь гоблина мечом в пещере и находишь зелье"
    entities = agent._extract_entities(text)
    
    assert "гоблин" in entities
    assert "меч" in entities
    # "пещер" matches "пещере" (stemming for better matching)
    assert "пещер" in entities
    assert "зелье" in entities


def test_extract_entities_no_duplicates():
    """Test that entity extraction removes duplicates."""
    agent = MemoryManagerAgent()
    
    text = "Гоблин атакует. Ты атакуешь гоблина. Гоблин падает."
    entities = agent._extract_entities(text)
    
    # Should have only one "гоблин"
    assert entities.count("гоблин") == 1


def test_extract_entities_empty():
    """Test entity extraction from text without entities."""
    agent = MemoryManagerAgent()
    
    text = "Ты делаешь какое-то действие"
    entities = agent._extract_entities(text)
    
    # Should return empty list if no matches
    assert isinstance(entities, list)


@pytest.mark.asyncio
async def test_global_instance():
    """Test that global instance is available."""
    from app.agents.memory_manager import memory_manager_agent
    
    assert isinstance(memory_manager_agent, MemoryManagerAgent)
    assert memory_manager_agent.name == "MemoryManager"
