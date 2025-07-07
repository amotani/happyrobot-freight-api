from fastapi import APIRouter, Depends

from ..auth import verify_api_key
from ..services import verify_carrier_mc_number

# Router for carrier verification endpoints
# Handles MC number validation against FMCSA database
carriers_router = APIRouter(prefix="/verify-carrier", tags=["carriers"])


@carriers_router.get("/{mc_number}")
async def verify_carrier_get(mc_number: str, api_key: str = Depends(verify_api_key)):
    """
    Verify carrier MC number using FMCSA API (GET method for voice agents)
    Optimized response for AI voice agents to easily understand and speak
    
    In the freight industry, MC numbers are required federal identifiers
    Carriers must be ACTIVE status to legally haul freight
    Voice agents need clear, structured responses for natural conversation
    """
    result = await verify_carrier_mc_number(mc_number)
    
    # Voice-agent friendly response structure
    # Provides both structured data and natural language messages
    if result["is_eligible"]:
        voice_response = {
            "eligible": True,
            "mc_number": result["mc_number"],
            "company_name": result.get("company_name", "Unknown Company"),
            "status": result.get("operation_status", "ACTIVE"),
            # Natural language message for voice AI to speak to caller
            "voice_message": f"Carrier {result['mc_number']} - {result.get('company_name', 'Unknown Company')} is verified and eligible for loads.",
            "next_action": "search_loads"  # Guides conversation flow
        }
    else:
        voice_response = {
            "eligible": False,
            "mc_number": mc_number,
            "error": result.get("error", "Verification failed"),
            # Clear rejection message for voice AI
            "voice_message": f"Sorry, carrier MC-{mc_number} is not eligible. {result.get('error', '')}",
            "next_action": "end_call"  # Terminates conversation for ineligible carriers
        }
    
    return voice_response 