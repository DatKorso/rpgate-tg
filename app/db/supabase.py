"""Supabase client for database operations."""
from typing import Optional
import logging
import asyncpg

logger = logging.getLogger(__name__)


async def get_db_connection() -> asyncpg.Connection:
    """
    Get direct PostgreSQL connection via asyncpg.
    
    Used for vector operations and complex queries that Supabase client doesn't support well.
    
    Returns:
        asyncpg.Connection instance
        
    Raises:
        Exception: If connection fails
    """
    from app.config import settings
    
    if not settings.supabase_db_url:
        raise ValueError("SUPABASE_DB_URL not configured in .env")
    
    try:
        conn = await asyncpg.connect(settings.supabase_db_url)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


class SupabaseClient:
    """Wrapper для Supabase client."""
    
    def __init__(self):
        """Initialize Supabase client (lazy loading to avoid import errors)."""
        self._client: Optional[object] = None
        self._initialized = False
    
    def _initialize(self):
        """Lazy initialization of Supabase client."""
        if self._initialized:
            return
        
        try:
            from supabase import create_client
            from app.config import settings
            
            if not settings.supabase_url or not settings.supabase_key:
                logger.warning(
                    "Supabase credentials not configured. "
                    "Database features will not be available."
                )
                self._initialized = True
                return
            
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Supabase client initialized")
            self._initialized = True
            
        except ImportError:
            logger.warning(
                "Supabase package not installed. "
                "Run 'uv add supabase' to enable database features."
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self._initialized = True
    
    @property
    def db(self):
        """Get Supabase client instance."""
        if not self._initialized:
            self._initialize()
        return self._client
    
    @property
    def is_available(self) -> bool:
        """Check if Supabase client is available."""
        if not self._initialized:
            self._initialize()
        return self._client is not None


# Global instance
supabase_client = SupabaseClient()
