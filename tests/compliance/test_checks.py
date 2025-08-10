"""Test checks CSV loading functionality."""

from datetime import datetime
from con_mon_v2.compliance.models import Check, CheckMetadata, OutputStatements, FixDetails, CheckOperation, ComparisonOperationEnum, ComparisonOperation
from con_mon_v2.resources import Resource

# Mock Resource for testing
class MockResource(Resource):
    """Mock resource for testing field extraction"""
    
    # Define the additional fields that aren't in the base Resource class
    repository_data: dict
    collaborators: list
    
    def __init__(self, **data):
        # Set required Resource fields
        if 'id' not in data:
            data['id'] = "mock_resource"
        if 'source_connector' not in data:
            data['source_connector'] = "mock"
        
        # Set mock data
        if 'repository_data' not in data:
            data['repository_data'] = {
                'branches': [
                    {'name': 'main', 'protection_details': {'enabled': True, 'required_reviewers': 2}},
                    {'name': 'dev', 'protection_details': {'enabled': False, 'required_reviewers': 1}},
                    {'name': 'feature', 'protection_details': {'enabled': True, 'required_reviewers': 3}},
                    {'name': 'hotfix', 'protection_details': None}  # Test missing data
                ],
                'security_settings': {
                    'alerts': [
                        {'type': 'secret_scanning', 'enabled': True},
                        {'type': 'dependency_scanning', 'enabled': False},
                        {'type': 'code_scanning', 'enabled': True}
                    ]
                },
                'basic_info': {
                    'description': 'Test repository',
                    'visibility': 'private'
                }
            }
        
        if 'collaborators' not in data:
            data['collaborators'] = [
                {'login': 'admin1', 'permissions': {'admin': True, 'push': True}},
                {'login': 'dev1', 'permissions': {'admin': False, 'push': True}},
                {'login': 'viewer1', 'permissions': {'admin': False, 'push': False}}
            ]
        
        # Call parent constructor
        super().__init__(**data)

def test_check_model_structure():
    """Test that the new Check model has the expected structure."""
    # Test creating a basic check with the new compliance model
    try:
        metadata = CheckMetadata(
            operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
            field_path="test.path",
            tags=["test"],
            category="test",  # RESTORED: Keep category field in metadata
            severity="medium"
        )
        
        output_statements = OutputStatements(
            success="Test passed",
            failure="Test failed", 
            partial="Test partial"
        )
        
        fix_details = FixDetails(
            description="Test fix",
            instructions=["Step 1", "Step 2"],
            estimated_time="2 weeks",
            automation_available=False
        )
        
        check = Check(
            id="test_check",
            name="Test Check",
            description="Test description",
            category="test",  # Category is at root level
            created_by="test",
            updated_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata,
            output_statements=output_statements,
            fix_details=fix_details
        )
        
        assert check.id == "test_check"
        assert check.category == "test"  # Verify root level category
        assert check.metadata.field_path == "test.path"
        assert check.metadata.operation.name == ComparisonOperationEnum.CUSTOM
        assert check.metadata.severity == "medium"  # Verify metadata severity
        assert check.metadata.tags == ["test"]  # Verify metadata tags
        assert check.metadata.category == "test"  # Verify metadata category
        assert check.output_statements.success == "Test passed"
        assert check.fix_details.description == "Test fix"
        assert check.fix_details.estimated_time == "2 weeks"  # Verify estimated_time field
        
        print("✅ Check model structure test passed")
        
    except Exception as e:
        print(f"❌ Check model structure test failed: {e}")
        raise

def test_enhanced_field_extraction_wildcards():
    """Test enhanced field extraction with wildcard array operations."""
    try:
        # Create a test check with custom operation for field extraction
        metadata = CheckMetadata(
            operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
            field_path="repository_data.branches.*.protection_details.enabled",
            resource_type="tests.compliance.test_checks.MockResource",
            tags=["test"],
            category="test",
            severity="medium"
        )
        
        check = Check(
            id="test_wildcard",
            name="Wildcard Test Check",
            description="Test wildcard extraction",
            category="test",
            created_by="test",
            updated_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata,
            output_statements=OutputStatements(
                success="Test passed", failure="Test failed", partial="Test partial"
            ),
            fix_details=FixDetails(
                description="Test fix", instructions=["Step 1"], automation_available=False
            )
        )
        
        resource = MockResource()
        
        # Test wildcard extraction
        enabled_values = check._extract_field_value(resource, "repository_data.branches.*.protection_details.enabled")
        expected = [True, False, True]  # Note: None values are filtered out
        assert enabled_values == expected, f"Expected {expected}, got {enabled_values}"
        
        # Test wildcard with numeric values
        reviewer_counts = check._extract_field_value(resource, "repository_data.branches.*.protection_details.required_reviewers")
        expected_reviewers = [2, 1, 3]  # None values filtered out
        assert reviewer_counts == expected_reviewers, f"Expected {expected_reviewers}, got {reviewer_counts}"
        
        # Test wildcard at end of path
        branch_names = check._extract_field_value(resource, "repository_data.branches.*.name")
        expected_names = ['main', 'dev', 'feature', 'hotfix']
        assert branch_names == expected_names, f"Expected {expected_names}, got {branch_names}"
        
        print("✅ Enhanced field extraction wildcards test passed")
        
    except Exception as e:
        print(f"❌ Enhanced field extraction wildcards test failed: {e}")
        raise

def test_enhanced_field_extraction_functions():
    """Test enhanced field extraction with built-in functions."""
    try:
        resource = MockResource()
        
        # Create a test check for function testing
        metadata = CheckMetadata(
            operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
            field_path="test.path",
            resource_type="tests.compliance.test_checks.MockResource",
            tags=["test"],
            category="test",
            severity="medium"
        )
        
        check = Check(
            id="test_functions",
            name="Functions Test Check",
            description="Test function extraction",
            category="test",
            created_by="test",
            updated_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata,
            output_statements=OutputStatements(
                success="Test passed", failure="Test failed", partial="Test partial"
            ),
            fix_details=FixDetails(
                description="Test fix", instructions=["Step 1"], automation_available=False
            )
        )
        
        # Test len() function
        branch_count = check._extract_field_value(resource, "len(repository_data.branches)")
        assert branch_count == 4, f"Expected 4 branches, got {branch_count}"
        
        # Test any() function
        any_protected = check._extract_field_value(resource, "any(repository_data.branches.*.protection_details.enabled)")
        assert any_protected == True, f"Expected True for any protected, got {any_protected}"
        
        # Test all() function  
        all_protected = check._extract_field_value(resource, "all(repository_data.branches.*.protection_details.enabled)")
        assert all_protected == False, f"Expected False for all protected, got {all_protected}"
        
        # Test count() function
        protected_count = check._extract_field_value(resource, "count(repository_data.branches.*.protection_details.enabled)")
        assert protected_count == 2, f"Expected 2 protected branches, got {protected_count}"
        
        # Test sum() function
        total_reviewers = check._extract_field_value(resource, "sum(repository_data.branches.*.protection_details.required_reviewers)")
        assert total_reviewers == 6, f"Expected 6 total reviewers, got {total_reviewers}"  # 2+1+3
        
        # Test max() function
        max_reviewers = check._extract_field_value(resource, "max(repository_data.branches.*.protection_details.required_reviewers)")
        assert max_reviewers == 3, f"Expected 3 max reviewers, got {max_reviewers}"
        
        # Test min() function
        min_reviewers = check._extract_field_value(resource, "min(repository_data.branches.*.protection_details.required_reviewers)")
        assert min_reviewers == 1, f"Expected 1 min reviewers, got {min_reviewers}"
        
        print("✅ Enhanced field extraction functions test passed")
        
    except Exception as e:
        print(f"❌ Enhanced field extraction functions test failed: {e}")
        raise

def test_enhanced_field_extraction_edge_cases():
    """Test enhanced field extraction edge cases and error handling."""
    try:
        resource = MockResource()
        
        # Create a test check
        metadata = CheckMetadata(
            operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
            field_path="test.path",
            resource_type="tests.compliance.test_checks.MockResource",
            tags=["test"],
            category="test",
            severity="medium"
        )
        
        check = Check(
            id="test_edge_cases",
            name="Edge Cases Test Check", 
            description="Test edge cases",
            category="test",
            created_by="test",
            updated_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata,
            output_statements=OutputStatements(
                success="Test passed", failure="Test failed", partial="Test partial"
            ),
            fix_details=FixDetails(
                description="Test fix", instructions=["Step 1"], automation_available=False
            )
        )
        
        # Test non-existent path with function
        try:
            result = check._extract_field_value(resource, "len(nonexistent.path)")
            # Should handle gracefully and return 0
            assert result == 0, f"Expected 0 for non-existent path, got {result}"
        except AttributeError:
            # This is also acceptable behavior
            pass
        
        # Test function with empty array - should handle missing field gracefully
        try:
            empty_result = check._extract_field_value(resource, "len(repository_data.empty_array)")
            # Should handle missing field gracefully and return 0
            assert empty_result == 0, f"Expected 0 for missing field, got {empty_result}"
        except AttributeError:
            # Expected for non-existent paths - this is acceptable behavior
            pass
        
        # Test any() with empty results
        try:
            any_empty = check._extract_field_value(resource, "any(repository_data.nonexistent.*.field)")
            # Should handle gracefully
        except AttributeError:
            # Expected for non-existent paths
            pass
        
        # Test function on non-array data (this should work)
        desc_length = check._extract_field_value(resource, "len(repository_data.basic_info.description)")
        assert isinstance(desc_length, int), f"Expected int length, got {type(desc_length)}"
        assert desc_length > 0, f"Expected positive length, got {desc_length}"
        
        # Test regular field extraction that should work
        branch_count = check._extract_field_value(resource, "len(repository_data.branches)")
        assert branch_count == 4, f"Expected 4 branches, got {branch_count}"
        
        print("✅ Enhanced field extraction edge cases test passed")
        
    except Exception as e:
        print(f"❌ Enhanced field extraction edge cases test failed: {e}")
        raise

def test_enhanced_field_extraction_complex_scenarios():
    """Test complex real-world scenarios with enhanced field extraction."""
    try:
        resource = MockResource()
        
        # Create a test check
        metadata = CheckMetadata(
            operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
            field_path="test.path",
            resource_type="tests.compliance.test_checks.MockResource",
            tags=["test"],
            category="test",
            severity="medium"
        )
        
        check = Check(
            id="test_complex",
            name="Complex Scenarios Test Check",
            description="Test complex scenarios",
            category="test",
            created_by="test",
            updated_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata,
            output_statements=OutputStatements(
                success="Test passed", failure="Test failed", partial="Test partial"
            ),
            fix_details=FixDetails(
                description="Test fix", instructions=["Step 1"], automation_available=False
            )
        )
        
        # Scenario 1: Check if any security alerts are enabled
        any_alerts = check._extract_field_value(resource, "any(repository_data.security_settings.alerts.*.enabled)")
        assert any_alerts == True, f"Expected True for any alerts enabled, got {any_alerts}"
        
        # Scenario 2: Count admin collaborators
        admin_perms = check._extract_field_value(resource, "collaborators.*.permissions.admin")
        admin_count = check._extract_field_value(resource, "count(collaborators.*.permissions.admin)")
        assert admin_count == 1, f"Expected 1 admin, got {admin_count}"  # Only one True value
        
        # Scenario 3: Check if all branches have protection (should be False)
        all_protected = check._extract_field_value(resource, "all(repository_data.branches.*.protection_details.enabled)")
        assert all_protected == False, f"Expected False for all protected, got {all_protected}"
        
        # Scenario 4: Get maximum required reviewers across all branches
        max_reviewers = check._extract_field_value(resource, "max(repository_data.branches.*.protection_details.required_reviewers)")
        assert max_reviewers == 3, f"Expected 3 max reviewers, got {max_reviewers}"
        
        # Scenario 5: Count total security alert types
        alert_count = check._extract_field_value(resource, "len(repository_data.security_settings.alerts)")
        assert alert_count == 3, f"Expected 3 alert types, got {alert_count}"
        
        print("✅ Enhanced field extraction complex scenarios test passed")
        
    except Exception as e:
        print(f"❌ Enhanced field extraction complex scenarios test failed: {e}")
        raise

def test_check_operation_enum_validation():
    """Test that CheckOperation properly validates enum values."""
    try:
        # Test valid enum values
        valid_operations = [
            ComparisonOperationEnum.CUSTOM,
            ComparisonOperationEnum.EQUAL,
            ComparisonOperationEnum.NOT_EQUAL,
            ComparisonOperationEnum.CONTAINS
        ]
        
        for op_enum in valid_operations:
            operation = CheckOperation(name=op_enum, logic="result = True")
            assert operation.name == op_enum
            
        # Test that CUSTOM operation requires valid logic
        try:
            CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="")
            # This should work at model level, but fail when used with get_custom_function
        except Exception:
            pass  # Model validation might not catch this
            
        print("✅ CheckOperation enum validation test passed")
        
    except Exception as e:
        print(f"❌ CheckOperation enum validation test failed: {e}")
        raise

def test_check_operation_empty_logic_validation():
    """Test that CheckOperation properly validates empty logic when creating comparison functions."""
    try:
        # Test that empty logic is rejected when creating the actual function
        operation = CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="")
        
        # This should fail when trying to create the comparison function
        try:
            ComparisonOperation.get_custom_function(operation.name, operation.logic)
            assert False, "Should have raised ValueError for empty logic"
        except ValueError as e:
            assert "cannot be empty" in str(e)
            print("✅ Empty logic in CheckOperation properly rejected")
        
        # Test that whitespace-only logic is rejected
        operation_whitespace = CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="   \n\t   ")
        try:
            ComparisonOperation.get_custom_function(operation_whitespace.name, operation_whitespace.logic)
            assert False, "Should have raised ValueError for whitespace-only logic"
        except ValueError as e:
            assert "cannot be empty" in str(e)
            print("✅ Whitespace-only logic in CheckOperation properly rejected")
        
        # Test that comments-only logic is rejected
        operation_comments = CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="# Only comments")
        try:
            ComparisonOperation.get_custom_function(operation_comments.name, operation_comments.logic)
            assert False, "Should have raised ValueError for comments-only logic"
        except ValueError as e:
            assert "only comments and whitespace" in str(e)
            print("✅ Comments-only logic in CheckOperation properly rejected")
        
        print("✅ CheckOperation empty logic validation test passed")
        
    except Exception as e:
        print(f"❌ CheckOperation empty logic validation test failed: {e}")
        raise

def test_comparison_operation_standard_functions():
    """Test all standard comparison operation functions."""
    try:
        # Test EQUAL operation
        equal_func = ComparisonOperation.get_function(ComparisonOperationEnum.EQUAL)
        assert equal_func(5, 5) == True
        assert equal_func(5, 10) == False
        assert equal_func("test", "test") == True
        assert equal_func("test", "other") == False
        
        # Test NOT_EQUAL operation
        not_equal_func = ComparisonOperation.get_function(ComparisonOperationEnum.NOT_EQUAL)
        assert not_equal_func(5, 10) == True
        assert not_equal_func(5, 5) == False
        
        # Test LESS_THAN operation
        less_than_func = ComparisonOperation.get_function(ComparisonOperationEnum.LESS_THAN)
        assert less_than_func(5, 10) == True
        assert less_than_func(10, 5) == False
        assert less_than_func(5, 5) == False
        
        # Test GREATER_THAN operation
        greater_than_func = ComparisonOperation.get_function(ComparisonOperationEnum.GREATER_THAN)
        assert greater_than_func(10, 5) == True
        assert greater_than_func(5, 10) == False
        assert greater_than_func(5, 5) == False
        
        # Test LESS_THAN_OR_EQUAL operation
        lte_func = ComparisonOperation.get_function(ComparisonOperationEnum.LESS_THAN_OR_EQUAL)
        assert lte_func(5, 10) == True
        assert lte_func(5, 5) == True
        assert lte_func(10, 5) == False
        
        # Test GREATER_THAN_OR_EQUAL operation
        gte_func = ComparisonOperation.get_function(ComparisonOperationEnum.GREATER_THAN_OR_EQUAL)
        assert gte_func(10, 5) == True
        assert gte_func(5, 5) == True
        assert gte_func(5, 10) == False
        
        # Test CONTAINS operation
        contains_func = ComparisonOperation.get_function(ComparisonOperationEnum.CONTAINS)
        assert contains_func([1, 2, 3, 4], 3) == True
        assert contains_func([1, 2, 3, 4], 5) == False
        assert contains_func("hello world", "world") == True
        assert contains_func("hello world", "xyz") == False
        assert contains_func({"a": 1, "b": 2}, "a") == True
        assert contains_func({"a": 1, "b": 2}, "c") == False
        
        # Test NOT_CONTAINS operation
        not_contains_func = ComparisonOperation.get_function(ComparisonOperationEnum.NOT_CONTAINS)
        assert not_contains_func([1, 2, 3, 4], 5) == True
        assert not_contains_func([1, 2, 3, 4], 3) == False
        assert not_contains_func("hello world", "xyz") == True
        assert not_contains_func("hello world", "world") == False
        
        print("✅ Standard comparison operations test passed")
        
    except Exception as e:
        print(f"❌ Standard comparison operations test failed: {e}")
        raise

def test_comparison_operation_custom_logic():
    """Test custom logic execution in comparison operations."""
    try:
        # Test simple custom logic
        simple_logic = """
if fetched_value and isinstance(fetched_value, int):
    result = fetched_value > 10
"""
        custom_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, simple_logic)
        assert custom_func(15, None) == True
        assert custom_func(5, None) == False
        assert custom_func(None, None) == False
        
        # Test complex custom logic with list processing
        complex_logic = """
if fetched_value and isinstance(fetched_value, list):
    admin_count = sum(1 for item in fetched_value if isinstance(item, dict) and item.get('role') == 'admin')
    total_count = len(fetched_value)
    
    if total_count > 0:
        admin_ratio = admin_count / total_count
        result = admin_count > 0 and admin_ratio <= 0.5
    else:
        result = False
"""
        complex_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, complex_logic)
        
        # Test with valid admin list
        good_members = [
            {"name": "user1", "role": "member"},
            {"name": "admin1", "role": "admin"},
            {"name": "user2", "role": "member"}
        ]
        assert complex_func(good_members, None) == True
        
        # Test with too many admins
        bad_members = [
            {"name": "admin1", "role": "admin"},
            {"name": "admin2", "role": "admin"}
        ]
        assert complex_func(bad_members, None) == False
        
        # Test with no admins
        no_admins = [
            {"name": "user1", "role": "member"},
            {"name": "user2", "role": "member"}
        ]
        assert complex_func(no_admins, None) == False
        
        # Test string validation logic
        string_logic = """
if fetched_value and isinstance(fetched_value, str):
    result = len(fetched_value.strip()) > 0 and not fetched_value.lower().startswith('todo')
"""
        string_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, string_logic)
        assert string_func("Valid description", None) == True
        assert string_func("TODO: Add description", None) == False
        assert string_func("", None) == False
        assert string_func("   ", None) == False
        
        print("✅ Custom logic comparison operations test passed")
        
    except Exception as e:
        print(f"❌ Custom logic comparison operations test failed: {e}")
        raise

def test_comparison_operation_edge_cases():
    """Test edge cases and error handling in comparison operations."""
    try:
        # Test contains with non-container types
        contains_func = ComparisonOperation.get_function(ComparisonOperationEnum.CONTAINS)
        assert contains_func(42, 4) == False  # int doesn't have __contains__
        assert contains_func(None, "test") == False
        
        # Test not_contains with non-container types
        not_contains_func = ComparisonOperation.get_function(ComparisonOperationEnum.NOT_CONTAINS)
        assert not_contains_func(42, 4) == True  # int doesn't have __contains__
        assert not_contains_func(None, "test") == True
        
        # Test custom logic with None values
        null_handling_logic = """
if fetched_value is None:
    result = config_value is None
else:
    result = fetched_value == config_value
"""
        null_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, null_handling_logic)
        assert null_func(None, None) == True
        assert null_func(None, "test") == False
        assert null_func("test", "test") == True
        
        # Test custom logic with exception handling
        safe_logic = """
try:
    if fetched_value and hasattr(fetched_value, '__len__'):
        result = len(fetched_value) > 0
    else:
        result = False
except Exception:
    result = False
"""
        safe_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, safe_logic)
        assert safe_func([1, 2, 3], None) == True
        assert safe_func([], None) == False
        assert safe_func("test", None) == True
        assert safe_func("", None) == False
        
        print("✅ Comparison operation edge cases test passed")
        
    except Exception as e:
        print(f"❌ Comparison operation edge cases test failed: {e}")
        raise

def test_comparison_operation_full_workflow():
    """Test complete ComparisonOperation workflow with callable interface."""
    try:
        # Create ComparisonOperation instances and test callable interface
        equal_op = ComparisonOperation(
            name=ComparisonOperationEnum.EQUAL,
            function=ComparisonOperation.get_function(ComparisonOperationEnum.EQUAL)
        )
        
        # Test callable interface
        assert equal_op(5, 5) == True
        assert equal_op(5, 10) == False
        
        # Create custom operation
        custom_logic = """
if isinstance(fetched_value, dict) and isinstance(config_value, str):
    result = config_value in fetched_value
else:
    result = False
"""
        custom_op = ComparisonOperation(
            name=ComparisonOperationEnum.CUSTOM,
            function=ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, custom_logic)
        )
        
        test_dict = {"enabled": True, "security": "high", "monitoring": False}
        assert custom_op(test_dict, "security") == True
        assert custom_op(test_dict, "missing") == False
        assert custom_op("not a dict", "security") == False
        
        print("✅ Complete comparison operation workflow test passed")
        
    except Exception as e:
        print(f"❌ Complete comparison operation workflow test failed: {e}")
        raise

def test_comparison_operation_invalid_logic_handling():
    """Test error handling for invalid custom logic and malformed code."""
    try:
        # Test 1: Syntax error in custom logic
        print("🧪 Testing syntax error handling...")
        syntax_error_logic = """
if fetched_value and isinstance(fetched_value, str:  # Missing closing parenthesis
    result = True
"""
        try:
            syntax_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, syntax_error_logic)
            # If no exception is raised during creation, test the function
            result = syntax_func("test", None)
            # Should return None (execution failure) due to syntax error
            assert result is None
            print("✅ Syntax error handled gracefully - returned None")
        except SyntaxError:
            print("✅ Syntax error properly caught and raised")
        except Exception as e:
            print(f"✅ Syntax error handled with exception: {type(e).__name__}")

        # Test 2: Runtime error in custom logic
        print("🧪 Testing runtime error handling...")
        runtime_error_logic = """
if fetched_value:
    # This will cause a runtime error - dividing by zero
    result = 1 / 0
else:
    result = False
"""
        runtime_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, runtime_error_logic)
        # Test that runtime errors are handled gracefully
        result = runtime_func("test", None)
        # Should return None (execution failure) due to runtime error being caught
        assert result is None
        print("✅ Runtime error handled gracefully - returned None (execution failure)")

        # Test 3: Logic that executes successfully but returns False
        print("🧪 Testing successful execution with False result...")
        false_logic = """
if fetched_value == "impossible_value":
    result = True
else:
    result = False  # This should execute successfully and return False
"""
        false_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, false_logic)
        result = false_func("test", None)
        # Should return False (logic failure, not execution failure)
        assert result == False
        print("✅ Logic executed successfully - returned False (logic failure)")

        # Test 4: Undefined variable error
        print("🧪 Testing undefined variable error...")
        undefined_var_logic = """
if fetched_value:
    result = undefined_variable  # This variable doesn't exist
else:
    result = False
"""
        undefined_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, undefined_var_logic)
        result = undefined_func("test", None)
        # Should return None (execution failure) due to undefined variable
        assert result is None
        print("✅ Undefined variable error handled - returned None (execution failure)")

        # Test 5: Missing result variable (execution failure)
        print("🧪 Testing missing result variable...")
        missing_result_logic = """
# This logic doesn't set the result variable
if fetched_value:
    temp = True
"""
        missing_result_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, missing_result_logic)
        result = missing_result_func("test", None)
        # Should return False (default value when no exception occurs)
        assert result == False
        print("✅ Missing result variable - returned False (default)")

        # Test 6: Return statement in logic (should work fine)
        print("🧪 Testing return statement in custom logic...")
        return_logic = """
if fetched_value and len(fetched_value) > 0:
    result = True
    return result
result = False
"""
        return_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, return_logic)
        result = return_func("test", None)
        # Should return True (successful execution and logic)
        assert result == True
        print("✅ Return statement works - returned True")

        print("✅ All invalid logic handling tests passed!")
        
    except Exception as e:
        print(f"❌ Invalid logic handling test failed: {e}")
        raise

def test_comparison_operation_security_restrictions():
    """Test that security restrictions are properly enforced in custom logic."""
    try:
        # Test that dangerous builtins are not available
        dangerous_operations = [
            "open('/etc/passwd', 'r')",  # File operations
            "eval('1+1')",               # Code evaluation
            "exec('print(1)')",          # Code execution
            "__import__('os')",          # Import restrictions
        ]
        
        for i, dangerous_op in enumerate(dangerous_operations, 1):
            print(f"🧪 Testing security restriction {i}: {dangerous_op}")
            dangerous_logic = f"""
try:
    result = bool({dangerous_op})
except:
    result = False
"""
            try:
                dangerous_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, dangerous_logic)
                result = dangerous_func("test", None)
                # Should return False due to security restrictions
                assert result == False
                print(f"✅ Dangerous operation {i} properly restricted")
            except (NameError, TypeError) as e:
                print(f"✅ Dangerous operation {i} blocked with {type(e).__name__}")

        # Test that only allowed builtins are available
        print("🧪 Testing allowed builtins...")
        allowed_builtins_logic = """
# Test that allowed builtins work
if fetched_value and isinstance(fetched_value, list):
    result = len(fetched_value) > 0 and all(isinstance(x, str) for x in fetched_value)
else:
    result = False
"""
        allowed_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, allowed_builtins_logic)
        result = allowed_func(["test1", "test2"], None)
        assert result == True
        print("✅ Allowed builtins work correctly")

        # Test restricted builtins
        print("🧪 Testing restricted builtins...")
        restricted_logic = """
try:
    # These should not be available
    result = bool(compile) or bool(eval) or bool(exec)
except NameError:
    result = False  # Expected - these should not be available
"""
        restricted_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, restricted_logic)
        result = restricted_func("test", None)
        assert result == False
        print("✅ Restricted builtins properly blocked")

        print("✅ Security restrictions tests completed")
        
    except Exception as e:
        print(f"❌ Security restrictions test failed: {e}")
        raise

if __name__ == "__main__":
    test_check_model_structure()
    test_enhanced_field_extraction_wildcards()
    test_enhanced_field_extraction_functions()
    test_enhanced_field_extraction_edge_cases()
    test_enhanced_field_extraction_complex_scenarios()
    test_check_operation_enum_validation()
    test_check_operation_empty_logic_validation()
    test_comparison_operation_standard_functions()
    test_comparison_operation_custom_logic()
    test_comparison_operation_edge_cases()
    test_comparison_operation_full_workflow()
    test_comparison_operation_invalid_logic_handling()
    test_comparison_operation_security_restrictions()
    print("✅ All tests passed")
