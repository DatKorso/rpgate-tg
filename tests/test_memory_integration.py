"""Integration tests for episodic memory manager."""
import pytest
import json
from typing import Optional
from uuid import uuid4
from app.memory.episodic import episodic_memory_manager
from app.db.supabase import get_db_connection
from app.game.character import CharacterSheet


async def create_test_character(telegram_user_id: Optional[int] = None) -> tuple:
    """Helper function to create a test character in DB."""
    if telegram_user_id is None:
        # Generate random telegram user ID
        import random
        telegram_user_id = random.randint(1000000, 9999999999)
    
    character = CharacterSheet(
        telegram_user_id=telegram_user_id,
        name="Тестовый Герой"
    )
    
    conn = await get_db_connection()
    try:
        query = """
            INSERT INTO characters (telegram_user_id, name, character_sheet)
            VALUES ($1, $2, $3)
            RETURNING id
        """
        row = await conn.fetchrow(
            query,
            telegram_user_id,
            character.name,
            json.dumps(character.model_dump(mode='json'))  # Convert to JSON string with UUID serialization
        )
        if row:
            character_id = row['id']
            return character_id, telegram_user_id
        else:
            raise ValueError("Failed to create character")
    finally:
        await conn.close()


async def cleanup_test_character(character_id):
    """Helper function to clean up test character from DB."""
    conn = await get_db_connection()
    try:
        # Foreign key cascade will delete related memories
        await conn.execute("DELETE FROM characters WHERE id = $1", character_id)
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_create_and_retrieve_memory():
    """Test creating a memory and retrieving it."""
    # Create test character first
    character_id, _ = await create_test_character()
    
    try:
        content = "Герой вошёл в таверну 'Золотой дракон' и встретил загадочного торговца"
        
        # Create memory
        memory = await episodic_memory_manager.create_memory(
            character_id=character_id,
            content=content,
            memory_type="event",
            importance_score=7,
            entities=["таверна", "торговец", "Золотой дракон"],
            location="tavern_golden_dragon"
        )
        
        assert memory is not None
        assert memory.content == content
        assert memory.character_id == character_id
        assert memory.memory_type == "event"
        assert memory.importance_score == 7
        assert "таверна" in memory.entities
        
        # Retrieve by ID
        retrieved = await episodic_memory_manager.get_memory_by_id(memory.id)
        assert retrieved is not None
        assert retrieved.content == content
    
    finally:
        # Cleanup
        await cleanup_test_character(character_id)


@pytest.mark.asyncio
async def test_search_memories():
    """Test semantic search of memories."""
    character_id, _ = await create_test_character()
    
    try:
        # Create several memories
        memories_data = [
            "Герой сражался с гоблинами в тёмной пещере",
            "В таверне герой услышал легенду о древнем артефакте",
            "Маг показал герою заклинание огненного шара",
            "Герой нашёл карту сокровищ в старой библиотеке"
        ]
        
        for content in memories_data:
            await episodic_memory_manager.create_memory(
                character_id=character_id,
                content=content,
                memory_type="event",
                importance_score=5
            )
        
        # Search for combat-related memories
        results = await episodic_memory_manager.search_memories(
            character_id=character_id,
            query="битва с врагами",
            limit=2,
            similarity_threshold=0.3
        )
        
        assert len(results) > 0
        # Should find the goblin fight memory
        assert any("гоблин" in memory.content.lower() for memory, _ in results)
        
        # Check similarity scores
        for memory, similarity in results:
            assert 0.0 <= similarity <= 1.0
            print(f"Similarity: {similarity:.3f} - {memory.content[:50]}...")
    
    finally:
        await cleanup_test_character(character_id)


@pytest.mark.asyncio
async def test_recent_memories():
    """Test retrieving recent memories."""
    character_id, _ = await create_test_character()
    
    try:
        # Create memories
        for i in range(5):
            await episodic_memory_manager.create_memory(
                character_id=character_id,
                content=f"Событие номер {i+1}",
                memory_type="event",
                importance_score=5
            )
        
        # Get recent memories
        recent = await episodic_memory_manager.get_recent_memories(
            character_id=character_id,
            limit=3
        )
        
        assert len(recent) == 3
        # Should be in reverse chronological order
        assert "5" in recent[0].content  # Most recent
        assert "4" in recent[1].content
        assert "3" in recent[2].content
    
    finally:
        await cleanup_test_character(character_id)


@pytest.mark.asyncio
async def test_memory_filtering():
    """Test filtering memories by type and importance."""
    character_id, _ = await create_test_character()
    
    try:
        # Create different types of memories
        await episodic_memory_manager.create_memory(
            character_id=character_id,
            content="Диалог с торговцем",
            memory_type="dialogue",
            importance_score=3
        )
        
        await episodic_memory_manager.create_memory(
            character_id=character_id,
            content="Битва с драконом",
            memory_type="combat",
            importance_score=10
        )
        
        await episodic_memory_manager.create_memory(
            character_id=character_id,
            content="Нашёл секретную комнату",
            memory_type="discovery",
            importance_score=8
        )
        
        # Search with type filter
        results = await episodic_memory_manager.search_memories(
            character_id=character_id,
            query="важное событие",
            memory_types=["combat", "discovery"],
            min_importance=7,
            limit=10
        )
        
        # Should only get combat and discovery with importance >= 7
        assert len(results) > 0
        for memory, _ in results:
            assert memory.memory_type in ["combat", "discovery"]
            assert memory.importance_score >= 7
            print(f"Found: {memory.memory_type} (importance {memory.importance_score})")
    
    finally:
        await cleanup_test_character(character_id)
