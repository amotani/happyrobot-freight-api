import logging
import uuid
from datetime import datetime
from typing import Dict, Any

from ..models import WebhookPayload, NegotiationOffer, NegotiationResult
from ..services import verify_carrier_mc_number, search_loads_by_criteria, extract_call_analytics
from ..database import negotiations_db, store_call_analytics, store_negotiation, store_call_event

logger = logging.getLogger(__name__)


async def process_webhook_event(payload: WebhookPayload) -> Dict[str, Any]:
    """
    Process webhook event from HappyRobot platform.
    
    Handles carrier engagement events including verification, load matching, 
    negotiation processing, and analytics extraction.
    """
    try:
        logger.info(f"Processing webhook event: {payload.event_type}")
        
        response_data = {
            "event_id": str(uuid.uuid4()),
            "received_at": datetime.utcnow().isoformat(),
            "event_type": payload.event_type,
            "status": "processed"
        }
        
        event_data = {
            "event_id": response_data["event_id"],
            "event_type": payload.event_type,
            "call_id": payload.call_data.get("call_id") if payload.call_data else None,
            "carrier_mc": payload.carrier_info.mc_number if payload.carrier_info else None,
            "load_id": payload.call_data.get("load_id") if payload.call_data else None,
            "received_at": response_data["received_at"]
        }
        store_call_event(event_data)
        
        if payload.event_type == "carrier_call_initiated":
            if payload.carrier_info:
                verification_result = await verify_carrier_mc_number(payload.carrier_info.mc_number)
                response_data["carrier_verification"] = verification_result
                
                if verification_result.get("is_eligible"):
                    loads = search_loads_by_criteria()
                    response_data["available_loads"] = loads[:5]
                    response_data["message"] = "Carrier verified - presenting available loads"
                else:
                    response_data["message"] = "Carrier verification failed"
        
        elif payload.event_type == "load_interest_expressed":
            response_data["message"] = "Load interest recorded - providing detailed information"
            response_data["next_action"] = "present_load_details"
        
        elif payload.event_type == "negotiation_offer":
            if payload.call_data and "offered_rate" in payload.call_data:
                load_id = payload.call_data.get("load_id")
                carrier_offer = payload.call_data["offered_rate"]
                original_rate = payload.call_data.get("original_rate")
                current_round = payload.call_data.get("counter_offer_count", 0)
                
                max_acceptable_rate = original_rate * 1.20 if original_rate else carrier_offer
                
                # Business rule: 3 rounds maximum
                if current_round >= 3:
                    response_data["negotiation_status"] = "limit_reached"
                    response_data["message"] = "Maximum negotiation rounds reached. Final offer stands."
                    response_data["next_action"] = "final_decision"
                    response_data["final_offer"] = min(carrier_offer, max_acceptable_rate)
                
                # Business rule: 20% rate cap
                elif carrier_offer > max_acceptable_rate:
                    response_data["negotiation_status"] = "over_limit"
                    response_data["message"] = f"Offer exceeds maximum acceptable rate. Best we can do is ${max_acceptable_rate:.2f}"
                    response_data["counter_offer"] = max_acceptable_rate
                    response_data["next_action"] = "counter_offer"
                
                else:
                    negotiation = NegotiationOffer(
                        load_id=load_id,
                        carrier_mc=payload.carrier_info.mc_number if payload.carrier_info else "unknown",
                        original_rate=original_rate,
                        offered_rate=carrier_offer,
                        counter_offer_count=current_round + 1,
                        max_acceptable_rate=max_acceptable_rate,
                        status="negotiating",
                        negotiation_history=[{
                            "round": current_round + 1,
                            "offered_rate": carrier_offer,
                            "timestamp": datetime.utcnow().isoformat()
                        }]
                    )
                    
                    negotiations_db.append(negotiation)
                    store_negotiation(negotiation)
                    
                    response_data["negotiation_status"] = "recorded"
                    response_data["message"] = "Counter offer recorded and within acceptable range"
                    response_data["next_action"] = "continue_negotiation"
                
                response_data["rate_analysis"] = {
                    "original_rate": original_rate,
                    "carrier_offer": carrier_offer,
                    "max_acceptable": max_acceptable_rate,
                    "current_round": current_round + 1,
                    "rounds_remaining": max(0, 3 - (current_round + 1))
                }
        
        elif payload.event_type == "agreement_reached":
            if payload.call_data:
                final_rate = payload.call_data.get("final_rate")
                load_id = payload.call_data.get("load_id")
                
                result = NegotiationResult(
                    load_id=load_id,
                    carrier_mc=payload.carrier_info.mc_number if payload.carrier_info else "unknown",
                    original_rate=payload.call_data.get("original_rate", 0),
                    final_rate=final_rate,
                    total_rounds=payload.call_data.get("total_rounds", 0),
                    outcome="agreement",
                    outcome_reason="price_agreed"
                )
                response_data["negotiation_result"] = result.dict()
            
            response_data["message"] = "Agreement reached - transferring to sales rep"
            response_data["next_action"] = "transfer_call"
        
        elif payload.event_type == "negotiation_declined":
            if payload.call_data:
                result = NegotiationResult(
                    load_id=payload.call_data.get("load_id"),
                    carrier_mc=payload.carrier_info.mc_number if payload.carrier_info else "unknown",
                    original_rate=payload.call_data.get("original_rate", 0),
                    final_rate=None,
                    total_rounds=payload.call_data.get("total_rounds", 0),
                    outcome="no_agreement",
                    outcome_reason="carrier_declined"
                )
                response_data["negotiation_result"] = result.dict()
            
            response_data["message"] = "Negotiation declined by carrier"
            response_data["next_action"] = "offer_other_loads"
        
        elif payload.event_type == "carrier_not_interested":
            response_data["message"] = "Carrier not interested in available loads"
            response_data["next_action"] = "end_call"
        
        elif payload.event_type == "transfer_failed":
            if payload.call_data:
                result = NegotiationResult(
                    load_id=payload.call_data.get("load_id"),
                    carrier_mc=payload.carrier_info.mc_number if payload.carrier_info else "unknown",
                    original_rate=payload.call_data.get("original_rate", 0),
                    final_rate=payload.call_data.get("final_rate"),
                    total_rounds=payload.call_data.get("total_rounds", 0),
                    outcome="agreement_transfer_failed",
                    outcome_reason=payload.call_data.get("transfer_failure_reason", "transfer_technical_failure")
                )
                response_data["negotiation_result"] = result.dict()
            
            response_data["message"] = "Agreement reached but transfer to sales failed - follow-up required"
            response_data["next_action"] = "schedule_callback"
            response_data["requires_follow_up"] = True
            response_data["failure_type"] = "operational"
        
        elif payload.event_type == "call_ended":
            call_data = payload.call_data or {}
            
            if payload.carrier_info:
                call_data["carrier_info"] = payload.carrier_info.dict()
            if payload.load_info:
                call_data["load_info"] = payload.load_info.dict()
            
            from ..services.analytics import extract_offer_data, classify_call_outcome, classify_carrier_sentiment
            offer_data = extract_offer_data(call_data)
            call_outcome = classify_call_outcome(call_data)
            carrier_sentiment = classify_carrier_sentiment(call_data)
            
            analytics = {
                "call_id": call_data.get("call_id", "unknown"),
                "event_id": response_data["event_id"],
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "offer_data": offer_data,
                "call_outcome": call_outcome,
                "carrier_sentiment": carrier_sentiment,
                "summary": {
                    "data_quality": offer_data["offer_summary"]["data_completeness"],
                    "outcome_confidence": call_outcome["outcome_confidence"],
                    "sentiment_confidence": carrier_sentiment["sentiment_confidence"],
                    "analysis_complete": True
                }
            }
            
            analytics_id = store_call_analytics(analytics)
            
            if call_data.get("negotiation_rounds", 0) > 0:
                try:
                    logger.info(f"Creating negotiation summary for call {call_data.get('call_id')}")
                    negotiation_summary = NegotiationOffer(
                        load_id=call_data.get("load_id", "unknown"),
                        carrier_mc=payload.carrier_info.mc_number if payload.carrier_info else "unknown",
                        original_rate=call_data.get("original_rate", 0),
                        offered_rate=call_data.get("final_rate", call_data.get("original_rate", 0)),
                        counter_offer_count=call_data.get("negotiation_rounds", 0),
                        max_acceptable_rate=call_data.get("original_rate", 0) * 1.20 if call_data.get("original_rate") else 0,
                        status="completed",
                        negotiation_history=[{
                            "round": call_data.get("negotiation_rounds", 0),
                            "final_rate": call_data.get("final_rate", 0),
                            "original_rate": call_data.get("original_rate", 0),
                            "outcome": call_data.get("outcome", "unknown"),
                            "timestamp": datetime.utcnow().isoformat()
                        }]
                    )
                    negotiation_id = store_negotiation(negotiation_summary)
                    logger.info(f"Negotiation stored with ID: {negotiation_id}")
                except Exception as e:
                    logger.error(f"Error creating/storing negotiation: {str(e)}")
            
            response_data["analytics"] = analytics
            response_data["analytics_id"] = analytics_id
            response_data["message"] = "Call analytics extracted: offer data, outcome classification, and sentiment analysis"
        
        return response_data
        
    except Exception as e:
        logger.error(f"Error processing webhook event: {str(e)}")
        raise 