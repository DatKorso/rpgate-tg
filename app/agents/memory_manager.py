"""Memory Manager Agent - Campaign Historian.

Агент для извлечения релевантного контекста из long-term памяти.
Использует RAG (Retrieval-Augmented Generation) для поиска похожих воспоминаний.
"""

from typing import Any, List, Optional
from uuid import UUID
import logging

from app.agents.base import BaseAgent
from app.config.models import AGENT_CONFIGS
from app.memory.episodic import episodic_memory_manager
from app.db.models import EpisodicMemoryDB

logger = logging.getLogger(__name__)


class MemoryManagerAgent(BaseAgent):
    """
    Agent для управления памятью и retrieval.
    
    Роль: "Campaign Historian"
    Задача: Извлечь релевантный контекст из long-term памяти
    
    Workflow:
    1. Vector search для семантически похожих воспоминаний
    2. Temporal retrieval для недавних событий
    3. Importance filtering для фокусировки на важных моментах
    4. Формирование текстового summary для промпта
    """
    
    def __init__(self):
        """Initialize Memory Manager Agent.
        
        Note: Этот агент НЕ использует LLM для основной работы,
        только embeddings + database queries.
        """
        # Используем базовую конфигурацию, но LLM не нужен для retrieval
        super().__init__(
            name="MemoryManager",
            model_config=AGENT_CONFIGS.MEMORY_MANAGER,
        )
        self.top_k_default = 3  # Default количество релевантных memories
        self.recent_limit_default = 5  # Default количество недавних memories
        self.min_importance_default = 3  # Только важные события (3-10)
    
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """
        Retrieve relevant memories for current action.
        
        Args:
            context: {
                "user_action": str - Действие игрока
                "character_id": UUID - ID персонажа в DB
                "session_id": UUID (optional) - ID текущей сессии
                "top_k": int (optional) - Количество релевантных memories (default 3)
                "recent_limit": int (optional) - Количество недавних memories (default 5)
                "min_importance": int (optional) - Минимальная важность (default 3)
            }
            
        Returns:
            {
                "relevant_memories": List[tuple[EpisodicMemoryDB, float]] - Семантически похожие
                "recent_memories": List[EpisodicMemoryDB] - Недавние события
                "memory_summary": str - Текстовое резюме для промпта
                "total_found": int - Общее количество найденных memories
            }
        """
        try:
            # Extract parameters
            user_action = context["user_action"]
            character_id: UUID = context["character_id"]
            session_id: Optional[UUID] = context.get("session_id")
            top_k = context.get("top_k", self.top_k_default)
            recent_limit = context.get("recent_limit", self.recent_limit_default)
            min_importance = context.get("min_importance", self.min_importance_default)
            
            self.logger.info(
                f"Memory retrieval for character {character_id}: '{user_action[:50]}...'"
            )
            
            # Step 1: Vector search для релевантных memories
            relevant_memories = await episodic_memory_manager.search_memories(
                character_id=character_id,
                query=user_action,
                limit=top_k,
                similarity_threshold=0.5,  # Минимальная similarity для включения
                min_importance=min_importance
            )
            
            self.logger.info(
                f"Found {len(relevant_memories)} relevant memories "
                f"(threshold=0.5, min_importance={min_importance})"
            )
            
            # Step 2: Get recent memories для immediate context
            recent_memories = await episodic_memory_manager.get_recent_memories(
                character_id=character_id,
                limit=recent_limit,
                session_id=session_id  # Опционально ограничить текущей сессией
            )
            
            self.logger.info(
                f"Retrieved {len(recent_memories)} recent memories "
                f"(session_id={session_id})"
            )
            
            # Step 3: Build memory summary для промпта
            memory_summary = self._build_memory_summary(
                relevant_memories,
                recent_memories
            )
            
            output = {
                "relevant_memories": relevant_memories,
                "recent_memories": recent_memories,
                "memory_summary": memory_summary,
                "total_found": len(relevant_memories) + len(recent_memories)
            }
            
            self.log_execution(context, output)
            return output
            
        except Exception as e:
            self.logger.error(f"Memory retrieval failed: {e}", exc_info=True)
            # Return empty result on error
            return {
                "relevant_memories": [],
                "recent_memories": [],
                "memory_summary": "❌ Ошибка загрузки воспоминаний.",
                "total_found": 0
            }
    
    def _build_memory_summary(
        self,
        relevant: List[tuple[EpisodicMemoryDB, float]],
        recent: List[EpisodicMemoryDB]
    ) -> str:
        """
        Build текстовое резюме памяти для промпта.
        
        Args:
            relevant: List of (memory, similarity_score) tuples
            recent: List of recent memories
            
        Returns:
            Formatted string для включения в LLM prompt
        """
        parts = []
        
        # Relevant memories section (семантически похожие)
        if relevant:
            parts.append("📚 **Релевантные воспоминания:**")
            for memory, similarity in relevant[:3]:  # Top 3
                # Importance stars (⭐ x score)
                importance_stars = "⭐" * min(memory.importance_score, 5)
                
                # Similarity percentage
                similarity_pct = int(similarity * 100)
                
                # Format: content (similarity%, importance)
                parts.append(
                    f"- {memory.content} "
                    f"({similarity_pct}% похоже, {importance_stars})"
                )
        
        # Recent memories section (временной контекст)
        if recent:
            parts.append("\n📅 **Недавние события:**")
            for memory in recent[:3]:  # Last 3
                # Location tag if available
                location_tag = f"[{memory.location}]" if memory.location else ""
                
                parts.append(f"- {memory.content} {location_tag}")
        
        # Empty state
        if not parts:
            return "💭 Нет доступных воспоминаний (новый персонаж)."
        
        return "\n".join(parts)
    
    async def extract_memory_metadata(
        self,
        user_action: str,
        assistant_response: str,
        mechanics_result: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Extract metadata for memory creation (без LLM, rule-based).
        
        Этот метод определяет:
        - memory_type (event, dialogue, discovery, combat)
        - importance_score (0-10)
        - entities (extracted keywords)
        - location (from context)
        
        Args:
            user_action: Действие игрока
            assistant_response: Ответ ассистента
            mechanics_result: Результат от Rules Arbiter
            
        Returns:
            {
                "memory_type": str,
                "importance_score": int,
                "entities": List[str],
                "suggested_location": str
            }
        """
        # Determine memory type based on mechanics
        action_type = mechanics_result.get("action_type", "other")
        
        type_mapping = {
            "attack": "combat",
            "spell": "combat",
            "skill_check": "event",
            "other": "event"
        }
        
        memory_type = type_mapping.get(action_type, "event")
        
        # Check for dialogue keywords (в user_action ИЛИ assistant_response)
        dialogue_keywords = ["говор", "спрос", "ответ", "сказал", "произнёс", "диалог", "спрашива"]
        combined_text = (user_action + " " + assistant_response).lower()
        if any(keyword in combined_text for keyword in dialogue_keywords):
            memory_type = "dialogue"
        
        # Check for discovery keywords
        discovery_keywords = ["находит", "обнаружил", "нашёл", "открыл", "узнал"]
        if any(keyword in assistant_response.lower() for keyword in discovery_keywords):
            memory_type = "discovery"
        
        # Determine importance (simple heuristic)
        importance_score = 5  # Default
        
        # Discoveries are important
        if memory_type == "discovery":
            importance_score = 7
        
        # Combat events are medium importance
        if memory_type == "combat":
            importance_score = 6
        
        # Critical events = higher importance (override combat default)
        if mechanics_result.get("success") and action_type == "attack":
            if mechanics_result.get("mechanics_result", {}).get("is_critical"):
                importance_score = 8  # Critical hit!
        
        # Extract entities (simple keyword extraction)
        # TODO: В будущем можно добавить NER (Named Entity Recognition)
        entities = self._extract_entities(user_action + " " + assistant_response)
        
        return {
            "memory_type": memory_type,
            "importance_score": importance_score,
            "entities": entities,
            "suggested_location": None  # Will be set from character state
        }
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Simple entity extraction from text (rule-based).
        
        Извлекает:
        - Существа (гоблин, волк, дракон, и т.д.)
        - Локации (пещера, таверна, лес, и т.д.)
        - Предметы (меч, зелье, амулет, и т.д.)
        
        Args:
            text: Input text
            
        Returns:
            List of extracted entities
        """
        # Common fantasy entities (можно расширить)
        entity_patterns = {
            # Creatures
            "гоблин", "орк", "дракон", "волк", "медведь", "тролль",
            "эльф", "дварф", "человек", "маг", "воин", "разбойник",
            "бармен",  # NPCs
            
            # Locations
            "пещер", "таверн", "лес", "город", "деревн", "замок",
            "храм", "подземель", "рудник", "болот",
            
            # Items
            "меч", "топор", "лук", "кинжал", "зелье", "амулет",
            "щит", "брон", "кольцо", "свиток",
        }
        
        text_lower = text.lower()
        found_entities = []
        
        for entity in entity_patterns:
            if entity in text_lower:
                found_entities.append(entity)
        
        return list(set(found_entities))  # Remove duplicates


# Global instance
memory_manager_agent = MemoryManagerAgent()
