from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.user import User
from app.models.revival import Revival
from app.models.memory import Memory
from app.schemas.memory import MemoryCreateRequest, MemoryResponse
from app.dependencies import get_current_user, verify_revival_ownership

router = APIRouter(tags=["Memories"])


@router.get("/revivals/{id}/memories", response_model=List[MemoryResponse])
async def list_revival_memories(
    id: str,
    revival: Revival = Depends(verify_revival_ownership),
    db: AsyncSession = Depends(get_db),
):
    """List all long-term memories associated with a Revival character."""
    result = await db.execute(
        select(Memory)
        .where(Memory.revival_id == id)
        .order_by(Memory.created_at.desc())
    )
    return result.scalars().all()


@router.post("/revivals/{id}/memories", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_revival_memory(
    id: str,
    payload: MemoryCreateRequest,
    revival: Revival = Depends(verify_revival_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Add a long-term memory for a Revival character."""
    memory = Memory(
        revival_id=id,
        memory_text=payload.memory_text,
        importance=payload.importance,
    )
    db.add(memory)
    await db.commit()
    await db.refresh(memory)
    return memory


@router.delete("/memories/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a memory item (verifying user ownership of the parent Revival)."""
    result = await db.execute(
        select(Memory)
        .join(Revival, Memory.revival_id == Revival.id)
        .where(Memory.id == id, Revival.user_id == current_user.id)
    )
    memory = result.scalar_one_or_none()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found")

    await db.delete(memory)
    await db.commit()
    return None
