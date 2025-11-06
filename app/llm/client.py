"""
OpenRouter client для работы с Grok-4-fast через OpenAI-совместимый API.
"""
import logging
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Client для взаимодействия с LLM через OpenRouter."""
    
    def __init__(self):
        """Initialize OpenRouter client with Grok configuration."""
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        )
        self.model = settings.llm_model
        self.extra_headers = {
            "HTTP-Referer": settings.site_url,
        }
    
    async def get_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """
        Получить completion от LLM.
        
        Args:
            messages: List of message dicts с ролями 'system', 'user', 'assistant'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_headers=self.extra_headers,
            )
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"LLM API Error: {e}", exc_info=True)
            
            # Обработка rate limits от OpenRouter
            if "rate_limit" in str(e).lower() or "429" in str(e):
                return "⏳ I'm getting too many requests right now. Please wait a moment and try again."
            
            # Обработка других ошибок API
            return "❌ Sorry, I encountered an error processing your request. Please try again later."


# Singleton instance
llm_client = LLMClient()
