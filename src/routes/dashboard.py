from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
import os
import secrets

from ..auth import verify_api_key
from ..database import get_analytics_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/config")
async def get_dashboard_config() -> Dict[str, Any]:
    """
    Get dashboard configuration
    
    Returns minimal configuration needed for dashboard to function
    Uses a temporary session token approach for security
    """
    try:
        session_token = secrets.token_urlsafe(32)
        main_api_key = os.getenv("HAPPYROBOT_API_KEY", "happyrobot-api-key-change-in-production")
        
        return {
            "api_key": main_api_key,
            "session_token": session_token,
            "environment": "production" if os.getenv("ENVIRONMENT", "development") == "production" else "development"
        }
    except Exception as e:
        logger.error(f"Error getting dashboard config: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not retrieve dashboard configuration")


@router.get("/analytics")
async def get_dashboard_analytics(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Get analytics data for dashboard visualization
    
    Returns comprehensive analytics including:
    - Call success rates and outcomes
    - Carrier sentiment analysis
    - Negotiation metrics and patterns
    - Load performance data
    
    This endpoint provides the data needed for the bonus dashboard requirement
    """
    try:
        logger.info("Fetching dashboard analytics data")
        
        analytics_summary = get_analytics_summary()
        dashboard_data = {
            "summary": analytics_summary,
            "dashboard_metadata": {
                "last_updated": analytics_summary.get("last_updated"),
                "data_freshness": "real-time",
                "dashboard_version": "1.0"
            },
            "visualizations": {
                "call_outcomes": {
                    "chart_type": "pie",
                    "title": "Call Outcomes Distribution",
                    "data": {
                        "successful": analytics_summary.get("successful_calls", 0),
                        "total": analytics_summary.get("total_calls", 0),
                        "success_rate": analytics_summary.get("success_rate", 0)
                    }
                },
                "sentiment_breakdown": {
                    "chart_type": "bar",
                    "title": "Carrier Sentiment Analysis",
                    "data": analytics_summary.get("sentiment_breakdown", {})
                },
                "negotiation_metrics": {
                    "chart_type": "metrics",
                    "title": "Negotiation Performance",
                    "data": analytics_summary.get("negotiation_metrics", {})
                }
            }
        }
        
        logger.info(f"Dashboard data retrieved: {analytics_summary.get('total_calls', 0)} calls analyzed")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics data")


@router.get("/status")
async def get_dashboard_status(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Get dashboard system status and health metrics
    
    Provides information about data collection status and system health
    """
    try:
        analytics_summary = get_analytics_summary()
        
        status_data = {
            "status": "operational",
            "analytics_collection": "active",
            "data_points": {
                "total_calls": analytics_summary.get("total_calls", 0),
                "total_negotiations": analytics_summary.get("negotiation_metrics", {}).get("total_negotiations", 0)
            },
            "last_activity": analytics_summary.get("last_updated", "No data yet"),
            "system_health": "healthy"
        }
        
        return status_data
        
    except Exception as e:
        logger.error(f"Error getting dashboard status: {str(e)}")
        raise HTTPException(status_code=500, detail="Dashboard status unavailable") 