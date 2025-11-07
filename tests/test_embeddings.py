"""Tests for embeddings service."""
import pytest
from app.memory.embeddings import embeddings_service


@pytest.mark.asyncio
async def test_embed_text():
    """Test single text embedding generation."""
    text = "Герой атакует гоблина мечом"
    
    embedding = await embeddings_service.embed_text(text)
    
    assert embedding is not None
    assert len(embedding) == 2560  # qwen/qwen3-embedding-4b dimension
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_embed_batch():
    """Test batch embedding generation."""
    texts = [
        "Герой исследует темную пещеру",
        "Гоблин атакует внезапно",
        "Маг читает древний свиток"
    ]
    
    embeddings = await embeddings_service.embed_batch(texts)
    
    assert len(embeddings) == len(texts)
    for embedding in embeddings:
        assert len(embedding) == 2560  # qwen/qwen3-embedding-4b dimension
        assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_dimension_adjustment():
    """Test dimension adjustment helper."""
    # Test truncation
    long_vector = [float(i) for i in range(3000)]
    adjusted = embeddings_service._adjust_dimension(long_vector)
    assert len(adjusted) == 2560
    assert adjusted[0] == 0.0
    assert adjusted[2559] == 2559.0
    
    # Test padding
    short_vector = [float(i) for i in range(100)]
    adjusted = embeddings_service._adjust_dimension(short_vector)
    assert len(adjusted) == 2560
    assert adjusted[0] == 0.0
    assert adjusted[99] == 99.0
    assert adjusted[100] == 0.0  # Padded with zeros
    
    # Test exact match
    exact_vector = [float(i) for i in range(2560)]
    adjusted = embeddings_service._adjust_dimension(exact_vector)
    assert len(adjusted) == 2560
    assert adjusted == exact_vector
