from typing import Dict, List, Tuple, Optional, Union
from .models import Check
from .db import load_checks_from_database, get_checks_by_ids as db_get_checks_by_ids
load_checks_from_database()

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
        check_ids: Optional[Union[List[int], int]] = None
) -> List[Tuple[int, str, Check]]:
    """
    Get checks by their IDs filtered by connection_id.

    Args:
        connection_id: Connection ID to filter by (1=GitHub, 2=AWS)
        check_ids: List of check IDs to filter by, single check ID, None or empty list to return all checks for connection

    Returns:
        List of tuples in format (check_id, check_name, check_object)
    """
    return db_get_checks_by_ids(_loaded_checks, check_ids)
