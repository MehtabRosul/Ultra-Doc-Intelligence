"""
Configuration settings for Ultra Doc-Intelligence backend.
Loads environment variables and defines application constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# --- HuggingFace ---
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")
LLM_MODEL_ID = "Qwen/Qwen2.5-72B-Instruct"
EMBEDDING_MODEL_ID = "BAAI/bge-small-en-v1.5"

# --- Encryption ---
AES_SECRET_KEY = os.getenv("AES_SECRET_KEY", "")

# --- RAG Thresholds ---
CONFIDENCE_THRESHOLD = 0.45
SIMILARITY_THRESHOLD = 0.35
TOP_K_CHUNKS = 5

# --- Chunking ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# --- Allowed file types ---
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
