"""
Data storage for HappyRobot API
Uses SQLite for persistent analytics storage and in-memory for sample data
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from ..models import LoadData, NegotiationOffer

logger = logging.getLogger(__name__)

# Database setup
DB_PATH = Path("happyrobot_analytics.db")

def init_database():
    """Initialize SQLite database with required tables"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Analytics table for storing call analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_id TEXT,
                event_id TEXT,
                analysis_timestamp TEXT,
                offer_data TEXT,  -- JSON string
                call_outcome TEXT,  -- JSON string
                carrier_sentiment TEXT,  -- JSON string
                summary_metrics TEXT,  -- JSON string
                created_at TEXT
            )
        """)
        
        # Negotiations table for detailed negotiation tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS negotiations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                load_id TEXT,
                carrier_mc TEXT,
                original_rate REAL,
                offered_rate REAL,
                max_acceptable_rate REAL,
                counter_offer_count INTEGER,
                status TEXT,
                negotiation_history TEXT,  -- JSON string
                created_at TEXT,
                updated_at TEXT
            )
        """)
        
        # Call events table for tracking all webhook events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT,
                event_type TEXT,
                call_id TEXT,
                carrier_mc TEXT,
                load_id TEXT,
                event_data TEXT,  -- JSON string
                received_at TEXT
            )
        """)
        
        conn.commit()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise
    finally:
        conn.close()

def store_call_analytics(analytics_data: Dict[str, Any]) -> Optional[int]:
    """Store call analytics data in SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO call_analytics (
                call_id, event_id, analysis_timestamp, offer_data, 
                call_outcome, carrier_sentiment, summary_metrics, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            analytics_data.get("call_id"),
            analytics_data.get("event_id"),
            analytics_data.get("analysis_timestamp"),
            json.dumps(analytics_data.get("offer_data", {})),
            json.dumps(analytics_data.get("call_outcome", {})),
            json.dumps(analytics_data.get("carrier_sentiment", {})),
            json.dumps(analytics_data.get("summary", {})),
            datetime.utcnow().isoformat()
        ))
        
        analytics_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Analytics stored with ID: {analytics_id}")
        return analytics_id
        
    except Exception as e:
        logger.error(f"Error storing analytics: {str(e)}")
        return None
    finally:
        conn.close()

def store_negotiation(negotiation: NegotiationOffer) -> Optional[int]:
    """Store negotiation data in SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO negotiations (
                load_id, carrier_mc, original_rate, offered_rate, 
                max_acceptable_rate, counter_offer_count, status, 
                negotiation_history, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            negotiation.load_id,
            negotiation.carrier_mc,
            negotiation.original_rate,
            negotiation.offered_rate,
            negotiation.max_acceptable_rate,
            negotiation.counter_offer_count,
            negotiation.status,
            json.dumps(negotiation.negotiation_history),
            negotiation.created_at.isoformat() if negotiation.created_at else datetime.utcnow().isoformat(),
            negotiation.updated_at.isoformat() if negotiation.updated_at else datetime.utcnow().isoformat()
        ))
        
        negotiation_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Negotiation stored with ID: {negotiation_id}")
        return negotiation_id
        
    except Exception as e:
        logger.error(f"Error storing negotiation: {str(e)}")
        return None
    finally:
        conn.close()

def store_call_event(event_data: Dict[str, Any]) -> Optional[int]:
    """Store webhook event data for tracking"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO call_events (
                event_id, event_type, call_id, carrier_mc, 
                load_id, event_data, received_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event_data.get("event_id"),
            event_data.get("event_type"),
            event_data.get("call_id"),
            event_data.get("carrier_mc"),
            event_data.get("load_id"),
            json.dumps(event_data),
            event_data.get("received_at")
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        return event_id
        
    except Exception as e:
        logger.error(f"Error storing call event: {str(e)}")
        return None
    finally:
        conn.close()

def get_analytics_summary() -> Dict[str, Any]:
    """Get analytics summary for dashboard"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM call_analytics")
        total_calls = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM call_analytics 
            WHERE json_extract(call_outcome, '$.primary_outcome') IN ('success', 'transferred', 'partial_success')
        """)
        successful_calls = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM call_analytics 
            WHERE json_extract(call_outcome, '$.primary_outcome') = 'success'
        """)
        complete_success_calls = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM call_analytics 
            WHERE json_extract(call_outcome, '$.primary_outcome') = 'partial_success'
        """)
        partial_success_calls = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT json_extract(carrier_sentiment, '$.overall_sentiment') as sentiment, 
                   COUNT(*) as count
            FROM call_analytics 
            GROUP BY sentiment
        """)
        sentiment_data = cursor.fetchall()
        
        cursor.execute("""
            SELECT AVG(counter_offer_count) as avg_rounds,
                   AVG(offered_rate - original_rate) as avg_rate_difference
            FROM negotiations
        """)
        negotiation_stats = cursor.fetchone()
        
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        return {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "success_rate": round(success_rate, 2),
            "success_breakdown": {
                "complete_success": complete_success_calls,
                "partial_success": partial_success_calls,
                "ai_success_rate": round(success_rate, 2),  # AI performed successfully
                "operational_success_rate": round((complete_success_calls / total_calls * 100) if total_calls > 0 else 0, 2)  # Full process success
            },
            "sentiment_breakdown": dict(sentiment_data),
            "negotiation_metrics": {
                "average_rounds": negotiation_stats[0] or 0,
                "average_rate_difference": negotiation_stats[1] or 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {str(e)}")
        return {}
    finally:
        conn.close()

loads_db: List[LoadData] = []
negotiations_db: List[NegotiationOffer] = []

SAMPLE_CARRIERS = {
    "123456": {
        "mc_number": "123456",
        "company_name": "Test Carrier LLC",
        "status": "ACTIVE",
        "equipment_types": ["Dry Van", "Reefer"],
        "service_areas": ["Midwest", "Southeast"],
        "created_at": datetime.utcnow().isoformat()
    },
    "999999": {
        "mc_number": "999999",
        "company_name": "Inactive Carrier Inc",
        "status": "INACTIVE",
        "equipment_types": ["Dry Van"],
        "service_areas": ["Northeast"],
        "created_at": datetime.utcnow().isoformat()
    }
}

SAMPLE_LOADS = [
    {
        "load_id": "LOAD001",
        "shipper": "ABC Manufacturing",
        "origin": "Chicago, IL",
        "destination": "Atlanta, GA",
        "pickup_date": (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "delivery_date": (datetime.utcnow() + timedelta(days=3)).strftime("%Y-%m-%d"),
        "equipment_type": "Dry Van",
        "weight": 35000,
        "rate": 2500.0,
        "miles": 717.0,
        "rate_per_mile": 3.49,
        "commodity": "Electronics",
        "special_requirements": [],
        "status": "available",
        "created_at": datetime.utcnow().isoformat()
    },
    {
        "load_id": "LOAD002",
        "shipper": "Fresh Foods Corp",
        "origin": "Los Angeles, CA",
        "destination": "Denver, CO",
        "pickup_date": (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "delivery_date": (datetime.utcnow() + timedelta(days=4)).strftime("%Y-%m-%d"),
        "equipment_type": "Reefer",
        "weight": 40000,
        "rate": 3200.0,
        "miles": 1015.0,
        "rate_per_mile": 3.15,
        "commodity": "Frozen Foods",
        "special_requirements": ["Temperature Control: -10°F to 0°F"],
        "status": "available",
        "created_at": datetime.utcnow().isoformat()
    }
]

def get_available_loads(equipment_type: str = None, origin_state: str = None) -> List[Dict[str, Any]]:
    """
    Get available freight loads with optional filtering.
    
    Args:
        equipment_type: Filter by trailer type (Dry Van, Reefer, Flatbed)
        origin_state: Filter by pickup state abbreviation
    """
    loads = [load for load in SAMPLE_LOADS if load["status"] == "available"]
    
    if equipment_type:
        loads = [load for load in loads if load["equipment_type"] == equipment_type]
    
    if origin_state:
        loads = [load for load in loads if origin_state.upper() in load["origin"]]
    
    return loads