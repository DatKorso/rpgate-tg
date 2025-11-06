"""Base agent class for all AI agents."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging
from app.config.models import ModelConfig

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(
        self, 
        name: str,
        model_config: ModelConfig,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        """
        Initialize agent.
        
        Args:
            name: Agent name for logging
            model_config: ModelConfig with default settings
            model: Override model (if None, use config)
            temperature: Override temperature (if None, use config)
        """
        self.name = name
        self.model_config = model_config
        self.model = model or model_config.model
        self.temperature = temperature if temperature is not None else model_config.temperature
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Execute agent logic.
        
        Args:
            context: Input context (varies by agent)
            
        Returns:
            Agent output (varies by agent)
        """
        pass
    
    def log_execution(self, context: dict, output: dict):
        """Log agent execution for debugging."""
        self.logger.info(
            f"Agent '{self.name}' executed",
            extra={
                "agent": self.name,
                "context_keys": list(context.keys()),
                "output_keys": list(output.keys()),
            }
        )
