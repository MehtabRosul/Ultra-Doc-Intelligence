"""
RAG service: retrieval-augmented generation for document Q&A.
Uses HuggingFace Inference API for LLM completion.
"""

import json
from huggingface_hub import InferenceClient

from app.config import HF_API_TOKEN, LLM_MODEL_ID, TOP_K_CHUNKS
from app.services.document_processor import search_similar_chunks
from app.services.guardrails import (
    evaluate_retrieval_quality,
    compute_final_confidence,
    build_guardrail_prompt,
)
from app.services.document_processor import get_full_text


_hf_client = InferenceClient(token=HF_API_TOKEN)


def _build_context(search_results: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block."""
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_parts.append(f"[Chunk {i}] (Relevance: {result['score']:.2f})\n{result['text']}")
    return "\n\n---\n\n".join(context_parts)


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call HuggingFace LLM via Inference API."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = _hf_client.chat_completion(
        model=LLM_MODEL_ID,
        messages=messages,
        max_tokens=1024,
        temperature=0.1,  # Low temperature for precise, deterministic answers
    )

    return response.choices[0].message.content.strip()


def _parse_llm_response(raw_response: str) -> dict:
    """Parse LLM JSON response, with fallback for non-JSON responses."""
    # Try to extract JSON from the response
    try:
        # Handle case where LLM wraps JSON in markdown code blocks
        cleaned = raw_response
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        parsed = json.loads(cleaned)
        return {
            "answer": parsed.get("answer", raw_response),
            "confidence": float(parsed.get("confidence", 0.5)),
            "source_text": parsed.get("source_text", ""),
        }
    except (json.JSONDecodeError, IndexError, ValueError):
        # Fallback: treat raw response as the answer
        return {
            "answer": raw_response,
            "confidence": 0.5,
            "source_text": "",
        }


def generate_suggested_questions(document_id: str) -> list[str]:
    """
    Generate 5 unique, short, specific questions based on the document content.
    """
    # Get first 3000 chars of text to generate questions from
    full_text = get_full_text(document_id)
    context_snippet = full_text[:3000]

    prompt = f"""DOCUMENT CONTEXT:
{context_snippet}

Generate 5 unique, short, specific questions that a user might ask about this logistics document.
The questions should be diverse (e.g., about dates, entities, reference numbers, weights).
Do not number them. Just provide 5 lines, one question per line.
"""

    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates questions for logistics documents."},
        {"role": "user", "content": prompt}
    ]

    try:
        response = _hf_client.chat_completion(
            model=LLM_MODEL_ID,
            messages=messages,
            max_tokens=256,
            temperature=0.7, 
        )
        content = response.choices[0].message.content.strip()
        questions = [q.strip("- ").strip() for q in content.split("\n") if q.strip()]
        return questions[:5]
    except Exception:
        return [
            "What is the shipment ID?",
            "Who is the shipper?",
            "What is the delivery date?",
            "What is the total weight?",
            "Who is the consignee?"
        ]



async def ask_question(document_id: str, question: str) -> dict:
    """
    Full RAG pipeline: retrieve → guardrail check → generate → score.
    Returns answer with sources, confidence, and guardrail status.
    """
    # Step 1: Retrieve similar chunks
    search_results = search_similar_chunks(document_id, question, top_k=TOP_K_CHUNKS)

    # Step 2: Evaluate retrieval quality (guardrail gate 1)
    quality = evaluate_retrieval_quality(search_results)
    if quality["status"] in ("no_context", "refused"):
        return {
            "answer": quality["message"],
            "sources": [],
            "confidence": quality["retrieval_score"],
            "guardrail_status": quality["status"],
        }

    # Step 3: Build context and prompt
    context = _build_context(search_results)
    
    # Updated prompt for strictly professional, concise answers
    system_prompt = """You are a precise, professional logistics document assistant.
Answer the user's question using ONLY the provided document context.
Your answers should be:
1. Short, specific, and very accurate.
2. NOT chatty. Do not use phrases like "Based on the document", "The text mentions", "Here is the answer".
3. Direct. Just give the answer.
4. If the answer is not in the context, say exactly: "The requested information is not available in the uploaded document."
"""
    
    user_prompt = f"""DOCUMENT CONTEXT:
{context}

QUESTION: {question}

Answer the question using ONLY the document context above."""

    # Step 4: Call LLM
    raw_response = _call_llm(system_prompt, user_prompt)

    # Step 5: Parse LLM response
    parsed = _parse_llm_response(raw_response)

    # Step 6: Compute final confidence (guardrail gate 2)
    final_confidence, guardrail_status = compute_final_confidence(
        quality["retrieval_score"], parsed["confidence"]
    )

    # Step 7: Build sources list
    sources = [
        {"text": r["text"], "similarity_score": r["score"]}
        for r in search_results[:3]  # Top 3 sources
    ]

    return {
        "answer": parsed["answer"],
        "sources": sources,
        "confidence": round(final_confidence, 3),
        "guardrail_status": guardrail_status,
    }
