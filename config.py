import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OLLAMA_URL = f"http://127.0.0.1:{int(os.getenv('PAPERPILOT_OLLAMA_PORT', '11434'))}"
DEFAULT_MODEL = "qwen2.5:3b"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_REVISION = "c9745ed1d9f207416be6d2e6f8de32d1f16199bf"
EMBEDDING_DIR = Path(os.getenv("HF_HOME", Path.home() / ".cache" / "huggingface")) / (
    "paperpilot-MiniLM-" + EMBEDDING_REVISION
)
MAX_UPLOAD_MB = int(os.getenv("PAPERPILOT_MAX_UPLOAD_MB", "20"))
MAX_PAGES = 150
MAX_TEXT_CHARS = 1_000_000
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
MAX_REQUEST_CHARS = 1200
CONTEXT_CHARS = 8500
NUM_CTX = 8192
REQUEST_TIMEOUT = 240
