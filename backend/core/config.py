"""
Application configuration loaded from environment variables.

Uses python-dotenv to read a `.env` file at the backend root and exposes
all settings as module-level constants. Every downstream module imports
from here instead of reading os.environ directly.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend directory (one level up from core/)
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")

# ── Required API Keys ────────────────────────────────────────────────────────

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

# ── ChromaDB ─────────────────────────────────────────────────────────────────

CHROMA_PERSIST_DIR: str = os.getenv(
    "CHROMA_PERSIST_DIR",
    str(_backend_dir / "chroma_db"),
)

# ── Embedding Model ──────────────────────────────────────────────────────────

EMBED_MODEL_NAME: str = os.getenv("EMBED_MODEL_NAME", "all-MiniLM-L6-v2")

# ── Groq Model ───────────────────────────────────────────────────────────────

GROQ_MODEL: str = "llama-3.3-70b-versatile"

# ── Upload Limits ────────────────────────────────────────────────────────────

MAX_UPLOAD_SIZE_MB: int = 10
MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# ── Temp Directory ───────────────────────────────────────────────────────────

TEMP_DIR: Path = _backend_dir / "tmp"
TEMP_DIR.mkdir(exist_ok=True)
