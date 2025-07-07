from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from .carrier import CarrierInfo
from .load import LoadData


class WebhookPayload(BaseModel):
    """Model for webhook payload from HappyRobot"""
    event_type: str
    carrier_info: Optional[CarrierInfo] = None
    load_info: Optional[LoadData] = None
    call_data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow) 