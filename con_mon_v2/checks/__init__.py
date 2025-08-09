from typing import Dict, List, Tuple, Optional, Union
from .models import Check
from .db_loader import (
    get_db_check_loader,
    get_csv_check_loader,
    # Legacy functions for backward compatibility
    load_checks_from_database,
    load_checks_from_csv,
    get_checks_by_ids as db_get_checks_by_ids
)

# Global storage for loaded checks
_loaded_checks: Dict[str, Check] = {}


def load_checks_init(use_csv: bool = True):
    """
    Load checks using the modern loader pattern and make them accessible as module attributes.
    
    Args:
        use_csv: If True, use CSV loader; if False, use database loader
    """
    global _loaded_checks

    try:
        # Use modern loader pattern
        if use_csv:
            loader = get_csv_check_loader()
        else:
            loader = get_db_check_loader()
        
        # Load checks using the loader
        _loaded_checks = loader.load_checks()

        # Make checks accessible as module attributes
        for check_name, check in _loaded_checks.items():
            globals()[check_name] = check

        print(f"✅ Loaded {len(_loaded_checks)} checks using {loader.name}")

    except Exception as e:
        print(f"❌ Error loading checks: {e}")


def get_loaded_checks() -> Dict[str, Check]:
    """Get all loaded checks."""
    return _loaded_checks.copy()


def get_checks_by_ids(
        check_ids: Optional[Union[List[int], int]] = None
) -> List[Tuple[int, str, Check]]:
    """
    Get checks by their IDs using the modern loader pattern.

    Args:
        check_ids: List of check IDs to filter by, single check ID, None or empty list to return all checks

    Returns:
        List of tuples in format (check_id, check_name, check_object)
    """
    # Use the default loader (CSV for now, but can be configured)
    loader = get_csv_check_loader()
    return loader.get_checks_by_ids(_loaded_checks, check_ids)


# Initialize checks on module import
load_checks_init()
