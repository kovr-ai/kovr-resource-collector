"""
SQL operations for con_mon - handles SQL generation and file operations.
"""
import json
import os
from datetime import datetime
from typing import List, Tuple, Any


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_json_dumps(data, indent=None):
    """Safely serialize data to JSON, handling datetime objects"""
    return json.dumps(data, cls=DateTimeEncoder, indent=indent)


def insert_check_results(executed_check_results: List[Tuple[int, str, List[Any]]],
                        resource_collection: Any,
                        customer_id: str,
                        connection_id: int,
                        output_dir: str):
    """
    Generate and write SQL files from executed check results.
    
    Args:
        executed_check_results: List of (check_id, check_name, check_results) tuples
        resource_collection: ResourceCollection for resource_json field
        customer_id: Customer identifier for SQL records
        connection_id: Connection identifier for SQL records
        output_dir: Directory to write SQL files
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Get ResourceCollection as dict for resource_json
    if hasattr(resource_collection, 'model_dump'):
        resource_collection_dict = resource_collection.model_dump()
    elif hasattr(resource_collection, 'dict'):
        resource_collection_dict = resource_collection.dict()
    else:
        resource_collection_dict = resource_collection.__dict__
    
    all_sql_statements = []
    
    for check_id, check_name, check_results in executed_check_results:
        # Count successes and failures
        success_count = sum(1 for result in check_results if result.passed)
        failure_count = sum(1 for result in check_results if not result.passed)
        total_count = len(check_results)
        success_percentage = int((success_count / total_count * 100)) if total_count > 0 else 0
        
        # Collect full Resource objects (as dicts)
        success_resources = []
        failed_resources = []
        
        for result in check_results:
            if hasattr(result.resource, 'model_dump'):
                resource_dict = result.resource.model_dump()
            elif hasattr(result.resource, 'dict'):
                resource_dict = result.resource.dict()
            else:
                resource_dict = result.resource.__dict__
                
            if result.passed:
                success_resources.append(resource_dict)
            else:
                failed_resources.append(resource_dict)
        
        # Determine overall result
        if failure_count == 0:
            overall_result = 'PASS'
            result_message = f"Check '{check_name}' passed for all {success_count} resources"
        elif success_count == 0:
            overall_result = 'FAIL'  
            result_message = f"Check '{check_name}' failed for all {failure_count} resources"
        else:
            overall_result = 'MIXED'
            result_message = f"Check '{check_name}' passed for {success_count} resources, failed for {failure_count} resources"
        
        # Add detailed failure messages
        failure_details = []
        if failure_count > 0:
            for result in check_results:
                if not result.passed:
                    failure_details.append({
                        'resource_id': result.resource.id,
                        'resource_name': result.resource.name,
                        'message': result.message
                    })
            result_message += f". Failures: {'; '.join([f'{fd['resource_name']}: {fd['message']}' for fd in failure_details])}"
        
        # Generate SQL INSERT statement
        sql = f"""-- GitHub Check Results for {check_name}
-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Result: {overall_result} ({success_count} passed, {failure_count} failed)

INSERT INTO con_mon_results (
    customer_id, connection_id, check_id, result, result_message,
    success_count, failure_count, success_percentage,
    success_resources, failed_resources, exclusions, resource_json
) VALUES (
    '{customer_id}', {connection_id}, {check_id}, '{overall_result}',
    '{result_message.replace("'", "''")}',
    {success_count}, {failure_count}, {success_percentage},
    '{safe_json_dumps(success_resources, indent=2).replace("'", "''")}'::jsonb,
    '{safe_json_dumps(failed_resources, indent=2).replace("'", "''")}'::jsonb,
    '[]'::jsonb,
    '{safe_json_dumps(resource_collection_dict, indent=2).replace("'", "''")}'::jsonb
);
"""
        
        all_sql_statements.append(sql)
    
    # Write single combined SQL file
    combined_sql = f"""-- Combined GitHub Check Results
-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Total checks: {len(executed_check_results)}

{chr(10).join(all_sql_statements)}
"""
    
    sql_filepath = os.path.join(output_dir, f"github_checks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    with open(sql_filepath, 'w') as f:
        f.write(combined_sql)
    
    # Print file generation summary
    print(f"\n📁 **Generated Files:**")
    print(f"   • SQL file: {sql_filepath}")
    print(f"   • Output directory: {output_dir}/")
    print(f"   • Contains {len(executed_check_results)} check results")
