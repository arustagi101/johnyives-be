import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.utils.dspy_config import configure_from_env as _configure_dspy

# Basic logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("ych")

app = FastAPI(title="YCH UX Auditor & Generator", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

# Log app startup
logger.info("FastAPI app initialized: %s v%s", app.title, app.version)

# Configure DSPy
_configure_dspy()
