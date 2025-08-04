"""
Checks module for resource validation and evaluation.
"""
import yaml
import os
from typing import Dict, Any, Callable, List, Tuple, Optional, Union
from .models import Check, ComparisonOperation, ComparisonOperationEnum

# Global storage for loaded checks
_loaded_checks: Dict[str, Check] = {}

def _create_check_from_config(check_id:int, check_name: str, check_config: Dict[str, Any]) -> Check:
    """Create a Check object from YAML configuration."""
    
    # Parse operation
    operation_config = check_config['operation']
    operation_name = operation_config['name']
    
    # Create ComparisonOperation - support both enum names and values
    try:
        # First try by enum name (e.g., "EQUAL", "NOT_EQUAL")
        operation_enum = ComparisonOperationEnum[operation_name]
    except KeyError:
        try:
            # Fallback to enum value (e.g., "==", "!=", "custom")
            operation_enum = ComparisonOperationEnum(operation_name)
        except ValueError:
            raise ValueError(f"Unsupported operation '{operation_name}'. Supported operations: {[op.name for op in ComparisonOperationEnum]} or {[op.value for op in ComparisonOperationEnum]}")
    
    operation = ComparisonOperation(name=operation_enum)
    
    # Handle custom logic if present - execute any logic defined in YAML
    if operation_name == 'custom' and 'custom_logic' in operation_config:
        custom_logic_code = operation_config['custom_logic']
        
        def create_dynamic_custom_function(code: str):
            """Create a custom function that executes YAML-defined logic."""
            def custom_function(fetched_value, config_value):
                # Create a safe namespace for executing the custom logic
                namespace = {
                    'fetched_value': fetched_value,
                    'config_value': config_value,
                    'isinstance': isinstance,
                    'list': list,
                    'dict': dict,
                    'getattr': getattr,
                    'len': len,
                    'any': any,
                    'all': all,
                    'True': True,
                    'False': False,
                    'None': None,
                    'result': False  # Default result
                }
                
                try:
                    # Execute the custom logic code from YAML
                    exec(code, {"__builtins__": {}}, namespace)
                    # The custom logic should set the 'result' variable
                    return namespace.get('result', False)
                    
                except Exception as e:
                    print(f"❌ Error executing custom logic for {check_name}: {e}")
                    return False
            
            return custom_function
        
        # Set the dynamic custom function on the operation
        operation.custom_function = create_dynamic_custom_function(custom_logic_code)
    
    # Create Check object
    return Check(
        id=check_id,
        name=check_name,
        field_path=check_config['field_path'],
        operation=operation,
        expected_value=check_config['expected_value'],
        description=check_config.get('description'),
        # NIST compliance fields
        framework_name=check_config.get('framework_name'),
        control_name=check_config.get('control_name'),
        # Additional metadata fields
        tags=check_config.get('tags'),
        severity=check_config.get('severity'),
        category=check_config.get('category')
    )

def load_checks_from_yaml(yaml_file_path: str = None):
    """
    Load checks from YAML file and make them accessible as module attributes.
    
    Args:
        yaml_file_path: Path to YAML file, defaults to checks/checks.yaml
    """
    global _loaded_checks
    
    if yaml_file_path is None:
        # Default to checks.yaml in the same directory as this file
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'checks.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
        
        # Process github_checks
        for check_config in yaml_data['checks']:
            check_id = check_config['id']
            check_name = check_config['name']

            # Create proper Check object
            check = _create_check_from_config(check_id, check_name, check_config)
            _loaded_checks[check_name] = check

            # Make accessible as module attribute
            globals()[check_name] = check
        
        print(f"✅ Loaded {len(_loaded_checks)} checks from {yaml_file_path}")
        
    except FileNotFoundError:
        print(f"❌ Checks YAML file not found: {yaml_file_path}")
    except Exception as e:
        print(f"❌ Error loading checks from YAML: {e}")

def get_loaded_checks() -> Dict[str, Check]:
    """Get all loaded checks."""
    return _loaded_checks.copy()

def get_checks_by_ids(check_ids: Optional[Union[List[int], int]] = None) -> List[Tuple[int, str, Check]]:
    """
    Get checks by their IDs or return all checks if check_ids is None or empty list.
    
    Args:
        check_ids: List of check IDs to filter by, single check ID, None or empty list to return all checks
        
    Returns:
        List of tuples in format (check_id, check_name, check_object)
        
    Examples:
        # Get all checks (any of these work)
        all_checks = get_checks_by_ids()
        all_checks = get_checks_by_ids(None)
        all_checks = get_checks_by_ids([])
        
        # Get specific checks by ID
        selected_checks = get_checks_by_ids([1001, 1002])
        
        # Get single check by ID
        single_check = get_checks_by_ids(1001)
    """
    # Convert single int to list for consistent processing
    if isinstance(check_ids, int):
        check_ids = [check_ids]
    
    # Treat empty list the same as None (return all checks)
    if check_ids is not None and len(check_ids) == 0:
        check_ids = None
    
    result = []
    
    for check_name, check_obj in _loaded_checks.items():
        # If no specific IDs requested, include all checks
        if check_ids is None:
            result.append((check_obj.id, check_name, check_obj))
        # If specific IDs requested, include only matching checks
        elif check_obj.id in check_ids:
            result.append((check_obj.id, check_name, check_obj))
    
    # Sort by check ID for consistent ordering
    result.sort(key=lambda x: x[0])
    
    # Log what checks were returned
    if check_ids is None:
        print(f"📋 Retrieved all {len(result)} available checks")
    else:
        found_ids = [check_id for check_id, _, _ in result]
        missing_ids = [cid for cid in check_ids if cid not in found_ids]
        
        print(f"📋 Retrieved {len(result)} checks matching IDs: {found_ids}")
        if missing_ids:
            print(f"⚠️ Warning: Check IDs not found: {missing_ids}")
    
    return result

# Auto-load checks when module is imported
load_checks_from_yaml()

# Export main functions and loaded checks
__all__ = [
    'get_checks_by_ids',
    'get_loaded_checks', 
    'load_checks_from_yaml'
] 
