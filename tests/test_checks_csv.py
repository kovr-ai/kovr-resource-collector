"""Tests for loading checks from CSV."""
import os
from datetime import datetime
from con_mon_v2.checks.db_loader import load_checks_from_csv
from con_mon_v2.checks.models import Check, CheckMetadata, CheckResultStatement, CheckFailureFix, CheckOperation

def test_load_checks_from_csv():
    """Test loading checks from CSV file with comprehensive deep-level validation."""
    # Ensure CSV file exists
    assert os.path.exists("data/csv/checks.csv"), "CSV file not found"
    
    # Load checks from CSV
    loaded_checks = load_checks_from_csv()
    
    # Verify checks were loaded
    assert loaded_checks, "No checks were loaded from CSV"
    assert len(loaded_checks) > 0, "Expected at least one check to be loaded"
    
    # Get a sample check
    sample_check = next(iter(loaded_checks.values()))
    
    # Deep validation of Check object structure
    assert isinstance(sample_check, Check), "Sample check should be a Check instance"
    
    # Verify basic Check fields
    assert sample_check.id is not None, "Check ID is missing"
    assert isinstance(sample_check.id, str), "Check ID should be a string"
    assert sample_check.name, "Check name is missing"
    assert isinstance(sample_check.name, str), "Check name should be a string"
    assert sample_check.description, "Check description is missing"
    assert isinstance(sample_check.description, str), "Check description should be a string"
    assert sample_check.category, "Check category is missing"
    assert isinstance(sample_check.category, str), "Check category should be a string"
    
    # Verify database-specific fields
    assert sample_check.created_by, "Check created_by is missing"
    assert isinstance(sample_check.created_by, str), "Check created_by should be a string"
    assert sample_check.updated_by, "Check updated_by is missing"
    assert isinstance(sample_check.updated_by, str), "Check updated_by should be a string"
    assert isinstance(sample_check.created_at, datetime), "Check created_at should be a datetime"
    assert isinstance(sample_check.updated_at, datetime), "Check updated_at should be a datetime"
    assert isinstance(sample_check.is_deleted, bool), "Check is_deleted should be a boolean"
    assert sample_check.is_deleted == False, "Check should not be marked as deleted"
    
    # Deep validation of CheckResultStatement
    assert sample_check.output_statements, "Check output statements are missing"
    assert isinstance(sample_check.output_statements, CheckResultStatement), "Output statements should be CheckResultStatement instance"
    assert sample_check.output_statements.success, "Output success message is missing"
    assert isinstance(sample_check.output_statements.success, str), "Output success should be a string"
    assert sample_check.output_statements.failure, "Output failure message is missing"
    assert isinstance(sample_check.output_statements.failure, str), "Output failure should be a string"
    assert sample_check.output_statements.partial, "Output partial message is missing"
    assert isinstance(sample_check.output_statements.partial, str), "Output partial should be a string"
    
    # Deep validation of CheckFailureFix
    assert sample_check.fix_details, "Check fix details are missing"
    assert isinstance(sample_check.fix_details, CheckFailureFix), "Fix details should be CheckFailureFix instance"
    assert sample_check.fix_details.description, "Fix description is missing"
    assert isinstance(sample_check.fix_details.description, str), "Fix description should be a string"
    assert isinstance(sample_check.fix_details.instructions, list), "Fix instructions should be a list"
    assert len(sample_check.fix_details.instructions) > 0, "Fix instructions should not be empty"
    assert all(isinstance(instr, str) for instr in sample_check.fix_details.instructions), "All fix instructions should be strings"
    assert sample_check.fix_details.estimated_date, "Fix estimated_date is missing"
    assert isinstance(sample_check.fix_details.estimated_date, str), "Fix estimated_date should be a string"
    assert isinstance(sample_check.fix_details.automation_available, bool), "Fix automation_available should be a boolean"
    
    # Deep validation of CheckMetadata
    assert sample_check.metadata, "Check metadata is missing"
    assert isinstance(sample_check.metadata, CheckMetadata), "Metadata should be CheckMetadata instance"
    
    # Verify metadata tags
    assert isinstance(sample_check.metadata.tags, list), "Metadata tags should be a list"
    assert len(sample_check.metadata.tags) > 0, "Metadata tags should not be empty"
    assert all(isinstance(tag, str) for tag in sample_check.metadata.tags), "All tags should be strings"
    assert "compliance" in sample_check.metadata.tags, "Tags should include 'compliance'"
    assert "nist" in sample_check.metadata.tags, "Tags should include 'nist'"
    
    # Verify metadata severity and category
    assert sample_check.metadata.severity, "Metadata severity is missing"
    assert isinstance(sample_check.metadata.severity, str), "Metadata severity should be a string"
    assert sample_check.metadata.severity in ["low", "medium", "high", "critical"], "Metadata severity should be valid"
    assert sample_check.metadata.category, "Metadata category is missing"
    assert isinstance(sample_check.metadata.category, str), "Metadata category should be a string"
    
    # Verify metadata field_path
    assert sample_check.metadata.field_path, "Metadata field_path is missing"
    assert isinstance(sample_check.metadata.field_path, str), "Metadata field_path should be a string"
    assert "." in sample_check.metadata.field_path, "Field path should be dot-separated"
    
    # Verify metadata expected_value
    assert sample_check.metadata.expected_value is not None, "Metadata expected_value should be present (can be empty string)"
    
    # Verify metadata name
    assert sample_check.metadata.name, "Metadata name is missing"
    assert isinstance(sample_check.metadata.name, str), "Metadata name should be a string"
    assert sample_check.metadata.name == sample_check.name, "Metadata name should match check name"
    
    # Deep validation of CheckOperation
    assert sample_check.metadata.operation, "Check operation is missing"
    assert isinstance(sample_check.metadata.operation, CheckOperation), "Operation should be CheckOperation instance"
    assert sample_check.metadata.operation.name, "Check operation name is missing"
    assert isinstance(sample_check.metadata.operation.name, str), "Operation name should be a string"
    assert sample_check.metadata.operation.name in ["custom", "equal", "not_equal", "contains", "not_contains", "less_than", "greater_than"], "Operation name should be valid"
    assert sample_check.metadata.operation.logic, "Check operation logic is missing"
    assert isinstance(sample_check.metadata.operation.logic, str), "Operation logic should be a string"
    assert "result = " in sample_check.metadata.operation.logic, "Operation logic should contain result assignment"
    assert len(sample_check.metadata.operation.logic.strip()) > 10, "Operation logic should be substantial"
    
    # Verify operation logic structure for custom operations
    if sample_check.metadata.operation.name == "custom":
        logic = sample_check.metadata.operation.logic
        assert "result = False" in logic or "result = True" in logic, "Custom logic should set result variable"
        assert "fetched_value" in logic, "Custom logic should reference fetched_value"
        # Check for proper Python syntax structure
        lines = logic.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        assert len(non_empty_lines) > 1, "Custom logic should have multiple lines"
    
    # Test multiple checks to ensure consistency
    check_count = 0
    for check_name, check in loaded_checks.items():
        check_count += 1
        # Basic validation for all checks
        assert isinstance(check, Check), f"Check {check_name} should be a Check instance"
        assert check.id, f"Check {check_name} should have an ID"
        assert check.name == check_name, f"Check name should match dictionary key"
        assert isinstance(check.metadata, CheckMetadata), f"Check {check_name} metadata should be CheckMetadata instance"
        assert isinstance(check.metadata.operation, CheckOperation), f"Check {check_name} operation should be CheckOperation instance"
        
        # Stop after validating 5 checks to avoid excessive test time
        if check_count >= 5:
            break
    
    # Print comprehensive summary
    print(f"\n✅ Loaded {len(loaded_checks)} checks from CSV")
    print(f"✅ Sample check name: {sample_check.name}")
    print(f"✅ Sample check ID: {sample_check.id}")
    print(f"✅ Sample check category: {sample_check.category}")
    print(f"✅ Sample check field_path: {sample_check.metadata.field_path}")
    print(f"✅ Sample check operation: {sample_check.metadata.operation.name}")
    print(f"✅ Sample check tags: {', '.join(sample_check.metadata.tags[:3])}...")
    print(f"✅ Sample check logic length: {len(sample_check.metadata.operation.logic)} characters")
    print(f"✅ Validated {min(check_count, 5)} checks for consistency")
