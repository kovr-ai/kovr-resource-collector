"""
Database operations for checks.

This module handles loading checks from the database and converting them
to Check model objects for use in the checks module.
"""

import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from con_mon.utils.db import get_db
from .models import Check, ComparisonOperation, ComparisonOperationEnum, CheckMetadata, CheckResultStatement, CheckFailureFix

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

    results = db.execute_query(select_sql)

    for row in results:
            # Convert database row to Check object
            check = _create_check_from_db_row(row)
            if check:
                loaded_checks[check.name] = check

    logger.info(f"✅ Loaded {len(loaded_checks)} checks from database")
    return loaded_checks


def _create_check_from_db_row(row: Dict[str, Any]) -> Optional[Check]:
    """
    Create a Check object from a database row.
    
    Args:
        row: Database row as dictionary
        
    Returns:
        Check object or None if creation fails
    """
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

    # Create nested objects with proper type conversion
    check_metadata = CheckMetadata(
        tags=metadata.get('tags', []),
        severity=metadata.get('severity'),
        category=metadata.get('category')
    )

    # Create output_statements object
    output_data = row.get('output_statements', {})
    if isinstance(output_data, dict) and output_data:
        try:
            output_statements = CheckResultStatement(**output_data)
        except Exception:
            # If data doesn't match expected structure, use default
            output_statements = CheckResultStatement(success="", failure="", partial="")
    else:
        output_statements = CheckResultStatement(success="", failure="", partial="")

    # Create fix_details object
    fix_data = row.get('fix_details', {})
    if isinstance(fix_data, dict) and fix_data:
        try:
            fix_details = CheckFailureFix(**fix_data)
        except Exception:
            # If data doesn't match expected structure, use default
            fix_details = CheckFailureFix(
                description="",
                instructions=[],
                estimated_date="",
                automation_available=False
            )
    else:
        fix_details = CheckFailureFix(
            description="",
            instructions=[],
            estimated_date="",
            automation_available=False
        )

    # Handle datetime conversion
    created_at = row.get('created_at')
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except Exception:
            created_at = datetime.now()
    elif not isinstance(created_at, datetime):
        created_at = datetime.now()

    updated_at = row.get('updated_at')
    if isinstance(updated_at, str):
        try:
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
        except Exception:
            updated_at = datetime.now()
    elif not isinstance(updated_at, datetime):
        updated_at = datetime.now()

    # Create Check object
    check = Check(
        id=row['id'],
        connection_id=connection_id,
        name=row['name'],
        field_path=field_path,
        operation=operation,
        expected_value=expected_value,
        description=row.get('description'),
        resource_type=resource_type,
        # Database-specific fields with proper type conversion
        output_statements=output_statements,
        fix_details=fix_details,
        created_by=row.get('created_by', 'system'),
        updated_by=row.get('updated_by', 'system'),
        created_at=created_at,
        updated_at=updated_at,
        is_deleted=row.get('is_deleted', False),
        metadata=check_metadata
    )

    return check


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
            # Safe execution environment with limited builtins
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'any': any,
                    'all': all,
                    'max': max,
                    'min': min,
                    'sum': sum,
                    'sorted': sorted,
                    'reversed': reversed,
                    'enumerate': enumerate,
                    'zip': zip,
                    'range': range,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'abs': abs,
                    'round': round,
                    'Exception': Exception,
                }
            }
            
            try:
                # Create a function template that will be executed
                function_template = """
def check_value(fetched_value, config_value):
    result = False
%s
    return result

result = check_value(fetched_value, config_value)
"""
                # Indent each line of custom logic by 4 spaces
                indented_logic = '\n'.join('    ' + line for line in custom_logic.split('\n'))
                
                # Create the complete function code
                function_code = function_template % indented_logic
                
                # Create local namespace with our variables
                local_ns = {
                    'fetched_value': fetched_value,
                    'config_value': config_value,
                    'expected_value': config_value,
                    'result': False
                }
                
                # Execute the function code in the local namespace
                exec(function_code, safe_globals, local_ns)
                
                # Get result from the local namespace
                return local_ns.get('result', False)
            except Exception as e:
                print(f"Custom logic that failed:\n{custom_logic}")
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

        # need to get models for resource_type pydantic class for resource on which this check is applicable
        if class_name in dynamic_models:
            return dynamic_models[class_name]
        else:
            logger.debug(f"⚠️ Resource type '{class_name}' not found in dynamic models")
            return None
            
    except Exception as e:
        logger.warning(f"⚠️ Could not resolve resource type '{resource_type_name}': {e}")
        return None


def get_checks_by_ids(
    loaded_checks: Dict[str, Check],
    check_ids: Optional[Union[List[int], int]] = None
) -> List[Tuple[int, str, Check]]:
    """
    Get checks by their IDs filtered by connection_id, or return all checks for connection if check_ids is None or empty list.
    
    Args:
        connection_id: Connection ID to filter by (1=GitHub, 2=AWS)
        loaded_checks: Dictionary of loaded checks
        check_ids: List of check IDs to filter by, single check ID, None or empty list to return all checks for connection
        
    Returns:
        List of tuples in format (check_id, check_name, check_object)
        
    Examples:
        # Get all checks
        all_checks = get_checks_by_ids(loaded_checks)
        all_checks = get_checks_by_ids(loaded_checks, None)
        all_checks = get_checks_by_ids(loaded_checks, [])
        
        # Get specific GitHub checks by ID
        selected_checks = get_checks_by_ids(loaded_checks, [1001, 1002])
        
        # Get single AWS check by ID
        single_aws_check = get_checks_by_ids(2, loaded_checks, 2001)
    """
    # Convert single int to list for consistent processing
    if isinstance(check_ids, int):
        check_ids = [check_ids]
    
    # Treat empty list the same as None (return all checks)
    if check_ids is not None and len(check_ids) == 0:
        check_ids = None
    
    # First filter by connection_id
    connection_checks = list(loaded_checks.values())
    
    # If no specific IDs requested, return all for connection
    if check_ids is None:
        filtered_checks = connection_checks
    else:
        # Filter by specific IDs
        filtered_checks = [
            check for check in connection_checks
            if check.id in check_ids
        ]
    
    # Convert to the expected tuple format
    result = [(check.id, check.name, check) for check in filtered_checks]
    
    # Sort by check ID for consistent ordering
    result.sort(key=lambda x: x[0])
    
    # Log what checks were returned
    if check_ids is None:
        logger.info(f"📋 Retrieved all {len(result)} available checks")
    else:
        found_ids = [check_id for check_id, _, _ in result]
        missing_ids = [cid for cid in check_ids if cid not in found_ids]
        
        logger.info(f"📋 Retrieved {len(result)} checks matching IDs: {found_ids}")
        if missing_ids:
            logger.warning(f"⚠️ Warning: check IDs not found: {missing_ids}")
    
    return result
