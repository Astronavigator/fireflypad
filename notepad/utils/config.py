import os
from pathlib import Path

# Data Directory Configuration
# For development: use local data/ folder
# For production: use user's local share directory
if os.getenv("NOTEPAD_DEV"):
    DATA_DIR = Path(__file__).parent.parent.parent / "data"
else:
    DATA_DIR = Path.home() / ".local" / "share" / "notepad"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Database paths
NOTES_DB = DATA_DIR / "notes.db"
ABC_DB = DATA_DIR / "abc.db"

# Model Configuration
EMBEDDING_MODEL = "my-qwen-q4"
#AI_MODEL = "kimi-k2.5:cloud"
AI_MODEL = "gemma4:e2b"
EMBEDDING_DIMENSION = 1024
OLLAMA_URL = "http://localhost:11434"
# OLLAMA_URL = "http://127.0.0.1:5544"