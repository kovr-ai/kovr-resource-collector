#!/usr/bin/env python3
"""
Generate Compliance Checks with LLM

This script demonstrates how to use the new LLM sub-module structure
to generate compliance checks from NIST control data.

Usage:
    python generate_checks_with_llm.py --control AC-2 --resource-type github
    python generate_checks_with_llm.py --analyze --control AC-3
"""

import argparse
import logging
from typing import Dict, Any, Optional

from con_mon.utils.llm import (
    get_llm_client,
    generate_compliance_check,
    analyze_control,
    generate_checks_yaml
)
from con_mon.utils.db import get_db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_control_from_db(control_name: str) -> Dict[str, Any]:
    """
    Get control information from the database.
    
    Args:
        control_name: Control identifier (e.g., "AC-2")
        
    Returns:
        Dictionary containing control information
    """
    db = get_db()
    
    # Query for NIST 800-53 controls (framework_id = 2)
    query = """
    SELECT 
        id,
        control_name,
        control_long_name,
        control_text,
        control_discussion,
        family_name
    FROM control 
    WHERE control_name = %s
    LIMIT 1;
    """
    
    try:
        results = db.execute_query(query, (control_name,))
        if results:
            return results[0]
        else:
            logger.error(f"Control {control_name} not found in database")
            return {}
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {}


def call_llm_for_check(
    control_name: str,
    control_data: Dict[str, Any],
    resource_type: str,
    connection_id: int
) -> str:
    """
    Call LLM to generate check YAML content.
    
    Args:
        control_name: Control identifier
        control_data: Control information from database
        resource_type: Target resource type
        connection_id: Connection ID for the check
        
    Returns:
        Generated YAML content from LLM
    """
    print(f"🤖 Calling LLM to generate check for {control_name}...")
    
    try:
        yaml_content = generate_checks_yaml(
            control_name=control_name,
            control_text=control_data['control_text'],
            control_title=control_data['control_long_name'],
            resource_type=resource_type,
            connection_id=connection_id,
            control_id=control_data['id'],
            max_tokens=1200,
            temperature=0.1
        )
        
        print(f"✅ LLM generated {len(yaml_content)} characters of YAML")
        return yaml_content
        
    except Exception as e:
        logger.error(f"Failed to call LLM: {e}")
        return ""


def process_response_to_check(
    yaml_content: str,
    control_name: str,
    control_data: Dict[str, Any],
    resource_type: str = "github",
    connection_id: int = 1
) -> Optional['Check']:
    """
    Process LLM YAML response and create a Check object.
    
    Args:
        yaml_content: YAML content from LLM
        control_name: Control identifier
        control_data: Control information from database
        resource_type: Target resource type
        connection_id: Connection ID for the check
        
    Returns:
        Check object or None if processing fails
    """
    print(f"🔄 Processing LLM response to create Check object...")
    
    if not yaml_content:
        logger.error("Empty YAML content provided")
        return None
    
    try:
        import yaml
        from datetime import datetime
        from con_mon.checks.models import Check, ComparisonOperation, ComparisonOperationEnum
        from con_mon.checks.models import CheckMetadata, CheckResultStatement, CheckFailureFix
        
        # Parse the generated YAML
        yaml_data = yaml.safe_load(yaml_content)
        
        # Extract check data
        if isinstance(yaml_data, dict) and 'checks' in yaml_data:
            checks_list = yaml_data['checks']
            if isinstance(checks_list, list) and len(checks_list) > 0:
                check_data = checks_list[0]
            else:
                logger.error("No checks found in YAML data")
                return None
        elif isinstance(yaml_data, dict):
            check_data = yaml_data
        elif isinstance(yaml_data, list) and len(yaml_data) > 0:
            check_data = yaml_data[0]
        else:
            logger.error("Could not parse YAML structure")
            return None
        
        # Create ComparisonOperation
        operation_data = check_data.get("operation", {})
        operation_name = operation_data.get("name", "custom")
        custom_logic = operation_data.get("custom_logic", "")
        
        # Map to enum
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
        
        operation = ComparisonOperation(name=operation_enum)
        
        # Store the original custom logic code as an attribute for later retrieval
        operation._original_custom_logic = custom_logic
        
        # Handle custom logic if present
        if operation_enum == ComparisonOperationEnum.CUSTOM and custom_logic:
            def custom_function(fetched_value, config_value):
                local_vars = {
                    'resource_data': fetched_value,
                    'fetched_value': fetched_value,
                    'config_value': config_value,
                    'expected_value': config_value,
                    'result': False
                }
                safe_globals = {
                    '__builtins__': {
                        'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                        'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'any': any,
                        'all': all, 'max': max, 'min': min, 'sum': sum, 'sorted': sorted,
                        'reversed': reversed, 'enumerate': enumerate, 'zip': zip, 'range': range,
                        'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
                        'abs': abs, 'round': round, 'Exception': Exception,
                    }
                }
                try:
                    exec(custom_logic, safe_globals, local_vars)
                    return local_vars.get('result', False)
                except Exception as e:
                    logger.error(f"Error in custom logic execution: {e}")
                    return False
            
            operation.custom_function = custom_function
        
        # Create nested objects
        check_metadata = CheckMetadata(
            tags=check_data.get("tags", []),
            severity=check_data.get("severity", "medium"),
            category=check_data.get("category", "compliance")
        )
        
        # Create output_statements
        output_data = check_data.get("output_statements", {})
        if isinstance(output_data, dict) and output_data:
            output_statements = CheckResultStatement(
                success=output_data.get("success") or "Check passed successfully",
                failure=output_data.get("failure") or "Check failed",
                partial=output_data.get("partial") or "Check partially passed"
            )
        else:
            output_statements = CheckResultStatement(
                success="Check passed successfully",
                failure="Check failed", 
                partial="Check partially passed"
            )
        
        # Create fix_details
        fix_data = check_data.get("fix_details", {})
        if isinstance(fix_data, dict) and fix_data:
            # Handle date conversion if needed
            estimated_date = fix_data.get("estimated_date", "2024-12-31")
            if hasattr(estimated_date, 'strftime'):  # It's a date/datetime object
                estimated_date = estimated_date.strftime("%Y-%m-%d")
            elif not isinstance(estimated_date, str):
                estimated_date = str(estimated_date)
            
            # Handle instructions - ensure it's a list
            instructions = fix_data.get("instructions", ["Review the failed check", "Implement necessary changes"])
            if isinstance(instructions, str):
                # If it's a string like "List[str]", use default
                if instructions in ["List[str]", "list", "List"]:
                    instructions = ["Review the failed check", "Implement necessary changes"]
                else:
                    # Split string into list if it contains actual instructions
                    instructions = [instructions]
            elif not isinstance(instructions, list):
                instructions = ["Review the failed check", "Implement necessary changes"]
            
            # Handle automation_available - ensure it's a boolean
            automation_available = fix_data.get("automation_available", False)
            if isinstance(automation_available, str):
                # Handle string representations
                if automation_available.lower() in ["true", "yes", "1"]:
                    automation_available = True
                elif automation_available.lower() in ["false", "no", "0", "bool = false"]:
                    automation_available = False
                else:
                    automation_available = False
            elif not isinstance(automation_available, bool):
                automation_available = bool(automation_available) if automation_available else False
            
            fix_details = CheckFailureFix(
                description=fix_data.get("description", f"Fix for {control_name} compliance check"),
                instructions=instructions,
                estimated_date=estimated_date,
                automation_available=automation_available
            )
        else:
            fix_details = CheckFailureFix(
                description=f"Fix for {control_name} compliance check",
                instructions=["Review the failed check", "Implement necessary changes"],
                estimated_date="2024-12-31",
                automation_available=False
            )
        
        # Resolve resource type
        resource_type_class = None
        try:
            from con_mon.resources.dynamic_models import get_dynamic_models
            dynamic_models = get_dynamic_models()
            
            # Try to get the resource type from the YAML data first
            yaml_resource_type = check_data.get("resource_type")
            if yaml_resource_type and yaml_resource_type in dynamic_models:
                resource_type_class = dynamic_models[yaml_resource_type]
            else:
                # Fallback: try to construct resource type name
                if resource_type.lower() == "github":
                    resource_class_name = "GithubResource"
                elif resource_type.lower() == "aws":
                    # For AWS, we need to infer the service type from field_path
                    field_path = check_data.get("field_path", "")
                    if field_path in ["policies", "users", "roles", "groups"]:
                        resource_class_name = "AWSIAMResource"
                    elif field_path in ["instances", "security_groups", "vpcs", "subnets"]:
                        resource_class_name = "AWSEC2Resource"
                    elif field_path in ["buckets", "bucket_policies", "bucket_encryption"]:
                        resource_class_name = "AWSS3Resource"
                    elif field_path in ["trails", "event_selectors"]:
                        resource_class_name = "AWSCloudTrailResource"
                    elif field_path in ["dashboards", "alarms", "log_groups", "metrics"]:
                        resource_class_name = "AWSCloudWatchResource"
                    else:
                        resource_class_name = "AWSIAMResource"  # Default fallback for AWS
                else:
                    resource_class_name = f"{resource_type.title()}Resource"
                
                resource_type_class = dynamic_models.get(resource_class_name)
                
        except Exception as e:
            logger.warning(f"Could not resolve resource type: {e}")
            try:
                dynamic_models = get_dynamic_models()
                if resource_type.lower() == "github":
                    resource_type_class = dynamic_models.get("GithubResource")
                elif resource_type.lower() == "aws":
                    resource_type_class = dynamic_models.get("AWSIAMResource")
            except:
                pass
        
        # Create Check object
        check = Check(
            id=check_data.get("id", 1000 + control_data['id']),
            connection_id=connection_id,
            name=check_data.get("name", f"{control_name.lower()}_compliance_check"),
            field_path=check_data.get("field_path", "data"),
            operation=operation,
            expected_value=check_data.get("expected_value"),
            description=check_data.get("description", f"Compliance check for {control_name}"),
            resource_type=resource_type_class,
            output_statements=output_statements,
            fix_details=fix_details,
            created_by="llm_generator",
            updated_by="llm_generator",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
            metadata=check_metadata
        )
        
        print(f"✅ Created Check object: {check.name}")
        return check
        
    except Exception as e:
        logger.error(f"Failed to process YAML to Check object: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_sql_from_check(check: 'Check', control_id: int) -> str:
    """
    Generate SQL INSERT queries for a Check object.
    
    Args:
        check: Check object to convert to SQL
        control_id: Database ID of the control for mapping
        
    Returns:
        SQL INSERT queries for checks and control_checks_mapping tables
    """
    print(f"📝 Generating SQL for check: {check.name}")
    
    try:
        import json
        from datetime import datetime
        
        # Convert nested objects to JSON
        output_statements_json = json.dumps({
            "success": check.output_statements.success,
            "failure": check.output_statements.failure,
            "partial": check.output_statements.partial
        })
        
        fix_details_json = json.dumps({
            "description": check.fix_details.description,
            "instructions": check.fix_details.instructions,
            "estimated_date": check.fix_details.estimated_date,
            "automation_available": check.fix_details.automation_available
        })
        
        # Build metadata JSON
        metadata_json = json.dumps({
            "connection_id": check.connection_id,
            "field_path": check.field_path,
            "expected_value": check.expected_value,
            "resource_type": f"<class 'con_mon.resources.dynamic_models.{check.resource_type.__name__}'>" if check.resource_type else None,
            "tags": check.metadata.tags,
            "severity": check.metadata.severity,
            "category": check.metadata.category,
            "operation": {
                "name": check.operation.name.value,
                "logic": getattr(check.operation, '_original_custom_logic', '') or ""
            }
        })
        
        # Generate timestamps
        current_time = datetime.now().isoformat()
        
        # Escape single quotes in strings for SQL
        def escape_sql_string(s):
            return s.replace("'", "''") if isinstance(s, str) else s
        
        check_name = escape_sql_string(check.name)
        check_description = escape_sql_string(check.description or "")
        
        # Generate SQL INSERT queries with auto-incrementing ID
        sql_query = f"""-- Insert the check and get the generated ID
INSERT INTO checks (
    name, 
    description, 
    output_statements, 
    fix_details,
    created_by, 
    updated_by, 
    category, 
    metadata, 
    created_at, 
    updated_at, 
    is_deleted
) VALUES (
    '{check_name}',
    '{check_description}',
    '{output_statements_json}',
    '{fix_details_json}',
    '{escape_sql_string(check.created_by)}',
    '{escape_sql_string(check.updated_by)}',
    '{escape_sql_string(check.metadata.category)}',
    '{metadata_json}',
    '{current_time}',
    '{current_time}',
    {str(check.is_deleted).lower()}
) RETURNING id;

-- Note: After executing the above query, use the returned ID for the mapping
-- INSERT INTO control_checks_mapping (
--     control_id,
--     check_id,
--     created_at,
--     updated_at,
--     is_deleted
-- ) VALUES (
--     {control_id},
--     <returned_check_id>,
--     '{current_time}',
--     '{current_time}',
--     false
-- );"""
        
        print(f"✅ Generated SQL INSERT queries with auto-incrementing ID")
        return sql_query
        
    except Exception as e:
        logger.error(f"Failed to generate SQL from Check object: {e}")
        import traceback
        traceback.print_exc()
        return ""


def validate_check_execution(
    check: 'Check',
    resource_type: str
) -> Dict[str, Any]:
    """
    Validate that the generated check can execute without errors.
    
    Args:
        check: Check object to validate
        resource_type: Type of resource (github, aws)
        
    Returns:
        Dictionary with validation results
    """
    print(f"🧪 Validating check execution for: {check.name}")
    
    validation_result = {
        "success": False,
        "error": None,
        "execution_result": None,
        "resource_created": False,
        "logic_extracted": False,
        "sample_data_loaded": False
    }
    
    try:
        # Step 1: Extract custom logic code
        if not hasattr(check.operation, '_original_custom_logic') or not check.operation._original_custom_logic:
            validation_result["error"] = "No custom logic found in check operation"
            return validation_result
        
        custom_logic = check.operation._original_custom_logic
        validation_result["logic_extracted"] = True
        print(f"✅ Extracted custom logic ({len(custom_logic)} characters)")
        
        # Step 2: Load sample data based on resource type
        sample_data = None
        if resource_type.lower() == "github":
            try:
                import json
                with open("github_response.json", "r") as f:
                    github_data = json.load(f)
                
                # Extract first repository data as sample
                if "repositories_data" in github_data and len(github_data["repositories_data"]) > 0:
                    sample_data = github_data["repositories_data"][0]
                    validation_result["sample_data_loaded"] = True
                    print(f"✅ Loaded GitHub sample data for repository: {sample_data.get('repository', 'unknown')}")
                else:
                    validation_result["error"] = "No repository data found in github_response.json"
                    return validation_result
                    
            except FileNotFoundError:
                validation_result["error"] = "github_response.json not found"
                return validation_result
            except json.JSONDecodeError as e:
                validation_result["error"] = f"Failed to parse github_response.json: {e}"
                return validation_result
                
        elif resource_type.lower() == "aws":
            try:
                import json
                with open("aws_response.json", "r") as f:
                    aws_data = json.load(f)
                
                # Extract the appropriate AWS service data based on field_path
                field_path = check.field_path
                region_data = None
                
                # Find first region data
                for region_name, region_info in aws_data.items():
                    if isinstance(region_info, dict) and "iam" in region_info:
                        region_data = region_info
                        break
                
                if not region_data:
                    validation_result["error"] = "No AWS region data found in aws_response.json"
                    return validation_result
                
                # Select appropriate service data based on field_path
                if field_path in ["policies", "users", "roles", "groups"]:
                    sample_data = region_data.get("iam", {})
                elif field_path in ["instances", "security_groups", "vpcs", "subnets"]:
                    sample_data = region_data.get("ec2", {})
                elif field_path in ["buckets", "bucket_policies", "bucket_encryption"]:
                    sample_data = region_data.get("s3", {})
                elif field_path in ["trails", "event_selectors"]:
                    sample_data = region_data.get("cloudtrail", {})
                elif field_path in ["dashboards", "alarms", "log_groups", "metrics"]:
                    sample_data = region_data.get("cloudwatch", {})
                else:
                    # Default to IAM if field_path doesn't match
                    sample_data = region_data.get("iam", {})
                
                if sample_data:
                    validation_result["sample_data_loaded"] = True
                    print(f"✅ Loaded AWS sample data for service with field: {field_path}")
                else:
                    validation_result["error"] = f"No AWS data found for field_path: {field_path}"
                    return validation_result
                    
            except FileNotFoundError:
                validation_result["error"] = "aws_response.json not found"
                return validation_result
            except json.JSONDecodeError as e:
                validation_result["error"] = f"Failed to parse aws_response.json: {e}"
                return validation_result
        else:
            validation_result["error"] = f"Unsupported resource type: {resource_type}"
            return validation_result
        
        # Step 3: Create resource object using dynamic models
        try:
            from con_mon.resources.dynamic_models import get_dynamic_models
            dynamic_models = get_dynamic_models()
            
            resource_class = check.resource_type
            if not resource_class:
                validation_result["error"] = "No resource type class found in check"
                return validation_result
            
            # Create resource instance with sample data
            if resource_type.lower() == "github":
                # For GitHub, we need to structure the data properly
                # Use the actual repository ID from basic_info if available, otherwise use repository name
                repo_name = sample_data.get("repository", "test-repo")
                basic_info = sample_data.get("basic_info", {})
                repo_id = str(basic_info.get("id", repo_name))  # Convert to string as required
                
                resource_instance = resource_class(
                    id=repo_id,  # Use actual repository ID
                    source_connector="github",
                    name=repo_name,
                    repository_data=basic_info,
                    actions_data=sample_data.get("actions_data", {}),
                    collaboration_data=sample_data.get("collaboration_data", {}),
                    security_data=sample_data.get("security_data", {}),
                    organization_data=sample_data.get("organization_data", {}),
                    advanced_features_data=sample_data.get("advanced_features_data", {})
                )
            else:
                # For AWS, create with the service-specific data
                # Try to extract a meaningful ID from the service data
                aws_id = "aws-resource"
                
                # Look for account information in the sample data
                if "account" in sample_data:
                    account_data = sample_data["account"]
                    if isinstance(account_data, dict):
                        # Try various account ID fields
                        aws_id = account_data.get("account_id") or account_data.get("AccountId") or aws_id
                
                # If no account ID found, try to use the first key from a major resource collection
                if aws_id == "aws-resource":
                    for key in ["users", "policies", "instances", "buckets", "trails"]:
                        if key in sample_data and isinstance(sample_data[key], dict) and sample_data[key]:
                            # Use the first resource key as identifier
                            first_resource_key = list(sample_data[key].keys())[0]
                            aws_id = f"aws-{key}-{first_resource_key[:20]}"  # Truncate if too long
                            break
                
                resource_instance = resource_class(
                    id=str(aws_id),  # Ensure it's a string
                    source_connector="aws",
                    **sample_data
                )
            
            validation_result["resource_created"] = True
            print(f"✅ Created {resource_class.__name__} instance")
            
        except Exception as e:
            validation_result["error"] = f"Failed to create resource instance: {e}"
            return validation_result
        
        # Step 4: Extract field value using field_path
        try:
            field_path = check.field_path
            field_parts = field_path.split('.')
            
            # Navigate through the resource to get the field value
            current_value = resource_instance
            for part in field_parts:
                if hasattr(current_value, part):
                    current_value = getattr(current_value, part)
                elif isinstance(current_value, dict) and part in current_value:
                    current_value = current_value[part]
                else:
                    validation_result["error"] = f"Field path '{field_path}' not found in resource. Failed at part: '{part}'"
                    return validation_result
            
            fetched_value = current_value
            print(f"✅ Extracted field value from path: {field_path}")
            
        except Exception as e:
            validation_result["error"] = f"Failed to extract field value: {e}"
            return validation_result
        
        # Step 5: Execute the custom logic
        try:
            # Set up execution environment
            local_vars = {
                'resource_data': fetched_value,
                'fetched_value': fetched_value,
                'config_value': check.expected_value,
                'expected_value': check.expected_value,
                'result': False
            }
            
            safe_globals = {
                '__builtins__': {
                    'len': len, 'str': str, 'int': int, 'float': float, 'bool': bool,
                    'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'any': any,
                    'all': all, 'max': max, 'min': min, 'sum': sum, 'sorted': sorted,
                    'reversed': reversed, 'enumerate': enumerate, 'zip': zip, 'range': range,
                    'isinstance': isinstance, 'hasattr': hasattr, 'getattr': getattr,
                    'abs': abs, 'round': round, 'Exception': Exception,
                }
            }
            
            # Execute the custom logic
            exec(custom_logic, safe_globals, local_vars)
            
            execution_result = local_vars.get('result', False)
            validation_result["execution_result"] = execution_result
            validation_result["success"] = True
            
            print(f"✅ Check executed successfully. Result: {execution_result}")
            print(f"📊 Field value type: {type(fetched_value).__name__}")
            if isinstance(fetched_value, (dict, list)):
                print(f"📊 Field value size: {len(fetched_value)}")
            
        except Exception as e:
            validation_result["error"] = f"Failed to execute custom logic: {e}"
            print(f"❌ Execution error: {e}")
            print(f"🐍 Custom logic:\n{custom_logic}")
            return validation_result
        
        return validation_result
        
    except Exception as e:
        validation_result["error"] = f"Validation failed with unexpected error: {e}"
        return validation_result


def generate_sql_check_for_control(
    control_name: str, 
    resource_type: str,
    connection_id: int,
    validate_execution: bool = True
) -> str:
    """
    Main function that orchestrates the three-step process with optional validation.
    
    Args:
        control_name: Control identifier
        resource_type: Target resource type
        connection_id: Connection ID for the check
        validate_execution: Whether to validate the check execution (default: True)
        
    Returns:
        Generated SQL INSERT queries
    """
    print(f"🔍 Fetching control data for {control_name}...")
    
    # Get control from database
    control_data = get_control_from_db(control_name)
    if not control_data:
        return ""
    
    print(f"📋 Control: {control_data['control_long_name']}")
    print(f"🏷️ Family: {control_data['family_name']}")
    
    # Step 1: Call LLM
    yaml_content = call_llm_for_check(
        control_name=control_name,
        control_data=control_data,
        resource_type=resource_type,
        connection_id=connection_id,
    )
    
    if not yaml_content:
        return ""
    
    # Step 2: Process response to Check object
    check = process_response_to_check(
        yaml_content=yaml_content,
        control_name=control_name,
        control_data=control_data,
        resource_type=resource_type,
        connection_id=connection_id
    )
    
    if not check:
        return ""
    
    # Step 3: Validate check execution (optional)
    if validate_execution:
        print(f"🧪 Validating check execution...")
        validation_result = validate_check_execution(check, resource_type)
        
        if validation_result["success"]:
            print(f"✅ Check validation passed!")
            print(f"📊 Execution result: {validation_result['execution_result']}")
        else:
            print(f"❌ Check validation failed: {validation_result['error']}")
            print(f"📋 Validation details:")
            print(f"   • Logic extracted: {validation_result['logic_extracted']}")
            print(f"   • Sample data loaded: {validation_result['sample_data_loaded']}")
            print(f"   • Resource created: {validation_result['resource_created']}")
            
            # Still generate SQL even if validation fails, but warn the user
            print(f"⚠️  Continuing with SQL generation despite validation failure...")
    
    # Step 4: Generate SQL from Check object
    sql_query = generate_sql_from_check(check, control_data['id'])
    
    return sql_query


def generate_check_for_control(control_name: str, resource_type: str = "github") -> str:
    """
    Generate compliance check code for a control.
    
    Args:
        control_name: Control identifier
        resource_type: Target resource type
        
    Returns:
        Generated Python code
    """
    print(f"🔍 Fetching control data for {control_name}...")
    
    # Get control from database
    control_data = get_control_from_db(control_name)
    if not control_data:
        return ""
    
    print(f"📋 Control: {control_data['control_long_name']}")
    print(f"🏷️ Family: {control_data['family_name']}")
    
    # Generate compliance check
    print(f"🤖 Generating compliance check code...")
    
    try:
        code = generate_compliance_check(
            control_name=control_name,
            control_text=control_data['control_text'],
            resource_type=resource_type,
            control_title=control_data['control_long_name'],
            max_tokens=800,
            temperature=0.1
        )
        
        print(f"✅ Generated {len(code)} characters of code")
        return code
        
    except Exception as e:
        logger.error(f"Failed to generate compliance check: {e}")
        return ""


def analyze_control_requirements(control_name: str) -> Dict[str, Any]:
    """
    Analyze control requirements for automation feasibility.
    
    Args:
        control_name: Control identifier
        
    Returns:
        Analysis results
    """
    print(f"🔍 Fetching control data for {control_name}...")
    
    # Get control from database
    control_data = get_control_from_db(control_name)
    if not control_data:
        return {}
    
    print(f"📋 Control: {control_data['control_long_name']}")
    print(f"🏷️ Family: {control_data['family_name']}")
    
    # Analyze control
    print(f"🔬 Analyzing control requirements...")
    
    try:
        analysis = analyze_control(
            control_name=control_name,
            control_text=control_data['control_text'],
            control_title=control_data['control_long_name'],
            max_tokens=1000,
            temperature=0.2
        )
        
        print(f"✅ Analysis completed")
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze control: {e}")
        return {}


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate compliance checks with LLM")
    parser.add_argument("--control", required=True, help="Control name (e.g., AC-2)")
    parser.add_argument("--resource-type", default="github", 
                       choices=["github", "aws", "azure", "gcp"],
                       help="Target resource type")
    parser.add_argument("--analyze", action="store_true", 
                       help="Analyze control instead of generating code")
    parser.add_argument("--yaml", action="store_true",
                       help="Generate SQL INSERT query for database instead of just code")
    parser.add_argument("--connection-id", type=int, default=1,
                       help="Connection ID for the check (default: 1)")
    parser.add_argument("--check-id", type=int,
                       help="Suggested check ID (auto-generated if not provided)")
    parser.add_argument("--validate", action="store_true", default=True,
                       help="Validate check execution against sample data (default: True)")
    parser.add_argument("--no-validate", action="store_false", dest="validate",
                       help="Skip check execution validation")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    print("🚀 LLM-Powered Compliance Check Generator")
    print("=" * 60)
    
    # Test LLM connection first
    try:
        client = get_llm_client()
        if not client.test_connection():
            print("❌ LLM connection test failed. Please check your AWS configuration.")
            return 1
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        return 1
    
    if args.analyze:
        # Analyze control
        analysis = analyze_control_requirements(args.control)
        
        if analysis:
            print("\n📊 Analysis Results:")
            print("-" * 40)
            print(f"Automation Feasibility: {analysis.get('automation_feasibility', 'unknown').upper()}")
            print(f"Implementation Complexity: {analysis.get('implementation_complexity', 'unknown').upper()}")
            print(f"Resource Types: {', '.join(analysis.get('resource_types', []))}")
            
            if analysis.get('key_requirements'):
                print("\nKey Requirements:")
                for req in analysis['key_requirements']:
                    print(f"  • {req}")
            
            if analysis.get('suggested_checks'):
                print("\nSuggested Automated Checks:")
                for check in analysis['suggested_checks']:
                    print(f"  • {check}")
            
            # Save to file if requested
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(analysis, f, indent=2)
                print(f"\n💾 Analysis saved to {args.output}")
    
    elif args.yaml:
        # Generate complete SQL check
        sql_query = generate_sql_check_for_control(
            args.control, 
            args.resource_type,
            args.connection_id,
            args.validate
        )
        
        if sql_query:
            print("\n📄 Generated SQL Check Entry:")
            print("-" * 40)
            print(sql_query)
            
            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(sql_query)
                print(f"\n💾 SQL saved to {args.output}")
        
    else:
        # Generate compliance check code only
        code = generate_check_for_control(args.control, args.resource_type)
        
        if code:
            print("\n🐍 Generated Python Code:")
            print("-" * 40)
            print(code)
            
            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(code)
                print(f"\n💾 Code saved to {args.output}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 