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
    if operation_enum == ComparisonOperationEnum.CUSTOM and 'custom_logic' in operation_config:
        custom_logic = operation_config['custom_logic']
        
        def custom_function(fetched_value, config_value):
            # Create local namespace for the custom logic
            local_vars = {
                'fetched_value': fetched_value,
                'config_value': config_value,
                'result': False  # Default result
            }
            
            try:
                # Execute the custom logic code
                exec(custom_logic, {"__builtins__": __builtins__}, local_vars)
                return local_vars.get('result', False)
            except Exception as e:
                print(f"❌ Error in custom logic for check '{check_name}': {e}")
                return False
        
        operation.custom_function = custom_function
    
    # Create Check object with updated field names for CSV compatibility
    return Check(
        id=check_id,
        connection_id=check_config['connection_id'],        # Connection ID from YAML
        name=check_name,
        field_path=check_config['field_path'],
        operation=operation,
        expected_value=check_config['expected_value'],
        description=check_config.get('description'),
        
        # Updated to use both IDs and names from CSV data
        framework_id=check_config['framework_id'],      # Integer ID from CSV (required)
        control_id=check_config['control_id'],          # Integer ID from CSV (required)
        framework_name=check_config['framework_name'],  # String name from CSV (required)
        control_name=check_config['control_name'],      # String name from CSV (required)
        
        # Additional metadata
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
        print(f"📊 Using framework_id and control_id from CSV data for better performance")
        
    except FileNotFoundError:
        print(f"❌ Checks YAML file not found: {yaml_file_path}")
    except Exception as e:
        print(f"❌ Error loading checks from YAML: {e}")

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
    
    result = []
    
    for check_name, check_obj in _loaded_checks.items():
        # First filter by connection_id
        if check_obj.connection_id != connection_id:
            continue
            
        # If no specific IDs requested, include all checks for this connection
        if check_ids is None:
            result.append((check_obj.id, check_name, check_obj))
        # If specific IDs requested, include only matching checks
        elif check_obj.id in check_ids:
            result.append((check_obj.id, check_name, check_obj))
    
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
load_checks_from_yaml()

# Export main functions and loaded checks
__all__ = [
    'get_checks_by_ids',
    'get_loaded_checks', 
    'load_checks_from_yaml'
] 
