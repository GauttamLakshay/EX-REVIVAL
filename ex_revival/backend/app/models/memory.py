import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    revival_id = Column(String(36), ForeignKey("revivals.id", ondelete="CASCADE"), index=True, nullable=False)
    memory_text = Column(Text, nullable=False)
    importance = Column(String(20), default="medium", nullable=False)  # "high", "medium", "low"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


    revival = relationship("Revival", back_populates="memories")
