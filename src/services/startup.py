import logging
from datetime import datetime, timedelta
from typing import List
from ..models import LoadData
from ..database import init_database

logger = logging.getLogger(__name__)


async def initialize_sample_data():
    """
    Initialize application with sample data and database setup.
    
    In production, this would connect to a real database and load actual freight data.
    For development/demo, we use sample carriers and loads representative of the freight industry.
    """
    
    logger.info("Initializing database...")
    init_database()
    
    sample_loads = [
        LoadData(
            load_id="LOAD001",
            origin="Chicago, IL",
            destination="Atlanta, GA",
            pickup_datetime=datetime.utcnow() + timedelta(days=1, hours=9),
            delivery_datetime=datetime.utcnow() + timedelta(days=3, hours=17),
            equipment_type="Dry Van",
            loadboard_rate=2500.0,
            notes="Standard delivery, dock high",
            weight=25000.0,
            commodity_type="Electronics",
            num_of_pieces=1,
            miles=717.0,
            dimensions="53ft trailer"
        ),
        LoadData(
            load_id="LOAD002", 
            origin="Los Angeles, CA",
            destination="Denver, CO",
            pickup_datetime=datetime.utcnow() + timedelta(days=2, hours=8),
            delivery_datetime=datetime.utcnow() + timedelta(days=4, hours=16),
            equipment_type="Reefer",
            loadboard_rate=3200.0,
            notes="Temperature controlled: 34-38°F",
            weight=32000.0,
            commodity_type="Fresh Produce",
            num_of_pieces=1,
            miles=1015.0,
            dimensions="53ft reefer trailer"
        )
    ]
    
    from ..database import loads_db
    loads_db.clear()
    loads_db.extend(sample_loads)
    
    logger.info(f"Initialized with {len(sample_loads)} sample loads and 2 sample carriers")
    
    return {
        "loads_initialized": len(sample_loads),
        "sample_carriers": 2,
        "database_initialized": True,
        "status": "ready"
    } 