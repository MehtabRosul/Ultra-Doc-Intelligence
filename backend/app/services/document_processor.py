"""
Document processing service: parsing, chunking, embedding, and FAISS storage.
Handles PDF, DOCX, and TXT files.
"""

import uuid
import pickle
from pathlib import Path
from io import BytesIO

import numpy as np
import faiss
from huggingface_hub import InferenceClient
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import (
    HF_API_TOKEN,
    EMBEDDING_MODEL_ID,
    UPLOAD_DIR,
    VECTOR_STORE_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    ALLOWED_EXTENSIONS,
)
from app.services.crypto_service import encrypt_file, decrypt_file


# Initialize HF client for embeddings
_hf_client = InferenceClient(token=HF_API_TOKEN)

# In-memory store for document metadata
_document_store: dict[str, dict] = {}


def _parse_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes."""
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _parse_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes."""
    from docx import Document
    doc = Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _parse_txt(file_bytes: bytes) -> str:
    """Extract text from TXT bytes."""
    return file_bytes.decode("utf-8", errors="replace")


def _parse_document(file_bytes: bytes, filename: str) -> str:
    """Route to the correct parser based on file extension."""
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return _parse_pdf(file_bytes)
    elif ext == ".docx":
        return _parse_docx(file_bytes)
    elif ext == ".txt":
        return _parse_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks using recursive character splitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(text)
    return chunks


def _get_embeddings(texts: list[str]) -> np.ndarray:
    """Get embeddings from HuggingFace Inference API."""
    embeddings = _hf_client.feature_extraction(
        texts,
        model=EMBEDDING_MODEL_ID,
    )
    arr = np.array(embeddings, dtype=np.float32)
    # Normalize for cosine similarity
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1
    arr = arr / norms
    return arr


def _save_faiss_index(document_id: str, index: faiss.IndexFlatIP, chunks: list[str]):
    """Persist FAISS index and chunks to disk."""
    doc_dir = VECTOR_STORE_DIR / document_id
    doc_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(doc_dir / "index.faiss"))
    with open(doc_dir / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)


def _load_faiss_index(document_id: str) -> tuple[faiss.IndexFlatIP, list[str]]:
    """Load FAISS index and chunks from disk."""
    doc_dir = VECTOR_STORE_DIR / document_id
    index = faiss.read_index(str(doc_dir / "index.faiss"))
    with open(doc_dir / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


async def process_document(file_bytes: bytes, filename: str) -> dict:
    """
    Full pipeline: parse → chunk → embed → store.
    Returns document metadata.
    """
    # Validate file type
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type '{ext}' not supported. Allowed: {ALLOWED_EXTENSIONS}")

    # Generate unique document ID
    document_id = str(uuid.uuid4())

    # Encrypt and save the original file
    encrypted = encrypt_file(file_bytes)
    encrypted_path = UPLOAD_DIR / f"{document_id}{ext}.enc"
    encrypted_path.write_bytes(encrypted)

    # Parse the document
    text = _parse_document(file_bytes, filename)
    if not text.strip():
        raise ValueError("No text could be extracted from the document.")

    # Chunk the text
    chunks = _chunk_text(text)

    # Generate embeddings
    embeddings = _get_embeddings(chunks)

    # Build FAISS index (Inner Product = cosine similarity for normalized vectors)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # Save to disk
    _save_faiss_index(document_id, index, chunks)

    # Store metadata in memory
    _document_store[document_id] = {
        "filename": filename,
        "num_chunks": len(chunks),
        "full_text": text,
        "file_ext": ext,
    }

    return {
        "document_id": document_id,
        "filename": filename,
        "num_chunks": len(chunks),
    }


def search_similar_chunks(
    document_id: str, query: str, top_k: int = 5
) -> list[dict]:
    """
    Search for chunks most similar to the query.
    Returns list of {text, score} dicts sorted by relevance.
    """
    # Get query embedding
    query_embedding = _get_embeddings([query])

    # Load index
    index, chunks = _load_faiss_index(document_id)

    # Search
    k = min(top_k, len(chunks))
    scores, indices = index.search(query_embedding, k)

    results = []
    for i in range(k):
        idx = indices[0][i]
        score = float(scores[0][i])
        if idx >= 0:
            results.append({
                "text": chunks[idx],
                "score": score,
            })

    return results


def get_full_text(document_id: str) -> str:
    """Get the full extracted text for a document."""
    if document_id in _document_store:
        return _document_store[document_id]["full_text"]
    # Fallback: reconstruct from chunks
    _, chunks = _load_faiss_index(document_id)
    return "\n".join(chunks)


def document_exists(document_id: str) -> bool:
    """Check if a document has been processed."""
    doc_dir = VECTOR_STORE_DIR / document_id
    return doc_dir.exists() and (doc_dir / "index.faiss").exists()
