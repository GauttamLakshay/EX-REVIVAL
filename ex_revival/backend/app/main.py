import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.session import init_db
from app.api.v1.auth import router as auth_router
from app.api.v1.revivals import router as revivals_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.memories import router as memories_router
from app.api.v1.health import router as health_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    # Ensure storage paths exist
    storage_dir = settings.get_storage_path()
    (storage_dir / "reference_audio").mkdir(parents=True, exist_ok=True)
    (storage_dir / "generated_audio").mkdir(parents=True, exist_ok=True)
    (storage_dir / "temp").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="EX REVIVAL — AI Voice Orchestration Platform",
    description="Voice-first conversational backend orchestrating STT, LLM reasoning, and Chatterbox Multilingual V3 voice synthesis.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) for Flutter Web, Desktop, Mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount audio storage static file directory
storage_dir = settings.get_storage_path()
storage_dir.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

# Include v1 API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(revivals_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")
app.include_router(memories_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "product": "EX REVIVAL",
        "tagline": "AI Voice-Recreated Conversational Experience",
        "docs": "/docs",
        "api_v1": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
