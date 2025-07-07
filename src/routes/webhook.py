from fastapi import APIRouter, HTTPException, Depends
from uuid import uuid4
from datetime import datetime
import logging
from typing import Dict, Any

from ..models import WebhookPayload
from ..auth import verify_api_key
from ..handlers import process_webhook_event

logger = logging.getLogger(__name__)

# Router for webhook endpoints
# Handles incoming events from HappyRobot voice AI platform
webhook_router = APIRouter(prefix="/webhook", tags=["webhooks"])


@webhook_router.post("/carrier-engagement")
async def handle_carrier_engagement(
    payload: WebhookPayload,
    api_key: str = Depends(verify_api_key)
):
    """
    Handle carrier engagement webhook events from HappyRobot platform.
    
    Processes call events and extracts analytics including offer data, 
    outcome classification, and sentiment analysis.
    """
    # Generate unique event ID for tracking and correlation
    event_id = str(uuid4())
    
    logger.info(f"Received webhook event: {payload.event_type}")
    
    analytics_result = await process_webhook_event(payload)
    
    return {
        "event_id": event_id,
        "received_at": datetime.utcnow().isoformat(),
        "event_type": payload.event_type,
        "status": "processed",
        "message": "Call analytics extracted: offer data, outcome classification, and sentiment analysis",
        "analytics": analytics_result  # Complete analytics breakdown
    }

@webhook_router.get("/health")
async def webhook_health():
    """Health check for webhook service"""
    return {"status": "healthy", "service": "webhook"} 