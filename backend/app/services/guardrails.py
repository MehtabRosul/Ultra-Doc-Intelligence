"""
Guardrails module: confidence scoring and hallucination prevention.
"""

from app.config import CONFIDENCE_THRESHOLD, SIMILARITY_THRESHOLD


def evaluate_retrieval_quality(search_results: list[dict]) -> dict:
    """
    Evaluate the quality of retrieved chunks.
    Returns quality metrics and guardrail decision.
    """
    if not search_results:
        return {
            "retrieval_score": 0.0,
            "best_score": 0.0,
            "status": "no_context",
            "message": "No relevant content found in the document.",
        }

    scores = [r["score"] for r in search_results]
    best_score = max(scores)
    avg_score = sum(scores) / len(scores)

    # Gate 1: Check if best chunk meets minimum similarity
    if best_score < SIMILARITY_THRESHOLD:
        return {
            "retrieval_score": avg_score,
            "best_score": best_score,
            "status": "refused",
            "message": "Not enough relevant context found in the document to answer this question.",
        }

    return {
        "retrieval_score": avg_score,
        "best_score": best_score,
        "status": "pass",
        "message": "",
    }


def compute_final_confidence(
    retrieval_score: float, llm_confidence: float
) -> tuple[float, str]:
    """
    Compute combined confidence score and determine guardrail status.
    Returns (confidence, status).
    """
    # Weighted combination: 50% retrieval similarity + 50% LLM self-assessment
    combined = 0.5 * retrieval_score + 0.5 * llm_confidence

    # Clamp to [0, 1]
    combined = max(0.0, min(1.0, combined))

    if combined >= CONFIDENCE_THRESHOLD:
        return combined, "grounded"
    else:
        return combined, "low_confidence"


def build_guardrail_prompt() -> str:
    """
    Returns system-level instructions that enforce strict grounding.
    """
    return """You are a precise document analysis AI assistant for logistics documents.

STRICT RULES YOU MUST FOLLOW:
1. Answer ONLY from the provided document context. NEVER use external knowledge.
2. If the answer is NOT in the context, respond EXACTLY with: "Not found in document."
3. Keep answers SHORT, SPECIFIC, and DIRECT. No verbose explanations.
4. Do NOT repeat the question in your answer.
5. Do NOT make up or hallucinate any information.
6. Do NOT provide uncertain or speculative answers.
7. If multiple values exist, list them concisely.
8. Always cite the source text that supports your answer.

RESPONSE FORMAT:
You must respond in this exact JSON format:
{
  "answer": "Your concise, accurate answer here",
  "confidence": 0.85,
  "source_text": "The exact text from the context that supports your answer"
}

The "confidence" field must be a float between 0.0 and 1.0 indicating how confident you are that your answer is correct and fully supported by the context.
- 0.9-1.0: Answer is explicitly and clearly stated in context
- 0.7-0.89: Answer is strongly supported by context
- 0.5-0.69: Answer is partially supported, some inference needed
- Below 0.5: Answer is weakly supported, use "Not found in document." instead"""
