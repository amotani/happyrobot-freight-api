from typing import List
from ..models import LoadData
from ..database import loads_db


def search_loads_by_criteria(origin: str = None, destination: str = None, equipment_type: str = None) -> List[LoadData]:
    """Search loads based on criteria"""
    results = loads_db.copy()
    
    if origin:
        results = [load for load in results if origin.lower() in load.origin.lower()]
    if destination:
        results = [load for load in results if destination.lower() in load.destination.lower()]
    if equipment_type:
        results = [load for load in results if equipment_type.lower() in load.equipment_type.lower()]
    
    return results 