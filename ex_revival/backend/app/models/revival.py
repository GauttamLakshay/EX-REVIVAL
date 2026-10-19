import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class Revival(Base):
    __tablename__ = "revivals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    name = Column(String(100), nullable=False)
    language = Column(String(50), default="en", nullable=False)
    personality = Column(Text, nullable=False, default="")
    speaking_style = Column(Text, nullable=False, default="")
    relationship_context = Column(Text, nullable=False, default="")
    reference_audio_path = Column(String(500), nullable=True)
    personality_dna = Column(Text, nullable=True)
    voice_authorized = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)


    user = relationship("User", back_populates="revivals")
    voice_assets = relationship("VoiceAsset", back_populates="revival", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="revival", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="revival", cascade="all, delete-orphan")


class VoiceAsset(Base):
    __tablename__ = "voice_assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    revival_id = Column(String(36), ForeignKey("revivals.id", ondelete="CASCADE"), index=True, nullable=False)
    storage_path = Column(String(500), nullable=False)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    sample_rate = Column(Integer, nullable=False, default=24000)
    status = Column(String(50), default="valid", nullable=False)  # valid, processing, invalid
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    revival = relationship("Revival", back_populates="voice_assets")

