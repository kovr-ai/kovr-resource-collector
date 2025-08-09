"""Tests for loading checks from CSV."""
import os
from con_mon_v2.checks.db import load_checks_from_csv

def test_load_checks_from_csv():
    """Test loading checks from CSV file."""
    # Ensure CSV file exists
    assert os.path.exists("data/csv/checks.csv"), "CSV file not found"
    
    # Load checks from CSV
    loaded_checks = load_checks_from_csv()
    
    # Verify checks were loaded
    assert loaded_checks, "No checks were loaded from CSV"
    
    # Get a sample check
    sample_check = next(iter(loaded_checks.values()))
    
    # Verify check structure
    assert sample_check.id is not None, "Check ID is missing"
    assert sample_check.name, "Check name is missing"
    assert sample_check.description, "Check description is missing"
    assert sample_check.output_statements, "Check output statements are missing"
    assert sample_check.fix_details, "Check fix details are missing"
    assert sample_check.metadata, "Check metadata is missing"
    
    # Verify nested structures
    assert isinstance(sample_check.metadata.tags, list), "Metadata tags should be a list"
    assert isinstance(sample_check.fix_details.instructions, list), "Fix details instructions should be a list"
    
    # Verify operation structure
    assert sample_check.operation, "Check operation is missing"
    
    # Print summary
    print(f"\nLoaded {len(loaded_checks)} checks from CSV")
    print(f"Sample check name: {sample_check.name}")
    print(f"Sample check type: {sample_check.resource_type}")
