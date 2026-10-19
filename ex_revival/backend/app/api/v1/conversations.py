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
from app.services.stt_service import get_stt_service, stt_service
from app.services.llm_service import get_llm_service, llm_service, build_system_prompt
from app.services.memory_service import memory_service
from app.services.chatterbox_engine import chatterbox_engine
from app.services.storage_service import storage_service
from app.services.cognitive_director import cognitive_director

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
            try:
                stt_svc = get_stt_service()
                transcript, stt_latency_ms = await stt_svc.transcribe(
                    audio_bytes=audio_bytes,
                    filename=audio_file.filename or "speech.wav",
                    language=revival.language,
                )
            except Exception as stt_err:
                logger.error(f"[{request_id}] STT failed: {stt_err}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="STT_FAILED",
                )

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio or transcript provided for turn.",
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

    # 5. Cognitive Director: Real-time Emotional Affect Analysis & Neural Steering
    acting_instructions, acoustic_controls = cognitive_director.analyze_turn_affect(
        transcript=transcript,
        recent_history=recent_history,
        personality_dna_raw=revival.personality_dna,
        language=revival.language or "en",
    )

    # Build system prompt with live acting directions & execute LLM
    prompt = build_system_prompt(
        name=revival.name,
        personality=revival.personality,
        speaking_style=revival.speaking_style,
        language=revival.language,
        relationship_context=revival.relationship_context,
        recent_messages=recent_history,
        memories=relevant_memories,
        transcript=transcript,
        acting_instructions=acting_instructions,
    )

    try:
        llm_svc = get_llm_service()
        response_text, llm_latency_ms = await llm_svc.generate(prompt=prompt, user_message=transcript)
    except Exception as llm_err:
        logger.error(f"[{request_id}] LLM Generation failed: {llm_err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM_FAILED",
        )

    # 6. Chatterbox Voice Synthesis with Affect Retargeting
    voice_start = time.time()
    gen_audio_path = None
    turn_status = "completed"
    try:
        # Auto-detect language: if revival is Hindi or Devanagari characters are present, route to [hi]
        synth_lang = revival.language or "en"
        if any('\u0900' <= char <= '\u097F' for char in response_text):
            synth_lang = "hi"

        gen_audio_path = await chatterbox_engine.synthesize(
            text=response_text,
            reference_audio_path=revival.reference_audio_path,
            language=synth_lang,
            emotion=acoustic_controls.get("emotion", revival.speaking_style or "warm"),
            exaggeration=acoustic_controls.get("exaggeration", 0.70),
            cfg_weight=acoustic_controls.get("cfg_weight", 0.65),
            temperature=acoustic_controls.get("temperature", 0.75),
            pitch_shift_semitones=acoustic_controls.get("pitch_shift_semitones", 0.0),
            tempo_scale=acoustic_controls.get("tempo_scale", 1.0),
        )
    except Exception as voice_err:
        logger.error(f"[{request_id}] Voice generation failed: {voice_err}")
        gen_audio_path = None
        turn_status = "VOICE_GENERATION_FAILED"

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
    try:
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
            f"Status: {turn_status}\n"
            f"----------------------------\n"
        )
    except Exception:
        try:
            safe_text = response_text.encode("ascii", errors="replace").decode("ascii")
            safe_trans = transcript.encode("ascii", errors="replace").decode("ascii")
            print(
                f"\n--- AI CONVERSATION TURN ---\n"
                f"Request: {request_id}\n"
                f"Conversation: {conversation.id}\n"
                f"Revival: {revival.name} ({revival.id})\n"
                f"Transcript: \"{safe_trans}\"\n"
                f"Response: \"{safe_text}\"\n"
                f"STT: {stt_latency_ms}ms\n"
                f"LLM: {llm_latency_ms}ms\n"
                f"Voice: {voice_latency_ms}ms\n"
                f"Total: {total_latency_ms}ms\n"
                f"Status: {turn_status}\n"
                f"----------------------------\n"
            )
        except Exception:
            pass

    turn_id = assistant_msg.id
    telem = chatterbox_engine.last_telemetry or {}
    engine_name = telem.get("engine", "chatterbox_v3_neural")
    health = await chatterbox_engine.get_health_telemetry()

    return TurnResponse(
        turn_id=turn_id,
        conversation_id=conversation.id,
        transcript=transcript,
        response_text=response_text,
        audio_url=audio_url,
        latency_ms=total_latency_ms,
        total_latency_ms=total_latency_ms,
        stt_latency_ms=stt_latency_ms,
        llm_latency_ms=llm_latency_ms,
        voice_latency_ms=voice_latency_ms,
        voice_engine=engine_name,
        voice_device=health.get("device", "cpu"),
        model_version=health.get("model_version", "v3"),
        model_loaded=health.get("model_loaded", True),
        status=turn_status,
    )


@router.post("/{id}/messages/{message_id}/retry-voice", response_model=MessageResponse)
async def retry_message_voice(
    id: str,
    message_id: str,
    conversation: Conversation = Depends(verify_conversation_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Retry voice generation for an assistant message where voice previously failed."""
    result = await db.execute(
        select(Revival).where(Revival.id == conversation.revival_id)
    )
    revival = result.scalar_one_or_none()
    if not revival or not revival.reference_audio_path or not os.path.exists(revival.reference_audio_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Revival does not have an active reference voice sample.",
        )

    msg_res = await db.execute(
        select(Message).where(Message.id == message_id, Message.conversation_id == id)
    )
    msg = msg_res.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    if msg.role != "assistant":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Can only retry voice for assistant messages")

    try:
        gen_audio_path = await chatterbox_engine.synthesize(
            text=msg.text,
            reference_audio_path=revival.reference_audio_path,
            language=revival.language,
            emotion="warm",
        )
        msg.audio_path = gen_audio_path
        await db.commit()
        await db.refresh(msg)
        msg.audio_url = storage_service.get_audio_url(gen_audio_path)
        return msg
    except Exception as e:
        logger.error(f"Retry voice generation failed: {e}")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="VOICE_GENERATION_FAILED")
