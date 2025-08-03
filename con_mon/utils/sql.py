"""
SQL operations for con_mon - handles SQL generation and file operations.
"""
import json
import os
from datetime import datetime
from typing import List, Tuple, Any, Optional


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
                        output_dir: Optional[str] = None):
    """
    Generate and write SQL files or insert directly into database from executed check results.
    
    Args:
        executed_check_results: List of (check_id, check_name, check_results) tuples
        resource_collection: ResourceCollection for resource_json field
        customer_id: Customer identifier for SQL records
        connection_id: Connection identifier for SQL records
        output_dir: Directory to write SQL files. If None, insert directly into database.
    """
    
    # Get ResourceCollection as dict for resource_json
    if hasattr(resource_collection, 'model_dump'):
        resource_collection_dict = resource_collection.model_dump()
    elif hasattr(resource_collection, 'dict'):
        resource_collection_dict = resource_collection.dict()
    else:
        resource_collection_dict = resource_collection.__dict__
    
    # Process each check result
    processed_results = []
    
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
        
        # Store processed result
        processed_results.append({
            'check_id': check_id,
            'check_name': check_name,
            'overall_result': overall_result,
            'result_message': result_message,
            'success_count': success_count,
            'failure_count': failure_count,
            'success_percentage': success_percentage,
            'success_resources': success_resources,
            'failed_resources': failed_resources,
            'resource_collection_dict': resource_collection_dict
        })
    
    # Choose output method based on output_dir parameter
    if output_dir is not None:
        # Generate SQL files
        _generate_sql_files(processed_results, customer_id, connection_id, output_dir)
    else:
        # Insert directly into database
        _insert_into_database(processed_results, customer_id, connection_id)


def _generate_sql_files(processed_results: List[dict], customer_id: str, connection_id: int, output_dir: str):
    """Generate SQL files from processed check results."""
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    all_sql_statements = []
    
    for result in processed_results:
        # Generate SQL INSERT statement
        sql = f"""-- GitHub Check Results for {result['check_name']}
-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Result: {result['overall_result']} ({result['success_count']} passed, {result['failure_count']} failed)

INSERT INTO con_mon_results (
    customer_id, connection_id, check_id, result, result_message,
    success_count, failure_count, success_percentage,
    success_resources, failed_resources, exclusions, resource_json
) VALUES (
    '{customer_id}', {connection_id}, {result['check_id']}, '{result['overall_result']}',
    '{result['result_message'].replace("'", "''")}',
    {result['success_count']}, {result['failure_count']}, {result['success_percentage']},
    '{safe_json_dumps(result['success_resources'], indent=2).replace("'", "''")}'::jsonb,
    '{safe_json_dumps(result['failed_resources'], indent=2).replace("'", "''")}'::jsonb,
    '[]'::jsonb,
    '{safe_json_dumps(result['resource_collection_dict'], indent=2).replace("'", "''")}'::jsonb
);
"""
        
        all_sql_statements.append(sql)
    
    # Write single combined SQL file
    combined_sql = f"""-- Combined GitHub Check Results
-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Total checks: {len(processed_results)}

{chr(10).join(all_sql_statements)}
"""
    
    sql_filepath = os.path.join(output_dir, f"github_checks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql")
    with open(sql_filepath, 'w') as f:
        f.write(combined_sql)
    
    # Print file generation summary
    print(f"\n📁 **Generated Files:**")
    print(f"   • SQL file: {sql_filepath}")
    print(f"   • Output directory: {output_dir}/")
    print(f"   • Contains {len(processed_results)} check results")


def _insert_into_database(processed_results: List[dict], customer_id: str, connection_id: int):
    """Insert check results directly into the database."""
    from .db import get_db
    
    database = get_db()
    
    if not database._connection_pool:
        print("❌ Database connection not available. Cannot insert check results.")
        print("💡 Consider providing output_dir parameter to generate SQL files instead.")
        return
    
    print(f"\n💾 **Inserting into Database:**")
    print(f"   • Database: {database._connection_pool._kwargs.get('database', 'unknown')}")
    print(f"   • Host: {database._connection_pool._kwargs.get('host', 'unknown')}")
    
    insert_sql = """
    INSERT INTO con_mon_results (
        customer_id, connection_id, check_id, result, result_message,
        success_count, failure_count, success_percentage,
        success_resources, failed_resources, exclusions, resource_json
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    ) RETURNING id;
    """
    
    inserted_count = 0
    failed_count = 0
    
    for result in processed_results:
        try:
            # Prepare parameters for parameterized query
            params = (
                customer_id,
                connection_id,
                result['check_id'],
                result['overall_result'],
                result['result_message'],
                result['success_count'],
                result['failure_count'],
                result['success_percentage'],
                safe_json_dumps(result['success_resources']),  # Will be cast to JSONB by PostgreSQL
                safe_json_dumps(result['failed_resources']),
                safe_json_dumps([]),  # Empty exclusions array
                safe_json_dumps(result['resource_collection_dict'])
            )
            
            # Insert into database
            row_id = database.execute_insert(insert_sql, params)
            
            if row_id:
                print(f"   ✅ {result['check_name']}: Inserted with ID {row_id}")
                inserted_count += 1
            else:
                print(f"   ⚠️ {result['check_name']}: Inserted but no ID returned")
                inserted_count += 1
                
        except Exception as e:
            print(f"   ❌ {result['check_name']}: Failed to insert - {e}")
            failed_count += 1
    
    # Print insertion summary
    print(f"\n📊 **Database Insertion Summary:**")
    print(f"   • Successfully inserted: {inserted_count}")
    print(f"   • Failed insertions: {failed_count}")
    print(f"   • Total check results: {len(processed_results)}")
    
    if inserted_count > 0:
        print(f"   ✅ Check results have been stored in the database")
    
    if failed_count > 0:
        print(f"   ⚠️ {failed_count} insertions failed - check database connectivity and table schema")
