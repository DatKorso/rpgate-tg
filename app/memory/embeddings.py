"""Embeddings service для vector search using OpenRouter."""
from typing import List
import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """Service для генерации embeddings через OpenRouter API."""
    
    def __init__(self):
        self.model = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding для одного текста.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
            
        Raises:
            Exception: If API call fails
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.site_url,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": text,
                        "dimensions": self.dimension,  # Request specific dimension
                    },
                    timeout=30.0,
                )
                
                response.raise_for_status()
                data = response.json()
                
                embedding = data["data"][0]["embedding"]
                
                # Ensure all elements are float (API sometimes returns int for zeros)
                embedding = [float(x) for x in embedding]
                
                # Validate dimension (should match exactly now with qwen-4b)
                if len(embedding) != self.dimension:
                    logger.warning(
                        f"Expected {self.dimension} dimensions, got {len(embedding)}. "
                        f"This may indicate model configuration mismatch."
                    )
                    # Only adjust if really necessary
                    if abs(len(embedding) - self.dimension) > 10:
                        embedding = self._adjust_dimension(embedding)
                
                logger.debug(f"Generated embedding for text: {text[:50]}...")
                
                return embedding
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings для multiple texts (batch).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            Exception: If API call fails
        """
        if not texts:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": settings.site_url,
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "input": texts,
                        "dimensions": self.dimension,  # Request specific dimension
                    },
                    timeout=60.0,
                )
                
                response.raise_for_status()
                data = response.json()
                
                embeddings = [item["embedding"] for item in data["data"]]
                
                # Ensure all elements are float (API sometimes returns int for zeros)
                embeddings = [[float(x) for x in emb] for emb in embeddings]
                
                # Validate dimensions (should match now)
                for i, embedding in enumerate(embeddings):
                    if len(embedding) != self.dimension:
                        logger.warning(
                            f"Embedding {i}: expected {self.dimension} dimensions, "
                            f"got {len(embedding)}."
                        )
                        # Only adjust if significantly different
                        if abs(len(embedding) - self.dimension) > 10:
                            embeddings[i] = self._adjust_dimension(embedding)
                
                logger.info(f"Generated {len(embeddings)} embeddings in batch")
                
                return embeddings
                
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise
    
    def _adjust_dimension(self, embedding: List[float]) -> List[float]:
        """
        Adjust embedding dimension to match configured dimension.
        
        Truncates if too long, pads with zeros if too short.
        """
        current_dim = len(embedding)
        target_dim = self.dimension
        
        if current_dim > target_dim:
            # Truncate
            return [float(x) for x in embedding[:target_dim]]
        elif current_dim < target_dim:
            # Pad with zeros
            return [float(x) for x in embedding] + [0.0] * (target_dim - current_dim)
        else:
            return [float(x) for x in embedding]


# Global instance
embeddings_service = EmbeddingsService()
