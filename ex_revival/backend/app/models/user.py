import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime

from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    auth_provider = Column(String(50), default="email", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


    revivals = relationship("Revival", back_populates="user", cascade="all, delete-orphan")
