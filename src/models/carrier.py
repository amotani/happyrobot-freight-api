from pydantic import BaseModel
from typing import Optional


class CarrierInfo(BaseModel):
    """Model for carrier information"""
    mc_number: str
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None 