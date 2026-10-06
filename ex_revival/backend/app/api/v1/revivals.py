import os
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.user import User
from app.models.revival import Revival, VoiceAsset
from app.schemas.revival import (
    RevivalCreateRequest,
    RevivalUpdateRequest,
    RevivalResponse,
    VoiceValidateResponse,
    VoicePreviewRequest,
    VoicePreviewResponse,
)
from app.dependencies import get_current_user, verify_revival_ownership
from app.services.audio_service import audio_service, AudioValidationError
from app.services.storage_service import storage_service
from app.services.chatterbox_engine import chatterbox_engine

router = APIRouter(prefix="/revivals", tags=["Revivals"])


@router.post("", response_model=RevivalResponse, status_code=status.HTTP_201_CREATED)
async def create_revival(
    payload: RevivalCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new Revival character profile."""
    revival = Revival(
        user_id=current_user.id,
        name=payload.name,
        language=payload.language,
        personality=payload.personality,
        speaking_style=payload.speaking_style,
        relationship_context=payload.relationship_context,
        voice_authorized=payload.voice_authorized,
    )
    db.add(revival)
    await db.commit()
    await db.refresh(revival)

    # Reload with relationships
    result = await db.execute(
        select(Revival).where(Revival.id == revival.id).options(selectinload(Revival.voice_assets))
    )
    return result.scalar_one()


@router.get("", response_model=List[RevivalResponse])
async def list_revivals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all Revival characters owned by the current user."""
    result = await db.execute(
        select(Revival)
        .where(Revival.user_id == current_user.id)
        .order_by(Revival.created_at.desc())
        .options(selectinload(Revival.voice_assets))
    )
    return result.scalars().all()


@router.get("/{id}", response_model=RevivalResponse)
async def get_revival(
    id: str,
    revival: Revival = Depends(verify_revival_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Get single Revival character by ID."""
    result = await db.execute(
        select(Revival).where(Revival.id == id).options(selectinload(Revival.voice_assets))
    )
    return result.scalar_one()


@router.patch("/{id}", response_model=RevivalResponse)
async def update_revival(
    id: str,
    payload: RevivalUpdateRequest,
    revival: Revival = Depends(verify_revival_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Update Revival attributes."""
    if payload.name is not None:
        revival.name = payload.name
    if payload.language is not None:
        revival.language = payload.language
    if payload.personality is not None:
        revival.personality = payload.personality
    if payload.speaking_style is not None:
        revival.speaking_style = payload.speaking_style
    if payload.relationship_context is not None:
        revival.relationship_context = payload.relationship_context
    if payload.voice_authorized is not None:
        revival.voice_authorized = payload.voice_authorized

    await db.commit()
    await db.refresh(revival)

    result = await db.execute(
        select(Revival).where(Revival.id == id).options(selectinload(Revival.voice_assets))
    )
    return result.scalar_one()


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_revival(
    id: str,
    revival: Revival = Depends(verify_revival_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Delete a Revival and clean up associated audio assets."""
    # Delete reference audio file
    if revival.reference_audio_path:
        await storage_service.delete_file(revival.reference_audio_path)

    await db.delete(revival)
    await db.commit()
    return None


@router.post("/{id}/voice", response_model=RevivalResponse)
async def upload_reference_voice(
    id: str,
    audio_file: UploadFile = File(...),
    voice_authorized: bool = Form(True),
    revival: Revival = Depends(verify_revival_ownership),
    db: AsyncSession = Depends(get_db),
):
    """Upload, validate, normalize, and attach reference voice audio to Revival."""
    content = await audio_file.read()
    try:
        normalized_bytes, metadata = audio_service.validate_and_normalize(content, audio_file.filename)
    except AudioValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Save to storage
    stored_path = await storage_service.save_reference_audio(normalized_bytes, ".wav")

    # Update Revival
    revival.reference_audio_path = stored_path
    revival.voice_authorized = voice_authorized

    # Create VoiceAsset record
    voice_asset = VoiceAsset(
        revival_id=revival.id,
        storage_path=stored_path,
        duration_seconds=metadata["duration_seconds"],
        sample_rate=metadata["sample_rate"],
        status="valid",
    )
    db.add(voice_asset)
    await db.commit()
    await db.refresh(revival)

    result = await db.execute(
        select(Revival).where(Revival.id == id).options(selectinload(Revival.voice_assets))
    )
    return result.scalar_one()


@router.post("/{id}/voice/validate", response_model=VoiceValidateResponse)
async def validate_voice_sample(
    id: str,
    audio_file: UploadFile = File(...),
    revival: Revival = Depends(verify_revival_ownership),
):
    """Pre-validation check of audio sample without persisting."""
    content = await audio_file.read()
    try:
        _, metadata = audio_service.validate_and_normalize(content, audio_file.filename)
        return VoiceValidateResponse(
            is_valid=True,
            duration_seconds=metadata["duration_seconds"],
            sample_rate=metadata["sample_rate"],
            channels=metadata["channels"],
            has_silence=metadata["has_silence"],
            has_clipping=metadata["has_clipping"],
            message="Audio quality verified and acceptable for voice synthesis.",
        )
    except AudioValidationError as e:
        return VoiceValidateResponse(
            is_valid=False,
            duration_seconds=0.0,
            sample_rate=0,
            channels=0,
            has_silence=True,
            has_clipping=False,
            message=str(e),
        )


@router.post("/{id}/voice/preview", response_model=VoicePreviewResponse)
async def preview_voice_sample(
    id: str,
    payload: VoicePreviewRequest,
    revival: Revival = Depends(verify_revival_ownership),
):
    """Synthesizes preview sample phrase using the reference voice."""
    if not revival.reference_audio_path or not os.path.exists(revival.reference_audio_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Revival does not have an active reference voice sample yet. Please record or upload one first.",
        )

    start_time = time.time()
    try:
        gen_path = await chatterbox_engine.synthesize(
            text=payload.phrase,
            reference_audio_path=revival.reference_audio_path,
            language=revival.language,
            emotion="warm",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Preview synthesis failed: {str(e)}")

    latency_ms = int((time.time() - start_time) * 1000)
    audio_url = storage_service.get_audio_url(gen_path)

    return VoicePreviewResponse(
        audio_url=audio_url or "",
        phrase=payload.phrase,
        duration_seconds=2.0,
        latency_ms=latency_ms,
    )
