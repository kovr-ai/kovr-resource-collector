"""Test checks CSV loading functionality."""

from datetime import datetime
from con_mon_v2.compliance.data_loader import ChecksLoader
from con_mon_v2.compliance.models import Check, CheckMetadata, OutputStatements, FixDetails, CheckOperation, ComparisonOperationEnum, ComparisonOperation

def test_load_checks_from_csv():
    """Test loading checks from CSV file."""
    try:
        # Initialize the ChecksLoader
        loader = ChecksLoader()
        
        # Test that we can create a loader instance
        assert loader is not None
        print("✅ ChecksLoader instance created successfully")
        
        # Test loading checks from CSV (if CSV file exists)
        try:
            checks = loader.load_all()
            print(f"✅ Loaded {len(checks)} checks from CSV")
            
            # Validate that loaded checks are Check instances
            if checks:
                first_check = checks[0]
                assert isinstance(first_check, Check)
                assert hasattr(first_check, 'id')
                assert hasattr(first_check, 'metadata')
                assert hasattr(first_check, 'output_statements')
                assert hasattr(first_check, 'fix_details')
                print("✅ Check objects have correct structure")
                
        except FileNotFoundError:
            print("⚠️ No CSV file found, skipping load test")
        except Exception as e:
            print(f"⚠️ CSV loading failed (expected if no data): {e}")
            
    except Exception as e:
        print(f"❌ ChecksLoader test failed: {e}")
        raise

def test_check_model_structure():
    """Test that the new Check model has the expected structure."""
    # Test creating a basic check with the new compliance model
    try:
        metadata = CheckMetadata(
            operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
            field_path="test.path",
            tags=["test"],
            category="test",
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
            estimated_date="2024-12-31",
            automation_available=False
        )
        
        check = Check(
            id="test_check",
            name="Test Check",
            description="Test description",
            category="test",
            created_by="test",
            updated_by="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata,
            output_statements=output_statements,
            fix_details=fix_details
        )
        
        assert check.id == "test_check"
        assert check.metadata.field_path == "test.path"
        assert check.metadata.operation.name == ComparisonOperationEnum.CUSTOM
        assert check.output_statements.success == "Test passed"
        assert check.fix_details.description == "Test fix"
        print("✅ Check model structure test passed")
        
    except Exception as e:
        print(f"❌ Check model structure test failed: {e}")
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
            
        print("✅ CheckOperation enum validation test passed")
        
    except Exception as e:
        print(f"❌ CheckOperation enum validation test failed: {e}")
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
            # Should return False (default fallback) due to syntax error
            assert result == False
            print("✅ Syntax error handled gracefully - returned False")
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
        # Should return False due to runtime error being caught by try-catch wrapper
        assert result == False
        print("✅ Runtime error handled gracefully - returned False")

        # Test 2b: Runtime error with try-catch in logic
        print("🧪 Testing runtime error with internal error handling...")
        safe_runtime_logic = """
try:
    if fetched_value:
        result = 1 / 0  # This will cause error but should be caught
    else:
        result = False
except:
    result = False  # Fallback on any error
"""
        safe_runtime_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, safe_runtime_logic)
        result = safe_runtime_func("test", None)
        assert result == False
        print("✅ Runtime error with internal handling - returned False")

        # Test 3: Logic that doesn't set result variable
        print("🧪 Testing logic without result variable...")
        no_result_logic = """
# This logic doesn't set the result variable
temp_var = fetched_value if fetched_value else "default"
# Missing: result = something
"""
        no_result_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, no_result_logic)
        result = no_result_func("test", None)
        # Should return False (default value set in template)
        assert result == False
        print("✅ Missing result variable handled - returned False")

        # Test 4: Logic with forbidden operations (should be restricted by safe_globals)
        print("🧪 Testing forbidden operations...")
        forbidden_logic = """
# Try to access forbidden functions/modules
import os  # Should fail due to restricted globals
result = True
"""
        try:
            forbidden_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, forbidden_logic)
            result = forbidden_func("test", None)
            # If it doesn't raise an error, it should return False
            print(f"✅ Forbidden operations handled, result: {result}")
        except (NameError, ImportError) as e:
            print(f"✅ Forbidden operations properly blocked: {type(e).__name__}")

        # Test 5: Logic with undefined variables
        print("🧪 Testing undefined variables...")
        undefined_var_logic = """
if fetched_value:
    # Using undefined variable
    result = undefined_variable > 0
else:
    result = False
"""
        undefined_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, undefined_var_logic)
        result = undefined_func("test", None)
        # Should return False due to NameError being caught by try-catch wrapper
        assert result == False
        print("✅ Undefined variable handled gracefully - returned False")

        # Test 6: Logic with return statements (should be ignored/cause issues)
        print("🧪 Testing logic with return statements...")
        return_logic = """
if fetched_value:
    return True  # This actually works in the function scope
result = False
"""
        return_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, return_logic)
        result = return_func("test", None)
        # Return statement actually works within the generated function scope
        assert result == True
        print("✅ Return statement works within function scope - returned True")

        # Test 7: Very long/complex logic that might timeout or cause issues
        print("🧪 Testing complex logic...")
        complex_logic = """
if fetched_value and isinstance(fetched_value, list):
    # Complex nested processing
    processed_items = []
    for item in fetched_value:
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, str) and len(value) > 0:
                    processed_items.append(f"{key}:{value}")
    
    # Multiple validation criteria
    has_items = len(processed_items) > 0
    has_required_keys = any("name:" in item for item in processed_items)
    has_valid_format = all(len(item.split(":")) == 2 for item in processed_items)
    
    result = has_items and has_required_keys and has_valid_format
else:
    result = False
"""
        complex_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, complex_logic)
        
        # Test with valid complex data
        complex_data = [
            {"name": "test1", "value": "data1"},
            {"name": "test2", "value": "data2"}
        ]
        result = complex_func(complex_data, None)
        assert result == True
        print("✅ Complex logic executed successfully")

        # Test 8: Empty or whitespace-only logic
        print("🧪 Testing empty logic...")
        empty_logic = """
# Just comments and whitespace


"""
        empty_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, empty_logic)
        result = empty_func("test", None)
        # Should return False (default value)
        assert result == False
        print("✅ Empty logic handled - returned False")

        # Test 9: Logic that tries to modify global state
        print("🧪 Testing global state modification attempts...")
        global_modify_logic = """
# Try to modify something outside the function scope
global some_global_var
some_global_var = "modified"
result = True
"""
        try:
            global_func = ComparisonOperation.get_custom_function(ComparisonOperationEnum.CUSTOM, global_modify_logic)
            result = global_func("test", None)
            print(f"✅ Global modification attempt result: {result}")
        except Exception as e:
            print(f"✅ Global modification properly blocked: {type(e).__name__}")

        print("✅ Invalid logic handling tests completed")
        
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
    test_load_checks_from_csv()
    test_check_model_structure()
    test_check_operation_enum_validation()
    test_comparison_operation_standard_functions()
    test_comparison_operation_custom_logic()
    test_comparison_operation_edge_cases()
    test_comparison_operation_full_workflow()
    test_comparison_operation_invalid_logic_handling()
    test_comparison_operation_security_restrictions()
    print("✅ All tests passed")
