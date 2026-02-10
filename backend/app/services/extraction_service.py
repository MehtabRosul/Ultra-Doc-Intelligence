"""
Structured extraction service: extracts shipment data as JSON from documents.
"""

import json
from huggingface_hub import InferenceClient

from app.config import HF_API_TOKEN, LLM_MODEL_ID
from app.services.document_processor import get_full_text


_hf_client = InferenceClient(token=HF_API_TOKEN)

EXTRACTION_PROMPT = """You are a precise logistics document data extraction AI.

Your task: Extract structured shipment data from the provided document text.

You MUST return a JSON object with EXACTLY these 11 fields:
{
  "shipment_id": "string or null",
  "shipper": "string or null",
  "consignee": "string or null",
  "pickup_datetime": "string or null",
  "delivery_datetime": "string or null",
  "equipment_type": "string or null",
  "mode": "string or null",
  "rate": "string or null",
  "currency": "string or null",
  "weight": "string or null",
  "carrier_name": "string or null"
}

STRICT RULES:
1. Extract ONLY from the provided text. NEVER invent data.
2. If a field is NOT found in the document, set it to null.
3. For dates/times, use the format found in the document.
4. For monetary values, include the number only in "rate" and the currency code in "currency".
5. Be precise — extract exact values, not paraphrased versions.
6. Return ONLY the JSON object, nothing else. No explanations, no markdown.

Also include a "confidence" field (0.0-1.0) indicating overall extraction confidence."""


async def extract_shipment_data(document_id: str) -> dict:
    """
    Extract structured shipment data from a document.
    Returns ShipmentData fields + confidence.
    """
    # Get full document text
    full_text = get_full_text(document_id)

    # Truncate if too long (stay within context window)
    max_chars = 12000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars]

    # Call LLM
    messages = [
        {"role": "system", "content": EXTRACTION_PROMPT},
        {"role": "user", "content": f"DOCUMENT TEXT:\n{full_text}\n\nExtract the structured shipment data as JSON."},
    ]

    response = _hf_client.chat_completion(
        model=LLM_MODEL_ID,
        messages=messages,
        max_tokens=1024,
        temperature=0.1,
    )

    raw = response.choices[0].message.content.strip()

    # Parse JSON
    try:
        cleaned = raw
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()

        data = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        # Fallback: all nulls
        data = {}

    # Extract confidence
    confidence = float(data.pop("confidence", 0.5))

    # Map to schema fields with null defaults
    fields = [
        "shipment_id", "shipper", "consignee",
        "pickup_datetime", "delivery_datetime",
        "equipment_type", "mode", "rate",
        "currency", "weight", "carrier_name",
    ]

    shipment_data = {}
    for field in fields:
        val = data.get(field)
        shipment_data[field] = val if val is not None else None

    return {
        "data": shipment_data,
        "confidence": round(confidence, 3),
    }
