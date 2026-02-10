"""
Pydantic models for request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    num_chunks: int
    message: str
    suggested_questions: list[str] = []


class AskRequest(BaseModel):
    document_id: str
    question: str


class SourceChunk(BaseModel):
    text: str
    similarity_score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    confidence: float
    guardrail_status: str  # "grounded", "low_confidence", "no_context", "refused"


class ExtractRequest(BaseModel):
    document_id: str


class ShipmentData(BaseModel):
    shipment_id: Optional[str] = None
    shipper: Optional[str] = None
    consignee: Optional[str] = None
    pickup_datetime: Optional[str] = None
    delivery_datetime: Optional[str] = None
    equipment_type: Optional[str] = None
    mode: Optional[str] = None
    rate: Optional[str] = None
    currency: Optional[str] = None
    weight: Optional[str] = None
    carrier_name: Optional[str] = None


class ExtractResponse(BaseModel):
    document_id: str
    data: ShipmentData
    confidence: float
