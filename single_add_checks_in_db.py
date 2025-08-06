#!/usr/bin/env python3
"""
Single Add Checks in DB with Validation

This script autonomously processes all controls from control.csv, generates checks
for both GitHub and AWS resources, validates them against sample data, and only
inserts successful checks into the database.

Features:
- CSV-based progress logging with resume capability
- Validation gating - only inserts if validation passes
- Time tracking with ETA calculations
- Comprehensive error handling and logging
- Support for both GitHub and AWS resources

Usage:
    python single_add_checks_in_db.py [--dry-run] [--resume] [--log-file progress.csv]
"""

import argparse
import csv
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from con_mon.utils.db import get_db
from generate_checks_with_llm import (
    get_control_from_db,
    call_llm_for_check,
    process_response_to_check,
    validate_check_execution
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('single_add_checks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CheckGenerationProgress:
    """Manages progress tracking and CSV logging for check generation."""
    
    def __init__(self, log_file: str = "check_generation_progress.csv"):
        self.log_file = log_file
        self.start_time = datetime.now()
        self.processed_count = 0
        self.total_count = 0
        self.successful_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
        # CSV headers
        self.headers = [
            'control_id', 'control_name', 'resource_type', 'connection_id',
            'status', 'error_message', 'start_time', 'end_time', 
            'duration_seconds', 'total_runtime_hms', 'estimated_completion_hms',
            'check_name', 'validation_success', 'execution_result', 'check_db_id'
        ]
        
        # Initialize CSV if it doesn't exist
        if not os.path.exists(self.log_file):
            self._create_csv()
        
        # Load existing progress
        self.completed_tasks = self._load_completed_tasks()
        
    def _create_csv(self):
        """Create CSV file with headers."""
        with open(self.log_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(self.headers)
        logger.info(f"📊 Created progress log: {self.log_file}")
    
    def _load_completed_tasks(self) -> set:
        """Load already completed tasks from CSV."""
        completed = set()
        try:
            with open(self.log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Create task key: control_id-resource_type-connection_id
                    task_key = f"{row['control_id']}-{row['resource_type']}-{row['connection_id']}"
                    completed.add(task_key)
                    
                    # Update counters based on status
                    if row['status'] == 'completed':
                        self.successful_count += 1
                    elif row['status'] == 'failed':
                        self.failed_count += 1
                    elif row['status'] == 'skipped':
                        self.skipped_count += 1
                        
            logger.info(f"📋 Loaded {len(completed)} completed tasks from {self.log_file}")
            logger.info(f"   ✅ Successful: {self.successful_count}")
            logger.info(f"   ❌ Failed: {self.failed_count}")
            logger.info(f"   ⏭️  Skipped: {self.skipped_count}")
            
        except FileNotFoundError:
            logger.info("📋 No existing progress file found, starting fresh")
        except Exception as e:
            logger.warning(f"⚠️  Error loading progress: {e}")
            
        return completed
    
    def is_task_completed(self, control_id: int, resource_type: str, connection_id: int) -> bool:
        """Check if a task is already completed."""
        task_key = f"{control_id}-{resource_type}-{connection_id}"
        return task_key in self.completed_tasks
    
    def log_task_start(self, control_id: int, control_name: str, resource_type: str, connection_id: int):
        """Log the start of a task."""
        self.current_task = {
            'control_id': control_id,
            'control_name': control_name,
            'resource_type': resource_type,
            'connection_id': connection_id,
            'start_time': datetime.now()
        }
        logger.info(f"🔄 Starting: {control_name} ({resource_type}) - Connection {connection_id}")
    
    def log_task_completion(
        self, 
        status: str, 
        error_message: str = "",
        check_name: str = "",
        validation_success: bool = False,
        execution_result: Any = None,
        check_db_id: int = None
    ):
        """Log the completion of a task."""
        end_time = datetime.now()
        duration = (end_time - self.current_task['start_time']).total_seconds()
        
        # Update counters
        self.processed_count += 1
        if status == 'completed':
            self.successful_count += 1
        elif status == 'failed':
            self.failed_count += 1
        elif status == 'skipped':
            self.skipped_count += 1
        
        # Calculate time estimates
        total_runtime = end_time - self.start_time
        total_runtime_hms = self._seconds_to_hms(total_runtime.total_seconds())
        
        # Calculate ETA
        if self.processed_count > 0:
            avg_time_per_task = total_runtime.total_seconds() / self.processed_count
            remaining_tasks = self.total_count - self.processed_count
            eta_seconds = avg_time_per_task * remaining_tasks
            eta_hms = self._seconds_to_hms(eta_seconds)
        else:
            eta_hms = "unknown"
        
        # Prepare row data
        row_data = {
            'control_id': self.current_task['control_id'],
            'control_name': self.current_task['control_name'],
            'resource_type': self.current_task['resource_type'],
            'connection_id': self.current_task['connection_id'],
            'status': status,
            'error_message': error_message,
            'start_time': self.current_task['start_time'].isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': round(duration, 2),
            'total_runtime_hms': total_runtime_hms,
            'estimated_completion_hms': eta_hms,
            'check_name': check_name,
            'validation_success': validation_success,
            'execution_result': str(execution_result) if execution_result is not None else "",
            'check_db_id': check_db_id or ""
        }
        
        # Write to CSV
        with open(self.log_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(row_data)
        
        # Add to completed tasks
        task_key = f"{self.current_task['control_id']}-{self.current_task['resource_type']}-{self.current_task['connection_id']}"
        self.completed_tasks.add(task_key)
        
        # Log status
        status_emoji = {"completed": "✅", "failed": "❌", "skipped": "⏭️"}.get(status, "❓")
        logger.info(f"{status_emoji} {status.title()}: {self.current_task['control_name']} ({self.current_task['resource_type']}) - {duration:.1f}s")
        
        if error_message:
            logger.error(f"   Error: {error_message}")
        
        # Progress update
        self._log_progress_update(eta_hms)
    
    def _log_progress_update(self, eta_hms: str):
        """Log overall progress update."""
        progress_pct = (self.processed_count / self.total_count * 100) if self.total_count > 0 else 0
        
        logger.info(f"📊 Progress: {self.processed_count}/{self.total_count} ({progress_pct:.1f}%)")
        logger.info(f"   ✅ Successful: {self.successful_count}")
        logger.info(f"   ❌ Failed: {self.failed_count}")
        logger.info(f"   ⏭️  Skipped: {self.skipped_count}")
        logger.info(f"   ⏱️  ETA: {eta_hms}")
        logger.info("-" * 60)
    
    def _seconds_to_hms(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def set_total_count(self, total: int):
        """Set the total number of tasks."""
        self.total_count = total
        remaining = total - len(self.completed_tasks)
        logger.info(f"📋 Total tasks: {total}, Remaining: {remaining}")


def get_all_controls() -> List[Dict[str, Any]]:
    """Get all controls from the database."""
    db = get_db()
    
    query = """
    SELECT 
        id,
        control_name,
        control_long_name,
        control_text,
        control_discussion,
        family_name
    FROM control 
    WHERE control_name IS NOT NULL
    ORDER BY control_name;
    """
    
    try:
        results = db.execute_query(query)
        logger.info(f"📋 Loaded {len(results)} controls from database")
        return results
    except Exception as e:
        logger.error(f"❌ Failed to load controls: {e}")
        return []


def insert_check_to_database(check: 'Check', control_id: int) -> Optional[int]:
    """
    Insert a validated check into the database.
    
    Args:
        check: Check object to insert
        control_id: Database ID of the control for mapping
        
    Returns:
        Database ID of the inserted check, or None if failed
    """
    db = get_db()
    
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
        
        current_time = datetime.now()
        
        # Insert check and get the generated ID
        insert_check_query = """
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
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        
        check_params = (
            check.name,
            check.description or "",
            output_statements_json,
            fix_details_json,
            check.created_by,
            check.updated_by,
            check.metadata.category,
            metadata_json,
            current_time,
            current_time,
            check.is_deleted
        )
        
        # Execute check insertion
        check_results = db.execute_query(insert_check_query, check_params)
        if not check_results:
            logger.error("❌ Failed to insert check - no ID returned")
            return None
        
        check_id = check_results[0]['id']
        logger.info(f"✅ Inserted check with ID: {check_id}")
        
        # Insert control-check mapping
        mapping_query = """
        INSERT INTO control_checks_mapping (
            control_id,
            check_id,
            created_at,
            updated_at,
            is_deleted
        ) VALUES (%s, %s, %s, %s, %s);
        """
        
        mapping_params = (
            control_id,
            check_id,
            current_time,
            current_time,
            False
        )
        
        db.execute_query(mapping_query, mapping_params)
        logger.info(f"✅ Created control-check mapping: control_id={control_id}, check_id={check_id}")
        
        return check_id
        
    except Exception as e:
        logger.error(f"❌ Failed to insert check to database: {e}")
        import traceback
        traceback.print_exc()
        return None


def process_single_control_resource(
    control_data: Dict[str, Any],
    resource_type: str,
    connection_id: int,
    progress: CheckGenerationProgress,
    dry_run: bool = False
) -> bool:
    """
    Process a single control-resource combination.
    
    Args:
        control_data: Control information from database
        resource_type: Target resource type (github, aws)
        connection_id: Connection ID for the check
        progress: Progress tracking object
        dry_run: If True, don't actually insert to database
        
    Returns:
        True if successful, False otherwise
    """
    control_id = control_data['id']
    control_name = control_data['control_name']
    
    # Check if already completed
    if progress.is_task_completed(control_id, resource_type, connection_id):
        logger.info(f"⏭️  Skipping {control_name} ({resource_type}) - already completed")
        return True
    
    # Start task logging
    progress.log_task_start(control_id, control_name, resource_type, connection_id)
    
    try:
        # Step 1: Call LLM to generate check
        yaml_content = call_llm_for_check(
            control_name=control_name,
            control_data=control_data,
            resource_type=resource_type,
            connection_id=connection_id
        )
        
        if not yaml_content:
            progress.log_task_completion('failed', 'LLM failed to generate YAML content')
            return False
        
        # Step 2: Process response to Check object
        check = process_response_to_check(
            yaml_content=yaml_content,
            control_name=control_name,
            control_data=control_data,
            resource_type=resource_type,
            connection_id=connection_id
        )
        
        if not check:
            progress.log_task_completion('failed', 'Failed to create Check object from YAML')
            return False
        
        # Step 3: Validate check execution
        validation_result = validate_check_execution(check, resource_type)
        
        if not validation_result["success"]:
            error_msg = f"Validation failed: {validation_result['error']}"
            progress.log_task_completion(
                'failed', 
                error_msg,
                check.name,
                False,
                None
            )
            return False
        
        # Step 4: Insert to database (only if validation passed and not dry run)
        check_db_id = None
        if not dry_run:
            check_db_id = insert_check_to_database(check, control_id)
            if not check_db_id:
                progress.log_task_completion(
                    'failed',
                    'Database insertion failed',
                    check.name,
                    True,
                    validation_result["execution_result"]
                )
                return False
        
        # Success!
        progress.log_task_completion(
            'completed',
            '',
            check.name,
            True,
            validation_result["execution_result"],
            check_db_id
        )
        return True
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        progress.log_task_completion('failed', error_msg)
        logger.error(f"❌ Unexpected error processing {control_name} ({resource_type}): {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Single Add Checks in DB with Validation")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run without actually inserting to database")
    parser.add_argument("--log-file", default="check_generation_progress.csv",
                       help="CSV file to track progress (default: check_generation_progress.csv)")
    parser.add_argument("--github-connection-id", type=int, default=1,
                       help="Connection ID for GitHub resources (default: 1)")
    parser.add_argument("--aws-connection-id", type=int, default=2,
                       help="Connection ID for AWS resources (default: 2)")
    parser.add_argument("--resource-types", nargs='+', default=['github', 'aws'],
                       choices=['github', 'aws'],
                       help="Resource types to process (default: github aws)")
    
    args = parser.parse_args()
    
    print("🚀 Single Add Checks in DB - Autonomous Processing")
    print("=" * 60)
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No database insertions will be made")
        print("-" * 60)
    
    # Initialize progress tracking
    progress = CheckGenerationProgress(args.log_file)
    
    # Get all controls
    controls = get_all_controls()
    if not controls:
        logger.error("❌ No controls found. Exiting.")
        return 1
    
    # Calculate total tasks
    connection_mapping = {
        'github': args.github_connection_id,
        'aws': args.aws_connection_id
    }
    
    total_tasks = len(controls) * len(args.resource_types)
    progress.set_total_count(total_tasks)
    
    # Process each control for each resource type
    successful_tasks = 0
    failed_tasks = 0
    
    for control_data in controls:
        for resource_type in args.resource_types:
            connection_id = connection_mapping[resource_type]
            
            success = process_single_control_resource(
                control_data=control_data,
                resource_type=resource_type,
                connection_id=connection_id,
                progress=progress,
                dry_run=args.dry_run
            )
            
            if success:
                successful_tasks += 1
            else:
                failed_tasks += 1
            
            # Small delay to avoid overwhelming the LLM service
            time.sleep(1)
    
    # Final summary
    total_time = datetime.now() - progress.start_time
    total_time_hms = progress._seconds_to_hms(total_time.total_seconds())
    
    print("\n" + "=" * 60)
    print("🏁 FINAL SUMMARY")
    print("=" * 60)
    print(f"⏱️  Total runtime: {total_time_hms}")
    print(f"📊 Total tasks: {progress.processed_count}")
    print(f"✅ Successful: {progress.successful_count}")
    print(f"❌ Failed: {progress.failed_count}")
    print(f"⏭️  Skipped: {progress.skipped_count}")
    print(f"📄 Progress log: {args.log_file}")
    
    if args.dry_run:
        print("🧪 DRY RUN completed - no database changes made")
    
    success_rate = (progress.successful_count / progress.processed_count * 100) if progress.processed_count > 0 else 0
    print(f"📈 Success rate: {success_rate:.1f}%")
    
    return 0 if failed_tasks == 0 else 1


if __name__ == "__main__":
    exit(main()) 