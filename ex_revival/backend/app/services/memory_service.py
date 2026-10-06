from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.memory import Memory


class MemoryService:
    @classmethod
    async def retrieve_relevant_memories(
        cls,
        db: AsyncSession,
        revival_id: str,
        current_message: str,
        top_k: int = 3,
    ) -> List[str]:
        """
        Retrieves top-k relevant memories for a revival based on importance and keyword relevance.
        Prioritizes high importance and matching keywords from current_message.
        """
        result = await db.execute(
            select(Memory).where(Memory.revival_id == revival_id)
        )
        memories = result.scalars().all()
        if not memories:
            return []

        message_words = set(current_message.lower().split())

        scored_memories = []
        for mem in memories:
            # Importance baseline score
            score = 3.0 if mem.importance == "high" else (2.0 if mem.importance == "medium" else 1.0)

            # Keyword overlap relevance
            mem_words = set(mem.memory_text.lower().split())
            overlap = len(message_words.intersection(mem_words))
            score += overlap * 2.0

            scored_memories.append((score, mem.memory_text))

        # Sort descending by score
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored_memories[:top_k]]


memory_service = MemoryService()
