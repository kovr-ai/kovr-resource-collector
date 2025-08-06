"""
Checks module for resource validation and evaluation.
"""
from typing import Dict, List, Tuple, Optional, Union
from .models import Check
from .db import load_checks_from_database, get_checks_by_ids as db_get_checks_by_ids

# Global storage for loaded checks
_loaded_checks: Dict[str, Check] = {}

def load_checks_from_database_init():
    """
    Load checks from database and make them accessible as module attributes.
    """
    global _loaded_checks
    
    try:
        # Load checks from database
        _loaded_checks = load_checks_from_database()
        
        # Make checks accessible as module attributes
        for check_name, check in _loaded_checks.items():
            globals()[check_name] = check
        
        print(f"✅ Loaded {len(_loaded_checks)} checks from database")
        
    except Exception as e:
        print(f"❌ Error loading checks from database: {e}")

def get_loaded_checks() -> Dict[str, Check]:
    """Get all loaded checks."""
    return _loaded_checks.copy()

def get_checks_by_ids(
    connection_id: int,
    check_ids: Optional[Union[List[int], int]] = None
) -> List[Tuple[int, str, Check]]:
    """
    Get checks by their IDs filtered by connection_id, or return all checks for connection if check_ids is None or empty list.
    
    Args:
        connection_id: Connection ID to filter by (1=GitHub, 2=AWS)
        check_ids: List of check IDs to filter by, single check ID, None or empty list to return all checks for connection
        
    Returns:
        List of tuples in format (check_id, check_name, check_object)
        
    Examples:
        # Get all GitHub checks (connection_id=1)
        all_github_checks = get_checks_by_ids(1)
        all_github_checks = get_checks_by_ids(1, None)
        all_github_checks = get_checks_by_ids(1, [])
        
        # Get specific GitHub checks by ID
        selected_github_checks = get_checks_by_ids(1, [1001, 1002])
        
        # Get single AWS check by ID
        single_aws_check = get_checks_by_ids(2, 2001)
    """
    # Convert single int to list for consistent processing
    if isinstance(check_ids, int):
        check_ids = [check_ids]
    
    # Treat empty list the same as None (return all checks)
    if check_ids is not None and len(check_ids) == 0:
        check_ids = None
    
    # Use database function to get filtered checks
    filtered_checks = db_get_checks_by_ids(connection_id, _loaded_checks, check_ids)
    
    # Convert to the expected tuple format
    result = [(check.id, check.name, check) for check in filtered_checks]
    
    # Sort by check ID for consistent ordering
    result.sort(key=lambda x: x[0])
    
    # Log what checks were returned
    connection_name = "GitHub" if connection_id == 1 else "AWS" if connection_id == 2 else f"Connection {connection_id}"
    if check_ids is None:
        print(f"📋 Retrieved all {len(result)} available {connection_name} checks")
    else:
        found_ids = [check_id for check_id, _, _ in result]
        missing_ids = [cid for cid in check_ids if cid not in found_ids]
        
        print(f"📋 Retrieved {len(result)} {connection_name} checks matching IDs: {found_ids}")
        if missing_ids:
            print(f"⚠️ Warning: {connection_name} check IDs not found: {missing_ids}")
    
    return result

# Auto-load checks when module is imported
load_checks_from_database_init()

# Export main functions and loaded checks
__all__ = [
    'get_checks_by_ids',
    'get_loaded_checks', 
    'load_checks_from_database_init'
] 
