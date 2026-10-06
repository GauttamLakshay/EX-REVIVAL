import os
import time
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.revival import Revival
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationCreateRequest,
    ConversationResponse,
    MessageResponse,
    TurnResponse,
)
from app.dependencies import get_current_user, verify_conversation_ownership
from app.services.stt_service import stt_service
from app.services.llm_service import llm_service, build_system_prompt
from app.services.memory_service import memory_service
from app.services.chatterbox_engine import chatterbox_engine
from app.services.storage_service import storage_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])
logger = logging.getLogger("ex_revival.pipeline")


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation session for a Revival."""
    # Verify Revival belongs to user
    result = await db.execute(select(Revival).where(Revival.id == payload.revival_id))
    revival = result.scalar_one_or_none()
    if not revival or revival.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revival not found")

    conversation = Conversation(
        revival_id=payload.revival_id,
        title=payload.title or f"Chat with {revival.name}",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    # Return with empty messages
    res = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation.id)
        .options(selectinload(Conversation.messages))
    )
    return res.scalar_one()


@router.get("/{id}", response_model=ConversationResponse)
async def get_conversation(
    id: str,
    conversation: Conversation = Depends(verify_conversation_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Get conversation details and full message history."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one()

    # Populate audio_url on messages
    for msg in conv.messages:
        if msg.audio_path:
            msg.audio_url = storage_service.get_audio_url(msg.audio_path)

    return conv


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    id: str,
    conversation: Conversation = Depends(verify_conversation_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and its messages."""
    await db.delete(conversation)
    await db.commit()
    return None


@router.post("/{id}/turns", response_model=TurnResponse)
async def process_conversation_turn(
    id: str,
    audio_file: Optional[UploadFile] = File(None),
    client_transcript: Optional[str] = Form(None),
    conversation: Conversation = Depends(verify_conversation_ownership),
    db: AsyncSession = Depends(get_db),
):
    """
    Core AI Voice Pipeline:
    Audio In (or Transcript) -> STT -> LLM Reasoning -> Chatterbox Voice -> Audio URL
    """
    request_id = uuid.uuid4().hex[:8]
    pipeline_start = time.time()

    # 1. Fetch Revival profile
    result = await db.execute(
        select(Revival).where(Revival.id == conversation.revival_id)
    )
    revival = result.scalar_one()

    if not revival.reference_audio_path or not os.path.exists(revival.reference_audio_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Revival does not have an active reference voice sample. Please upload reference audio first.",
        )

    # 2. STT: Transcribe user audio or use client transcript if provided
    transcript = ""
    stt_latency_ms = 0
    if client_transcript and client_transcript.strip():
        transcript = client_transcript.strip()
    elif audio_file:
        audio_bytes = await audio_file.read()
        if len(audio_bytes) > 0:
            transcript, stt_latency_ms = await stt_service.transcribe(
                audio_bytes=audio_bytes,
                filename=audio_file.filename or "speech.wav",
                language=revival.language,
            )


    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="I couldn't understand that. Try speaking again.",
        )

    # 3. Retrieve relevant long-term memories
    relevant_memories = await memory_service.retrieve_relevant_memories(
        db=db,
        revival_id=revival.id,
        current_message=transcript,
        top_k=3,
    )

    # 4. Fetch recent conversation messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(6)
    )
    recent_db_msgs = list(reversed(msg_result.scalars().all()))
    recent_history = [{"role": m.role, "text": m.text} for m in recent_db_msgs]

    # 5. Build system prompt & execute LLM
    prompt = build_system_prompt(
        name=revival.name,
        personality=revival.personality,
        speaking_style=revival.speaking_style,
        language=revival.language,
        relationship_context=revival.relationship_context,
        recent_messages=recent_history,
        memories=relevant_memories,
        transcript=transcript,
    )

    try:
        response_text, llm_latency_ms = await llm_service.generate(prompt=prompt, user_message=transcript)
    except Exception as llm_err:
        logger.error(f"[{request_id}] LLM Generation failed: {llm_err}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI reasoning temporarily failed.")

    # 6. Chatterbox Voice Synthesis
    voice_start = time.time()
    try:
        gen_audio_path = await chatterbox_engine.synthesize(
            text=response_text,
            reference_audio_path=revival.reference_audio_path,
            language=revival.language,
            emotion="warm",
        )
    except Exception as voice_err:
        logger.error(f"[{request_id}] Voice generation failed: {voice_err}")
        # Allow graceful degradation or error
        gen_audio_path = None

    voice_latency_ms = int((time.time() - voice_start) * 1000)
    total_latency_ms = int((time.time() - pipeline_start) * 1000)

    # Convert audio path to web URL
    audio_url = storage_service.get_audio_url(gen_audio_path) or ""

    # 7. Persist user and assistant messages
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        text=transcript,
    )
    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        text=response_text,
        audio_path=gen_audio_path,
        latency_ms=total_latency_ms,
    )
    db.add(user_msg)
    db.add(assistant_msg)
    await db.commit()

    # 8. Structured Logging per Section 26
    print(
        f"\n--- AI CONVERSATION TURN ---\n"
        f"Request: {request_id}\n"
        f"Conversation: {conversation.id}\n"
        f"Revival: {revival.name} ({revival.id})\n"
        f"Transcript: \"{transcript}\"\n"
        f"Response: \"{response_text}\"\n"
        f"STT: {stt_latency_ms}ms\n"
        f"LLM: {llm_latency_ms}ms\n"
        f"Voice: {voice_latency_ms}ms\n"
        f"Total: {total_latency_ms}ms\n"
        f"Status: SUCCESS\n"
        f"----------------------------\n"
    )

    turn_id = assistant_msg.id
    return TurnResponse(
        turn_id=turn_id,
        conversation_id=conversation.id,
        transcript=transcript,
        response_text=response_text,
        audio_url=audio_url,
        latency_ms=total_latency_ms,
        stt_latency_ms=stt_latency_ms,
        llm_latency_ms=llm_latency_ms,
        voice_latency_ms=voice_latency_ms,
        status="completed",
    )
