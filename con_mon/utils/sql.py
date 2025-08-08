"""
SQL operations for con_mon - handles SQL generation and file operations.
"""
import json
import os
from datetime import datetime
from typing import List, Tuple, Any, Optional
from .helpers import generate_result_message
from .db import get_db


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_json_dumps(data, indent=None):
    """Safely serialize data to JSON, handling datetime objects"""
    return json.dumps(data, cls=DateTimeEncoder, indent=indent)


def get_check_dicts(
    executed_check_results: List[Tuple[int, str, List[Any]]],
    resource_collection: Any,
):
    # Process each check result
    processed_results = []

    for check_id, check_name, check_results in executed_check_results:
        # Skip if no results
        if not check_results:
            continue
            
        # Count successes and failures
        success_count = sum(1 for result in check_results if result.passed)
        failure_count = sum(1 for result in check_results if not result.passed)
        total_count = len(check_results)
        success_percentage = int((success_count / total_count * 100)) if total_count > 0 else 0

        # Collect full Resource objects (as dicts)
        success_resources = []
        failed_resources = []

        for result in check_results:
            if result.passed:
                success_resources.append(result.resource.id)
            else:
                failed_resources.append(result.resource.id)

        # Generate static result message based on check properties
        # Get the check object from the first result (all results have the same check)
        check_obj = check_results[0].check
        overall_result, result_message = generate_result_message(
            check_obj,
            success_count,
            failure_count
        )

        # # Add detailed failure messages with proper formatting
        # failure_details = []
        # if failure_count > 0:
        #     for result in check_results:
        #         if not result.passed:
        #             if result.error:
        #                 overall_result = 'ERROR'
        #             failure_details.append({
        #                 'resource_id': result.resource.id,
        #                 'resource_name': result.resource.name,
        #                 'message': result.message,
        #                 'error': result.error if result.error else None
        #             })
        #
        #     # Format failure details with proper line breaks
        #     if len(failure_details) == 1:
        #         # Single failure - keep it concise
        #         fd = failure_details[0]
        #         if fd['error']:
        #             result_message += f"\n• Failure: {fd['resource_name']} - {fd['message']}\n• Error: {fd['error']}"
        #         else:
        #             result_message += f"\n• Failure: {fd['resource_name']} - {fd['message']}"
        #     else:
        #         # Multiple failures - format as a list
        #         result_message += f"\n• Failures ({len(failure_details)} resources):"
        #         for i, fd in enumerate(failure_details[:5]):  # Limit to first 5 for readability
        #             if fd['error']:
        #                 result_message += f"\n  {i + 1}. {fd['resource_name']}: {fd['message']} (Error: {fd['error']})"
        #             else:
        #                 result_message += f"\n  {i + 1}. {fd['resource_name']}: {fd['message']}"
        #
        #         # Add summary if there are more failures
        #         if len(failure_details) > 5:
        #             result_message += f"\n  ... and {len(failure_details) - 5} more failures"

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
            'resource_collection_dict': resource_collection.model_dump()
        })
    return processed_results


def insert_check_results(processed_results,
                        customer_id: str,
                        connection_id: int,
                        output_dir: Optional[str] = None,
                        **kwargs):
    """
    Generate and write SQL files or insert directly into database from executed check results.
    
    Args:
        executed_check_results: List of (check_id, check_name, check_results) tuples
        resource_collection: ResourceCollection for resource_json field
        customer_id: Customer identifier for SQL records
        connection_id: Connection identifier for SQL records
        output_dir: Directory to write SQL files. If None, insert directly into database.
        **kwargs: Additional keyword arguments (ignored, for compatibility)
    """

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


def _insert_into_database(processed_results: List[dict], customer_id: str, connection_id: int, batch_size: int = 50):
    """Insert check results into both history and current results tables using bulk operations in batches."""
    database = get_db()
    
    if not database._connection_pool:
        print("❌ Database connection not available. Cannot insert check results.")
        print("💡 Consider providing output_dir parameter to generate SQL files instead.")
        return
    
    print(f"\n💾 **Bulk Inserting into Database:**")
    print(f"   • Database: {database._connection_pool._kwargs.get('database', 'unknown')}")
    print(f"   • Host: {database._connection_pool._kwargs.get('host', 'unknown')}")
    print(f"   • Processing {len(processed_results)} check results in batches of {batch_size}...")
    
    try:
        with database.get_connection() as conn:
            with conn.cursor() as cursor:
                total_history_inserted = 0
                total_current_deleted = 0
                total_current_inserted = 0
                
                # Process in batches
                for i in range(0, len(processed_results), batch_size):
                    batch = processed_results[i:i + batch_size]
                    print(f"\n📦 **Processing batch {(i//batch_size) + 1} ({len(batch)} records)...**")
                    
                    # Prepare batch parameters
                    batch_params = []
                    batch_check_ids = []
                    
                    for result in batch:
                        params = (
                            customer_id,
                            connection_id,
                            result['check_id'],
                            result['overall_result'],
                            result['result_message'],
                            result['success_count'],
                            result['failure_count'],
                            result['success_percentage'],
                            safe_json_dumps(result['success_resources']),
                            safe_json_dumps(result['failed_resources']),
                            safe_json_dumps([]),  # Empty exclusions array
                            safe_json_dumps(result['resource_collection_dict'])
                        )
                        batch_params.append(params)
                        batch_check_ids.append(result['check_id'])
                    
                    # Step 1: Bulk INSERT into history table (con_mon_results_history)
                    print(f"   📜 Step 1: Bulk inserting batch into history table...")
                    history_insert_sql = """
                    INSERT INTO con_mon_results_history (
                        customer_id, connection_id, check_id, result, result_message,
                        success_count, failure_count, success_percentage,
                        success_resources, failed_resources, exclusions, resource_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    );
                    """
                    
                    cursor.executemany(history_insert_sql, batch_params)
                    history_inserted = cursor.rowcount
                    total_history_inserted += history_inserted
                    print(f"      ✅ Inserted {history_inserted} records into history")
                    
                    # Step 2: Bulk DELETE from current results table
                    print(f"   🗑️  Step 2: Bulk deleting batch from current results table...")
                    if len(batch_check_ids) == 1:
                        delete_current_sql = """
                        DELETE FROM con_mon_results 
                        WHERE customer_id = %s AND connection_id = %s AND check_id = %s;
                        """
                        cursor.execute(delete_current_sql, (customer_id, connection_id, batch_check_ids[0]))
                    else:
                        # Use IN clause for multiple check_ids
                        placeholders = ','.join(['%s'] * len(batch_check_ids))
                        delete_current_sql = f"""
                        DELETE FROM con_mon_results 
                        WHERE customer_id = %s AND connection_id = %s AND check_id IN ({placeholders});
                        """
                        cursor.execute(delete_current_sql, (customer_id, connection_id, *batch_check_ids))
                    
                    deleted_rows = cursor.rowcount
                    total_current_deleted += deleted_rows
                    print(f"      ✅ Deleted {deleted_rows} existing records")
                    
                    # Step 3: Bulk INSERT into current results table
                    print(f"   💾 Step 3: Bulk inserting batch into current results table...")
                    current_insert_sql = """
                    INSERT INTO con_mon_results (
                        customer_id, connection_id, check_id, result, result_message,
                        success_count, failure_count, success_percentage,
                        success_resources, failed_resources, exclusions, resource_json
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    );
                    """
                    
                    cursor.executemany(current_insert_sql, batch_params)
                    current_inserted = cursor.rowcount
                    total_current_inserted += current_inserted
                    print(f"      ✅ Inserted {current_inserted} records")
                    
                    # Commit each batch
                    conn.commit()
                    print(f"   ✅ Batch {(i//batch_size) + 1} committed successfully")
                
                # Print comprehensive insertion summary
                print(f"\n📊 **Bulk Database Operation Summary:**")
                print(f"   • History records inserted: {total_history_inserted}")
                print(f"   • Current records deleted: {total_current_deleted}")
                print(f"   • Current records inserted: {total_current_inserted}")
                print(f"   • Total check results processed: {len(processed_results)}")
                print(f"   • Number of batches: {(len(processed_results) + batch_size - 1) // batch_size}")
                print(f"   • Batch size: {batch_size}")
                
                print(f"\n✅ **All operations completed successfully:**")
                print(f"   • All check executions preserved in history")
                print(f"   • Latest check results available in current results table")
                print(f"   • Database consistency maintained")
                
    except Exception as e:
        print(f"\n❌ **Bulk database operation failed:** {e}")
        print(f"💡 Consider providing output_dir parameter to generate SQL files instead.")
        raise
