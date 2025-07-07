from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def extract_offer_data(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract actionable freight data from voice calls.
    
    Returns carrier info, load details, and negotiation data for sales team follow-up.
    """
    offer_data = {
        "extracted_at": datetime.utcnow().isoformat(),
        "carrier_info": {},
        "load_details": {},
        "negotiation_data": {},
        "offer_summary": {}
    }
    
    if "carrier_info" in call_data:
        carrier = call_data["carrier_info"]
        offer_data["carrier_info"] = {
            "mc_number": carrier.get("mc_number"),
            "company_name": carrier.get("company_name"),
            "is_verified": carrier.get("is_verified", False),
            "equipment_type": carrier.get("preferred_equipment")
        }
    
    if "load_info" in call_data:
        load = call_data["load_info"]
        offer_data["load_details"] = {
            "load_id": load.get("load_id"),
            "origin": load.get("origin"),
            "destination": load.get("destination"),
            "original_rate": load.get("original_rate"),
            "miles": load.get("miles"),
            "equipment_type": load.get("equipment_type"),
            "pickup_date": load.get("pickup_date"),
            "delivery_date": load.get("delivery_date")
        }
    
    if "negotiation_data" in call_data or call_data.get("negotiation_occurred"):
        original_rate = call_data.get("original_rate")
        final_rate = call_data.get("final_rate") or call_data.get("carrier_offered_rate")
        
        offer_data["negotiation_data"] = {
            "original_rate": original_rate,
            "carrier_offered_rate": call_data.get("carrier_offered_rate"),
            "final_agreed_rate": final_rate,
            "negotiation_rounds": call_data.get("negotiation_rounds", 0),
            "rate_difference": (final_rate - original_rate) if (final_rate and original_rate) else None,
            "negotiation_success": call_data.get("agreement_reached", False)
        }
    
    offer_data["offer_summary"] = {
        "has_carrier_info": bool(offer_data["carrier_info"]),
        "has_load_details": bool(offer_data["load_details"]),
        "negotiation_occurred": bool(offer_data["negotiation_data"]),
        "deal_closed": call_data.get("agreement_reached", False),
        "data_completeness": calculate_data_completeness(offer_data)
    }
    
    return offer_data


def classify_call_outcome(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify call outcomes for actionable sales decisions and follow-up strategies.
    """
    outcome_data = {
        "classified_at": datetime.utcnow().isoformat(),
        "primary_outcome": "unknown",
        "secondary_outcomes": [],
        "outcome_confidence": 0.0,
        "outcome_details": {}
    }
    
    outcome = call_data.get("outcome", "").lower()
    
    if outcome in ["load_assigned", "deal_closed"]:
        outcome_data["primary_outcome"] = "success"
        outcome_data["outcome_confidence"] = 0.95
        outcome_data["outcome_details"]["deal_closed"] = True
        outcome_data["outcome_details"]["transfer_completed"] = True
        
    elif outcome in ["agreement_reached"]:
        outcome_data["primary_outcome"] = "success"
        outcome_data["outcome_confidence"] = 0.90
        outcome_data["outcome_details"]["deal_closed"] = True
        outcome_data["outcome_details"]["awaiting_transfer"] = True
        
    elif outcome in ["agreement_transfer_failed"]:
        outcome_data["primary_outcome"] = "partial_success"
        outcome_data["outcome_confidence"] = 0.85
        outcome_data["outcome_details"]["deal_closed"] = True
        outcome_data["outcome_details"]["transfer_failed"] = True
        outcome_data["outcome_details"]["follow_up_required"] = True
        outcome_data["outcome_details"]["failure_type"] = "operational"
        
    elif outcome in ["transferred_to_sales", "sales_transfer"]:
        outcome_data["primary_outcome"] = "success"
        outcome_data["outcome_confidence"] = 0.95
        outcome_data["outcome_details"]["deal_closed"] = True
        outcome_data["outcome_details"]["transfer_completed"] = True
        outcome_data["outcome_details"]["transfer_reason"] = "qualified_lead"
        
    elif outcome in ["carrier_not_eligible", "verification_failed"]:
        outcome_data["primary_outcome"] = "unqualified"
        outcome_data["outcome_confidence"] = 0.85
        outcome_data["outcome_details"]["rejection_reason"] = "carrier_verification_failed"
        
    elif outcome in ["carrier_not_interested", "no_interest"]:
        outcome_data["primary_outcome"] = "no_interest"
        outcome_data["outcome_confidence"] = 0.80
        outcome_data["outcome_details"]["rejection_reason"] = "carrier_declined_loads"
        
    elif call_data.get("duration", call_data.get("call_duration_seconds", 0)) < 30:
        outcome_data["primary_outcome"] = "abandoned"
        outcome_data["outcome_confidence"] = 0.80
        outcome_data["outcome_details"]["abandonment_reason"] = "short_call"
        
    elif call_data.get("carrier_interested") and not call_data.get("agreement_reached"):
        outcome_data["primary_outcome"] = "qualified_lead"
        outcome_data["outcome_confidence"] = 0.75
        outcome_data["outcome_details"]["follow_up_needed"] = True
        
    else:
        conversation_analysis = analyze_conversation_patterns(call_data)
        outcome_data["primary_outcome"] = conversation_analysis["likely_outcome"]
        outcome_data["outcome_confidence"] = conversation_analysis["confidence"]
        outcome_data["outcome_details"] = conversation_analysis["details"]
    
    if call_data.get("negotiation_occurred"):
        outcome_data["secondary_outcomes"].append("negotiation_attempted")
    
    if call_data.get("multiple_loads_discussed"):
        outcome_data["secondary_outcomes"].append("multiple_opportunities")
    
    return outcome_data


def classify_carrier_sentiment(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze carrier sentiment for sales team insights and follow-up prioritization.
    """
    sentiment_data = {
        "classified_at": datetime.utcnow().isoformat(),
        "overall_sentiment": "neutral",
        "sentiment_confidence": 0.0,
        "sentiment_progression": [],
        "sentiment_details": {}
    }
    
    sentiment_scores = {
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "interested": 0,
        "frustrated": 0
    }
    
    if call_data.get("carrier_sentiment"):
        explicit_sentiment = call_data["carrier_sentiment"].lower()
        if explicit_sentiment in ["positive", "interested", "enthusiastic"]:
            sentiment_scores["positive"] += 0.8
            sentiment_scores["interested"] += 0.7
        elif explicit_sentiment in ["negative", "frustrated", "angry"]:
            sentiment_scores["negative"] += 0.8
            sentiment_scores["frustrated"] += 0.7
        elif explicit_sentiment in ["neutral", "indifferent"]:
            sentiment_scores["neutral"] += 0.6
    
    if call_data.get("questions_asked", 0) > 3:
        sentiment_scores["interested"] += 0.6
    
    if call_data.get("negotiation_occurred"):
        sentiment_scores["interested"] += 0.5
    
    if call_data.get("call_duration_seconds", 0) < 60:
        sentiment_scores["negative"] += 0.4
    
    if call_data.get("carrier_requested_callback"):
        sentiment_scores["positive"] += 0.6
    
    if call_data.get("call_duration_seconds", 0) > 300:
        engagement_score = min(0.5, (call_data["call_duration_seconds"] - 300) / 600)
        sentiment_scores["interested"] += engagement_score
    
    negotiation_rounds = call_data.get("negotiation_rounds", 0)
    if negotiation_rounds > 0:
        sentiment_scores["interested"] += min(0.4, negotiation_rounds * 0.1)
        if negotiation_rounds > 5:
            sentiment_scores["frustrated"] += 0.3
    
    max_sentiment = max(sentiment_scores.items(), key=lambda x: x[1])
    sentiment_data["overall_sentiment"] = max_sentiment[0]
    sentiment_data["sentiment_confidence"] = min(1.0, max_sentiment[1])
    
    sentiment_data["sentiment_details"] = {
        "engagement_level": "high" if sentiment_scores["interested"] > 0.5 else "medium" if sentiment_scores["interested"] > 0.2 else "low",
        "negotiation_willingness": call_data.get("negotiation_occurred", False),
        "frustration_indicators": sentiment_scores["frustrated"] > 0.3,
        "positive_indicators": sentiment_scores["positive"],
        "negative_indicators": sentiment_scores["negative"]
    }
    
    if "call_events" in call_data:
        sentiment_data["sentiment_progression"] = track_sentiment_progression(call_data["call_events"])
    
    return sentiment_data


def analyze_conversation_patterns(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze conversation patterns to determine likely outcome"""
    patterns = {
        "likely_outcome": "unknown",
        "confidence": 0.5,
        "details": {}
    }
    
    if call_data.get("questions_asked", 0) > 3:
        patterns["likely_outcome"] = "qualified_lead"
        patterns["confidence"] = 0.7
    elif call_data.get("call_duration_seconds", 0) > 180:
        patterns["likely_outcome"] = "interested"
        patterns["confidence"] = 0.6
    else:
        patterns["likely_outcome"] = "failed"
        patterns["confidence"] = 0.6
    
    return patterns


def track_sentiment_progression(call_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Track sentiment changes throughout the call"""
    progression = []
    
    for event in call_events:
        event_sentiment = "neutral"
        
        if event.get("type") in ["question_asked", "interest_expressed"]:
            event_sentiment = "positive"
        elif event.get("type") in ["objection_raised", "call_terminated_early"]:
            event_sentiment = "negative"
        
        progression.append({
            "timestamp": event.get("timestamp"),
            "event_type": event.get("type"),
            "sentiment": event_sentiment
        })
    
    return progression


def calculate_data_completeness(offer_data: Dict[str, Any]) -> float:
    """Calculate data completeness score for quality assessment"""
    total_fields = 9
    completed_fields = 0
    
    if offer_data["carrier_info"].get("mc_number"):
        completed_fields += 1
    if offer_data["carrier_info"].get("company_name"):
        completed_fields += 1
    if offer_data["carrier_info"].get("is_verified"):
        completed_fields += 1
    
    if offer_data["load_details"].get("load_id"):
        completed_fields += 1
    if offer_data["load_details"].get("origin"):
        completed_fields += 1
    if offer_data["load_details"].get("destination"):
        completed_fields += 1
    
    if offer_data["negotiation_data"].get("original_rate"):
        completed_fields += 1
    if offer_data["negotiation_data"].get("final_agreed_rate"):
        completed_fields += 1
    if offer_data["negotiation_data"].get("negotiation_rounds"):
        completed_fields += 1
    
    return completed_fields / total_fields


def extract_call_analytics(call_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main analytics function that combines all analysis types.
    
    Returns comprehensive analytics extraction for the call including
    offer data, outcome classification, and carrier sentiment.
    """
    analytics = {
        "analysis_timestamp": datetime.utcnow().isoformat(),
        "call_id": call_data.get("call_id", "unknown"),
        "analysis_version": "1.0"
    }
    
    try:
        analytics["offer_data"] = extract_offer_data(call_data)
        analytics["call_outcome"] = classify_call_outcome(call_data)
        analytics["carrier_sentiment"] = classify_carrier_sentiment(call_data)
        
        analytics["summary"] = {
            "data_quality": analytics["offer_data"]["offer_summary"]["data_completeness"],
            "outcome_confidence": analytics["call_outcome"]["outcome_confidence"],
            "sentiment_confidence": analytics["carrier_sentiment"]["sentiment_confidence"],
            "analysis_complete": True
        }
        
        logger.info(f"Analytics extracted for call {analytics['call_id']}")
        
    except Exception as e:
        logger.error(f"Error extracting analytics: {str(e)}")
        analytics["error"] = str(e)
        analytics["analysis_complete"] = False
    
    return analytics 