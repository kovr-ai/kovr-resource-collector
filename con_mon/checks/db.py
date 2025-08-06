"""
Database operations for checks.

This module handles loading checks from the database and converting them
to Check model objects for use in the checks module.
"""

import logging
from typing import List, Dict, Any, Optional
from con_mon.utils.db import get_db
from .models import Check, ComparisonOperation, ComparisonOperationEnum

logger = logging.getLogger(__name__)


def load_checks_from_database() -> Dict[str, Check]:
    """
    Load all active checks from the database and convert them to Check objects.
    
    Returns:
        Dictionary mapping check names to Check objects
    """
    db = get_db()
    loaded_checks = {}
    
    select_sql = """
    SELECT id, name, description, output_statements, fix_details,
           created_by, category, metadata, updated_by, created_at, updated_at, is_deleted
    FROM checks 
    WHERE is_deleted = false
    ORDER BY name;
    """
    
    try:
        results = db.execute_query(select_sql)
        
        for row in results:
            try:
                # Convert database row to Check object
                check = _create_check_from_db_row(row)
                if check:
                    loaded_checks[check.name] = check
                    
            except Exception as e:
                logger.error(f"❌ Failed to create check from row {row.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ Loaded {len(loaded_checks)} checks from database")
        return loaded_checks
        
    except Exception as e:
        logger.error(f"❌ Failed to load checks from database: {e}")
        return {}


def _create_check_from_db_row(row: Dict[str, Any]) -> Optional[Check]:
    """
    Create a Check object from a database row.
    
    Args:
        row: Database row as dictionary
        
    Returns:
        Check object or None if creation fails
    """
    try:
        # Extract metadata for execution fields
        metadata = row.get('metadata', {})
        
        # Get connection_id from metadata
        connection_id = metadata.get('connection_id', 1)
        
        # Get field_path from metadata
        field_path = metadata.get('field_path', 'data')
        
        # Create operation from metadata
        operation = _create_operation_from_metadata(metadata)
        
        # Get expected_value from metadata
        expected_value = metadata.get('expected_value')
        
        # Get resource_type from metadata
        resource_type = _resolve_resource_type(metadata.get('resource_type'))
        
        # Get control_ids from metadata (convert strings to ints if needed)
        control_ids = []
        metadata_control_ids = metadata.get('control_ids', [])
        for cid in metadata_control_ids:
            try:
                if isinstance(cid, str):
                    # Try to convert string control names to numeric IDs if possible
                    # For now, just use a hash or keep as 0
                    control_ids.append(hash(cid) % 10000)  # Simple hash to int
                else:
                    control_ids.append(int(cid))
            except (ValueError, TypeError):
                logger.warning(f"Could not convert control_id {cid} to int")
                continue
        
        # Create Check object
        check = Check(
            id=int(row['id']) if row['id'].isdigit() else hash(row['id']) % 100000,  # Convert string ID to int
            connection_id=connection_id,
            name=row['name'],
            field_path=field_path,
            operation=operation,
            expected_value=expected_value,
            description=row.get('description'),
            resource_type=resource_type,
            control_ids=control_ids,
            tags=metadata.get('tags', []),
            severity=metadata.get('severity'),
            category=row.get('category')
        )
        
        return check
        
    except Exception as e:
        logger.error(f"❌ Error creating check from database row: {e}")
        return None


def _create_operation_from_metadata(metadata: Dict[str, Any]) -> ComparisonOperation:
    """
    Create a ComparisonOperation from metadata.
    
    Args:
        metadata: Metadata dictionary containing operation info
        
    Returns:
        ComparisonOperation object
    """
    operation_data = metadata.get('operation', {})
    operation_name = operation_data.get('name', 'custom')
    custom_logic = operation_data.get('logic')  # Changed from 'custom_logic' to 'logic'
    
    # Map operation name to enum
    operation_enum = ComparisonOperationEnum.CUSTOM
    
    if operation_name in ['equal', '==']:
        operation_enum = ComparisonOperationEnum.EQUAL
    elif operation_name in ['not_equal', '!=']:
        operation_enum = ComparisonOperationEnum.NOT_EQUAL
    elif operation_name in ['less_than', '<']:
        operation_enum = ComparisonOperationEnum.LESS_THAN
    elif operation_name in ['greater_than', '>']:
        operation_enum = ComparisonOperationEnum.GREATER_THAN
    elif operation_name in ['less_than_or_equal', '<=']:
        operation_enum = ComparisonOperationEnum.LESS_THAN_OR_EQUAL
    elif operation_name in ['greater_than_or_equal', '>=']:
        operation_enum = ComparisonOperationEnum.GREATER_THAN_OR_EQUAL
    elif operation_name == 'contains':
        operation_enum = ComparisonOperationEnum.CONTAINS
    elif operation_name == 'not_contains':
        operation_enum = ComparisonOperationEnum.NOT_CONTAINS
    elif operation_name == 'custom':
        operation_enum = ComparisonOperationEnum.CUSTOM
    
    operation = ComparisonOperation(name=operation_enum)
    
    # Handle custom logic if present
    if operation_enum == ComparisonOperationEnum.CUSTOM and custom_logic:
        def custom_function(fetched_value, config_value):
            # Create local namespace for the custom logic
            local_vars = {
                'resource_data': fetched_value,  # Use resource_data as variable name
                'fetched_value': fetched_value,
                'config_value': config_value,
                'expected_value': config_value,
                'result': False  # Default result
            }
            
            # Safe execution environment
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'any': any,
                    'all': all,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                }
            }
            
            try:
                # Execute the custom logic code
                exec(custom_logic, safe_globals, local_vars)
                return local_vars.get('result', False)
            except Exception as e:
                logger.error(f"❌ Error in custom logic execution: {e}")
                return False
        
        operation.custom_function = custom_function
    
    return operation


def _resolve_resource_type(resource_type_name: Optional[str]):
    """
    Resolve resource type string to actual model type.
    
    Args:
        resource_type_name: String name of the resource type
        
    Returns:
        Resource type class or None
    """
    if not resource_type_name:
        return None
    
    try:
        # Handle different formats of resource type names
        # Format 1: "<class 'con_mon.resources.dynamic_models.AWSIAMResource'>"
        if resource_type_name.startswith("<class '") and resource_type_name.endswith("'>"):
            # Extract the class name from the string
            class_path = resource_type_name[8:-2]  # Remove "<class '" and "'>"
            if '.' in class_path:
                class_name = class_path.split('.')[-1]  # Get the last part
            else:
                class_name = class_path
        # Format 2: "AWSIAMResource" (just the class name)
        elif '.' not in resource_type_name and not resource_type_name.startswith('<'):
            class_name = resource_type_name
        # Format 3: "con_mon.resources.dynamic_models.AWSIAMResource"
        elif '.' in resource_type_name:
            class_name = resource_type_name.split('.')[-1]
        else:
            class_name = resource_type_name
        
        # Import dynamic models to get access to the generated classes
        from con_mon.resources.dynamic_models import get_dynamic_models
        dynamic_models = get_dynamic_models()
        
        if class_name in dynamic_models:
            return dynamic_models[class_name]
        else:
            logger.debug(f"⚠️ Resource type '{class_name}' not found in dynamic models")
            return None
            
    except Exception as e:
        logger.warning(f"⚠️ Could not resolve resource type '{resource_type_name}': {e}")
        return None


def get_checks_by_connection_id(connection_id: int, loaded_checks: Dict[str, Check]) -> List[Check]:
    """
    Filter loaded checks by connection ID.
    
    Args:
        connection_id: Connection ID to filter by
        loaded_checks: Dictionary of loaded checks
        
    Returns:
        List of checks matching the connection ID
    """
    return [
        check for check in loaded_checks.values() 
        if check.connection_id == connection_id
    ]


def get_checks_by_ids(
    connection_id: int,
    loaded_checks: Dict[str, Check],
    check_ids: Optional[List[int]] = None
) -> List[Check]:
    """
    Get checks by their IDs filtered by connection_id.
    
    Args:
        connection_id: Connection ID to filter by
        loaded_checks: Dictionary of loaded checks
        check_ids: List of check IDs to filter by, or None for all
        
    Returns:
        List of Check objects
    """
    # First filter by connection_id
    connection_checks = get_checks_by_connection_id(connection_id, loaded_checks)
    
    # If no specific IDs requested, return all for connection
    if check_ids is None or len(check_ids) == 0:
        return connection_checks
    
    # Filter by specific IDs
    return [
        check for check in connection_checks
        if check.id in check_ids
    ] 