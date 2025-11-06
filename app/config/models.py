"""Model configuration for all agents."""

from typing import Literal
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for LLM model."""
    
    model: str = Field(..., description="Model identifier (e.g., 'x-ai/grok-4-fast', 'mistralai/mistral-nemo')")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=500, ge=1, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling")
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    response_format: Literal["text", "json"] = Field(default="text", description="Response format")


class AgentModelConfigs:
    """Model configurations for all agents."""
    
    # Rules Arbiter: Fast, cheap, deterministic
    RULES_ARBITER = ModelConfig(
        model="x-ai/grok-4-fast",
        temperature=0.1,
        max_tokens=300,
        response_format="text"
    )
    
    # Rules Arbiter Intent Analysis: Structured output
    RULES_ARBITER_INTENT = ModelConfig(
        model="x-ai/grok-4-fast",
        temperature=0.1,
        max_tokens=250,
        response_format="json"  # For structured JSON output
    )
    
    # Narrative Director: Creative, high quality
    NARRATIVE_DIRECTOR = ModelConfig(
        model="x-ai/grok-4-fast",  # Quality model for narrative
        temperature=0.8,
        max_tokens=400,
        frequency_penalty=0.3,
        presence_penalty=0.2,
        response_format="text"
    )
    
    # Response Synthesizer: Balanced quality
    RESPONSE_SYNTHESIZER = ModelConfig(
        model="x-ai/grok-4-fast",
        temperature=0.3,
        max_tokens=600,
        response_format="text"
    )
    
    # Memory Manager (Sprint 3): Fast retrieval
    MEMORY_MANAGER = ModelConfig(
        model="x-ai/grok-4-fast",
        temperature=0.2,
        max_tokens=400,
        response_format="text"
    )
    
    # World State Agent (Sprint 3): Structured tracking
    WORLD_STATE = ModelConfig(
        model="x-ai/grok-4-fast",
        temperature=0.1,
        max_tokens=300,
        response_format="json"
    )


# Export for convenience
AGENT_CONFIGS = AgentModelConfigs()
