from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class NegotiationOffer(BaseModel):
    """Model for carrier negotiation offers"""
    load_id: str
    carrier_mc: str
    original_rate: float  # Original posted rate
    offered_rate: float   # Carrier's current offer
    counter_offer_count: int = 0
    max_acceptable_rate: Optional[float] = None  # 20% above original
    status: str = "pending"  # pending, accepted, rejected, negotiating, limit_reached
    negotiation_history: List[dict] = Field(default_factory=list)  # Track all offers
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class NegotiationResult(BaseModel):
    """Model for final negotiation outcome"""
    load_id: str
    carrier_mc: str
    original_rate: float
    final_rate: Optional[float] = None
    total_rounds: int = 0
    outcome: str  # "agreement", "no_agreement", "over_limit", "max_rounds"
    outcome_reason: Optional[str] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow) 