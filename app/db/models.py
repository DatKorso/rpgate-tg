"""Database models for Sprint 3."""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class CharacterDB(BaseModel):
    """Character model для database."""
    id: UUID
    telegram_user_id: int
    name: str
    character_sheet: dict  # JSON with CharacterSheet data
    created_at: datetime
    updated_at: datetime
    last_session_at: Optional[datetime] = None


class GameSessionDB(BaseModel):
    """Game session model."""
    id: UUID
    character_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    summary: Optional[str] = None
    turns_count: int = 0
    total_damage_dealt: int = 0
    total_damage_taken: int = 0


class EpisodicMemoryDB(BaseModel):
    """Episodic memory model."""
    id: UUID
    character_id: UUID
    session_id: Optional[UUID] = None
    content: str
    embedding: Optional[List[float]] = None  # Vector embedding
    memory_type: str = "event"
    importance_score: int = Field(default=5, ge=0, le=10)
    entities: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    created_at: datetime


class SemanticMemoryDB(BaseModel):
    """Semantic memory (world lore) model."""
    id: UUID
    content: str
    category: str  # 'rule', 'lore', 'location', 'npc', 'item'
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class WorldStateDB(BaseModel):
    """World state model."""
    id: UUID
    character_id: UUID
    state_data: dict
    version: int = 1
    updated_at: datetime
