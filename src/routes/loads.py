from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import logging

from ..models import LoadData
from ..auth import verify_api_key
from ..services import search_loads_by_criteria
from ..database import loads_db

logger = logging.getLogger(__name__)

loads_router = APIRouter(prefix="/loads", tags=["loads"])


@loads_router.get("/for-voice-agent")
async def get_loads_for_voice_agent(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    equipment_type: Optional[str] = None,
    limit: Optional[int] = 3,
    api_key: str = Depends(verify_api_key)
):
    """
    Get loads optimized for AI voice agents
    Returns easy-to-speak load summaries
    """
    loads = search_loads_by_criteria(origin, destination, equipment_type)
    
    if not loads:
        return {
            "available": False,
            "count": 0,
            "voice_message": f"Sorry, I don't have any loads available right now{' from ' + origin if origin else ''}{' to ' + destination if destination else ''}{' for ' + equipment_type if equipment_type else ''}.",
            "loads": []
        }
    
    # Limit results for voice agent (don't overwhelm the caller)
    limited_loads = loads[:limit] if limit else loads
    
    # Create voice-friendly summaries
    voice_loads = []
    for load in limited_loads:
        load_summary = {
            "load_id": load.load_id,
            "route": f"{load.origin} to {load.destination}",
            "rate": load.loadboard_rate,
            "equipment": load.equipment_type,
            "miles": load.miles,
            "voice_summary": f"Load {load.load_id}: {load.origin} to {load.destination}, {load.equipment_type}, ${load.loadboard_rate:,.0f}, {load.miles} miles"
        }
        voice_loads.append(load_summary)
    
    # Create overall voice message
    if len(loads) == 1:
        voice_message = f"I have 1 load available: {voice_loads[0]['voice_summary']}"
    elif len(loads) <= limit:
        voice_message = f"I have {len(loads)} loads available: " + "; ".join([load['voice_summary'] for load in voice_loads])
    else:
        voice_message = f"I have {len(loads)} loads total. Here are the top {limit}: " + "; ".join([load['voice_summary'] for load in voice_loads])
    
    return {
        "available": True,
        "count": len(loads),
        "showing": len(voice_loads),
        "voice_message": voice_message,
        "loads": voice_loads,
        "next_action": "carrier_response"
    }


@loads_router.get("/{load_id}/for-voice-agent")
async def get_load_details_for_voice_agent(load_id: str, api_key: str = Depends(verify_api_key)):
    """Get specific load details optimized for voice agents"""
    load = next((load for load in loads_db if load.load_id == load_id), None)
    if not load:
        return {
            "found": False,
            "voice_message": f"Sorry, I couldn't find load {load_id}.",
            "next_action": "ask_for_different_load"
        }
    
    # Voice-friendly detailed description
    details = f"Load {load.load_id}: Pickup from {load.origin} on {load.pickup_datetime.strftime('%B %d')}, "
    details += f"delivery to {load.destination} by {load.delivery_datetime.strftime('%B %d')}. "
    details += f"Equipment needed: {load.equipment_type}. "
    details += f"Rate: ${load.loadboard_rate:,.0f} for {load.miles} miles. "
    
    if load.weight:
        details += f"Weight: {load.weight:,.0f} pounds. "
    if load.commodity_type:
        details += f"Commodity: {load.commodity_type}. "
    if load.notes:
        details += f"Special notes: {load.notes}"
    
    return {
        "found": True,
        "load_id": load.load_id,
        "rate": load.loadboard_rate,
        "miles": load.miles,
        "equipment_type": load.equipment_type,
        "voice_message": details,
        "next_action": "carrier_decision",
        "full_details": load.dict()
    } 