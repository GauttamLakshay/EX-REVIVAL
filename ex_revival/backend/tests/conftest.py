import os
import sys
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add app and root to path
backend_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

from app.db.session import Base, get_db
# Import all models to ensure Base.metadata contains all tables
from app.models.user import User
from app.models.revival import Revival, VoiceAsset
from app.models.conversation import Conversation, Message
from app.models.memory import Memory

from app.main import app
from app.services.chatterbox_engine import chatterbox_engine

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_ex_revival.db"

test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def mock_voice_synthesis_in_unit_tests(monkeypatch):
    """
    Prevents unit tests from hanging on long CPU neural Chatterbox synthesis calls.
    Returns a valid dummy audio path for test assertions.
    """
    test_audio_path = str(backend_path / "test_synth.wav")
    if not os.path.exists(test_audio_path):
        with open(test_audio_path, "wb") as f:
            f.write(b"RIFF" + b"\x00" * 1000)

    async def _mock_synthesize(text, reference_audio_path, language="en", emotion="warm"):
        return test_audio_path

    monkeypatch.setattr(chatterbox_engine, "synthesize", _mock_synthesize)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
