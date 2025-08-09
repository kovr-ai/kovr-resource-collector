#!/usr/bin/env python3
"""Script to export checks from database to CSV."""
import csv
import json
from datetime import datetime
from typing import Any, Dict

from con_mon.utils.db import get_db

def datetime_handler(obj: Any) -> str:
    """Handle datetime serialization to string."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionaries for CSV format."""
    items: list = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, json.dumps(v, default=datetime_handler) if isinstance(v, (dict, list, datetime)) else v))
    return dict(items)

def get_raw_checks_from_db():
    """Get all checks from database without validation."""
    query = """
    SELECT *
    FROM checks
    WHERE NOT is_deleted
    ORDER BY id;
    """
    db = get_db()
    return db.execute_query(query)

def main():
    """Main function to export checks to CSV."""
    # Get all checks from database
    checks = get_raw_checks_from_db()
    
    if not checks:
        print("No checks found in database")
        return
    
    # Prepare output file path
    output_path = "data/csv/checks.csv"
    
    # Convert rows to dictionaries
    check_dicts = [dict(check) for check in checks]
    
    # Flatten the first check to get all possible fields for headers
    flattened_check = flatten_dict(check_dicts[0])
    fieldnames = list(flattened_check.keys())
    
    # Write to CSV
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for check in check_dicts:
            flattened = flatten_dict(check)
            writer.writerow(flattened)
    
    print(f"Exported {len(checks)} checks to {output_path}")

if __name__ == "__main__":
    main() 