#!/usr/bin/env python3
"""Script to update resource type paths in checks CSV."""
import csv
from pathlib import Path

def update_resource_type(old_type: str) -> str:
    """Update resource type path from old to new format."""
    if not old_type or not isinstance(old_type, str):
        return old_type
        
    # Handle class format: "<class 'con_mon.resources.dynamic_models.AWSIAMResource'>"
    if old_type.startswith("<class '") and old_type.endswith("'>"):
        # Extract just the class name
        class_name = old_type.split('.')[-1].rstrip("'>")
        
        # Map AWS resources to new format
        if class_name.startswith('AWS'):
            # Remove AWS prefix and map to aws module
            new_name = class_name[3:]  # Remove 'AWS' prefix
            return f"<class 'con_mon_v2.mappings.aws.{new_name}'>"
        
        # Map GitHub resources
        elif class_name == 'GithubResource':
            return f"<class 'con_mon_v2.mappings.github.{class_name}'>"
            
        # Map AdvancedFeaturesData to GithubResource
        elif class_name == 'AdvancedFeaturesData':
            return f"<class 'con_mon_v2.mappings.github.GithubResource'>"
    
    return old_type

def main():
    """Update resource type paths in checks CSV."""
    csv_path = Path("data/csv/checks.csv")
    backup_path = Path("data/csv/checks.csv.bak")
    
    # Create backup
    backup_path.write_text(csv_path.read_text())
    print(f"Created backup at {backup_path}")
    
    # Read CSV
    rows = []
    with open(csv_path, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames
        
        for row in reader:
            # Update resource type
            if 'metadata.resource_type' in row:
                row['metadata.resource_type'] = update_resource_type(row['metadata.resource_type'])
            rows.append(row)
    
    # Write updated CSV
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Updated {len(rows)} rows in {csv_path}")

if __name__ == "__main__":
    main() 