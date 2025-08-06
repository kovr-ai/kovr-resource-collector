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
- Colorful console output with progress bars
- Secondary progress monitoring command

Usage:
    python single_add_checks_in_db.py [--dry-run] [--log-file progress.csv] [--resource-types github aws]
    python single_add_checks_in_db.py --progress [--log-file progress.csv]  # Monitor from another terminal
"""

import argparse
import csv
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional

# Console coloring
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    # Fallback if colorama not available
    class MockColor:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
        BRIGHT = ""
    
    Fore = Back = Style = MockColor()
    COLORS_AVAILABLE = False

# Progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from con_mon.utils.db import get_db
from generate_checks_with_llm import (
    call_llm_for_check,
    process_response_to_check,
    validate_check_execution
)

# Color-enhanced logging formatter
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors."""
    
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
    }

    def format(self, record):
        if COLORS_AVAILABLE:
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

# Set up logging with colors
def setup_logging():
    """Setup colored logging."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler with colors
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # File handler without colors
    file_handler = logging.FileHandler('single_add_checks.log')
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()


def print_colored(message: str, color: str = "", style: str = ""):
    """Print colored message."""
    if COLORS_AVAILABLE:
        color_code = getattr(Fore, color.upper(), "") if color else ""
        style_code = getattr(Style, style.upper(), "") if style else ""
        print(f"{color_code}{style_code}{message}{Style.RESET_ALL}")
    else:
        print(message)


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
        self.progress_bar = None
        
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
        print_colored(f"📊 Created progress log: {self.log_file}", "green")
    
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
                        
            print_colored(f"📋 Loaded {len(completed)} completed tasks from {self.log_file}", "blue")
            print_colored(f"   ✅ Successful: {self.successful_count}", "green")
            print_colored(f"   ❌ Failed: {self.failed_count}", "red")
            print_colored(f"   ⏭️  Skipped: {self.skipped_count}", "yellow")
            
        except FileNotFoundError:
            print_colored("📋 No existing progress file found, starting fresh", "blue")
        except Exception as e:
            print_colored(f"⚠️  Error loading progress: {e}", "yellow")
            
        return completed
    
    def is_task_completed(self, control_id: int, resource_type: str, connection_id: int) -> bool:
        """Check if a task is already completed."""
        task_key = f"{control_id}-{resource_type}-{connection_id}"
        return task_key in self.completed_tasks
    
    def setup_progress_bar(self, total: int):
        """Setup progress bar if tqdm is available."""
        if TQDM_AVAILABLE:
            self.progress_bar = tqdm(
                total=total,
                initial=len(self.completed_tasks),
                desc="Processing Controls",
                unit="task",
                colour="green",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
            )
    
    def log_task_start(self, control_id: int, control_name: str, resource_type: str, connection_id: int):
        """Log the start of a task."""
        self.current_task = {
            'control_id': control_id,
            'control_name': control_name,
            'resource_type': resource_type,
            'connection_id': connection_id,
            'start_time': datetime.now()
        }
        
        if self.progress_bar:
            self.progress_bar.set_description(f"Processing: {control_name} ({resource_type})")
        else:
            print_colored(f"🔄 Starting: {control_name} ({resource_type}) - Connection {connection_id}", "blue")
    
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
        
        # Update progress bar
        if self.progress_bar:
            self.progress_bar.update(1)
            # Set postfix with current stats
            self.progress_bar.set_postfix({
                'Success': self.successful_count,
                'Failed': self.failed_count,
                'ETA': eta_hms
            })
        else:
            # Log status with colors
            status_info = {
                "completed": ("✅", "green"),
                "failed": ("❌", "red"), 
                "skipped": ("⏭️", "yellow")
            }
            emoji, color = status_info.get(status, ("❓", "white"))
            
            print_colored(
                f"{emoji} {status.title()}: {self.current_task['control_name']} "
                f"({self.current_task['resource_type']}) - {duration:.1f}s", 
                color
            )
            
            if error_message:
                print_colored(f"   Error: {error_message}", "red")
            
            # Progress update
            self._log_progress_update(eta_hms)
    
    def _log_progress_update(self, eta_hms: str):
        """Log overall progress update."""
        if self.progress_bar:
            return  # Progress bar handles this
            
        progress_pct = (self.processed_count / self.total_count * 100) if self.total_count > 0 else 0
        
        print_colored(f"📊 Progress: {self.processed_count}/{self.total_count} ({progress_pct:.1f}%)", "cyan")
        print_colored(f"   ✅ Successful: {self.successful_count}", "green")
        print_colored(f"   ❌ Failed: {self.failed_count}", "red")
        print_colored(f"   ⏭️  Skipped: {self.skipped_count}", "yellow")
        print_colored(f"   ⏱️  ETA: {eta_hms}", "magenta")
        print_colored("-" * 60, "cyan")
    
    def _seconds_to_hms(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        hours, remainder = divmod(int(seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def set_total_count(self, total: int):
        """Set the total number of tasks."""
        self.total_count = total
        remaining = total - len(self.completed_tasks)
        print_colored(f"📋 Total tasks: {total}, Remaining: {remaining}", "blue")
        
        # Setup progress bar
        self.setup_progress_bar(total)
    
    def close_progress_bar(self):
        """Close progress bar."""
        if self.progress_bar:
            self.progress_bar.close()


def show_progress_monitor(log_file: str = "check_generation_progress.csv"):
    """Show live progress monitoring from CSV file."""
    print_colored("🔍 Progress Monitor - Live View", "cyan", "bright")
    print_colored("=" * 60, "cyan")
    
    if not os.path.exists(log_file):
        print_colored(f"❌ Progress file not found: {log_file}", "red")
        return
    
    last_count = 0
    start_time = None
    
    try:
        while True:
            try:
                # Read current progress
                with open(log_file, 'r') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                
                if not rows:
                    print_colored("📋 No progress data yet...", "yellow")
                    time.sleep(5)
                    continue
                
                # Calculate stats
                total_tasks = len(rows)
                completed = sum(1 for row in rows if row['status'] == 'completed')
                failed = sum(1 for row in rows if row['status'] == 'failed')
                skipped = sum(1 for row in rows if row['status'] == 'skipped')
                
                # Get latest task info
                latest_row = rows[-1]
                latest_control = latest_row['control_name']
                latest_resource = latest_row['resource_type']
                latest_status = latest_row['status']
                
                # Calculate progress
                progress_pct = (total_tasks / 100) if total_tasks > 0 else 0  # Assuming ~100 total controls
                
                # Get timing info
                if latest_row['total_runtime_hms']:
                    runtime = latest_row['total_runtime_hms']
                    eta = latest_row['estimated_completion_hms']
                else:
                    runtime = "00:00:00"
                    eta = "unknown"
                
                # Clear screen and show progress
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print_colored("🔍 LIVE PROGRESS MONITOR", "cyan", "bright")
                print_colored("=" * 60, "cyan")
                print_colored(f"📊 Tasks Processed: {total_tasks}", "blue")
                print_colored(f"✅ Successful: {completed}", "green")
                print_colored(f"❌ Failed: {failed}", "red")
                print_colored(f"⏭️  Skipped: {skipped}", "yellow")
                print_colored(f"⏱️  Runtime: {runtime}", "magenta")
                print_colored(f"🎯 ETA: {eta}", "magenta")
                print_colored("-" * 60, "cyan")
                print_colored(f"🔄 Latest: {latest_control} ({latest_resource}) - {latest_status}", "white")
                
                # Show progress bar
                if total_tasks > 0:
                    bar_length = 40
                    filled_length = int(bar_length * progress_pct / 100)
                    bar = '█' * filled_length + '░' * (bar_length - filled_length)
                    print_colored(f"Progress: |{bar}| {progress_pct:.1f}%", "green")
                
                print_colored("\n⏹️  Press Ctrl+C to exit monitor", "yellow")
                
                last_count = total_tasks
                time.sleep(5)  # Update every 5 seconds
                
            except FileNotFoundError:
                print_colored("📋 Waiting for progress file...", "yellow")
                time.sleep(5)
            except Exception as e:
                print_colored(f"⚠️  Error reading progress: {e}", "red")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print_colored("\n👋 Progress monitor stopped", "green")


def get_all_controls(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get all controls from the database with optional filtering."""
    db = get_db()
    
    # Base query
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
    """

    params = []

    # Add limit if specified
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    
    query += ";"
    
    try:
        results = db.execute_query(query, params if params else None)
        
        if limit:
            print_colored(f"📋 Loaded {len(results)} controls (limited to {limit})", "blue")
        else:
            print_colored(f"📋 Loaded {len(results)} controls from database", "blue")
            
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
        
        # Use get_connection for proper transaction handling
        with db.get_connection() as conn:
            with conn.cursor() as cursor:
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
                cursor.execute(insert_check_query, check_params)
                check_result = cursor.fetchone()
                
                if not check_result:
                    logger.error("❌ Failed to insert check - no ID returned")
                    return None
                
                check_id = check_result[0]
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
                
                cursor.execute(mapping_query, mapping_params)
                logger.info(f"✅ Created control-check mapping: control_id={control_id}, check_id={check_id}")
                
                # Commit the transaction
                conn.commit()
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
        if not progress.progress_bar:
            print_colored(f"⏭️  Skipping {control_name} ({resource_type}) - already completed", "yellow")
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
    parser = argparse.ArgumentParser(
        description="Single Add Checks in DB with Validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process both GitHub and AWS (default)
  python single_add_checks_in_db.py
  
  # Process only GitHub
  python single_add_checks_in_db.py --resource-types github
  
  # Process only AWS  
  python single_add_checks_in_db.py --resource-types aws
  
  # Process only first 5 controls
  python single_add_checks_in_db.py --limit 5
  
  # Process specific controls
  python single_add_checks_in_db.py --control-filter AC-1 AC-2 AC-3
  
  # Dry run mode
  python single_add_checks_in_db.py --dry-run
  
  # Monitor progress from another terminal
  python single_add_checks_in_db.py --progress
  
  # Run with nohup and monitor separately
  nohup python single_add_checks_in_db.py > output.log 2>&1 &
  python single_add_checks_in_db.py --progress
        """
    )
    parser.add_argument("--dry-run", action="store_true", 
                       help="Run without actually inserting to database")
    parser.add_argument("--log-file", default="check_generation_progress.csv",
                       help="CSV file to track progress (default: check_generation_progress.csv)")
    parser.add_argument("--github-connection-id", type=int, default=1,
                       help="Connection ID for GitHub resources (default: 1)")
    parser.add_argument("--aws-connection-id", type=int, default=2,
                       help="Connection ID for AWS resources (default: 2)")
    parser.add_argument("--resource-types", nargs='+', 
                       choices=['github', 'aws'],
                       help="Resource types to process. Default: both github and aws. "
                            "Use --resource-types github for GitHub only, "
                            "--resource-types aws for AWS only")
    parser.add_argument("--progress", action="store_true",
                       help="Show live progress monitor (run from another terminal)")
    parser.add_argument("--limit", type=int,
                       help="Limit number of controls to process (useful for testing)")
    
    args = parser.parse_args()
    
    # Handle progress monitor mode
    if args.progress:
        show_progress_monitor(args.log_file)
        return 0
    
    # Set default resource types if not specified
    if not args.resource_types:
        args.resource_types = ['github', 'aws']
    
    print_colored("🚀 Single Add Checks in DB - Autonomous Processing", "cyan", "bright")
    print_colored("=" * 60, "cyan")
    
    if args.dry_run:
        print_colored("🧪 DRY RUN MODE - No database insertions will be made", "yellow", "bright")
        print_colored("-" * 60, "yellow")
    
    print_colored(f"🎯 Resource types: {', '.join(args.resource_types)}", "blue")
    print_colored(f"📄 Progress log: {args.log_file}", "blue")
    
    if args.limit:
        print_colored(f"🔢 Processing limit: {args.limit} controls", "blue")

    if TQDM_AVAILABLE:
        print_colored("📊 Progress bar enabled", "green")
    else:
        print_colored("📊 Install 'tqdm' for progress bar: pip install tqdm", "yellow")
    
    print_colored("-" * 60, "cyan")
    
    # Initialize progress tracking
    progress = CheckGenerationProgress(args.log_file)
    
    # Get controls with optional filtering
    controls = get_all_controls(limit=args.limit)
    if not controls:
        print_colored("❌ No controls found. Exiting.", "red")
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
    
    try:
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
    
    except KeyboardInterrupt:
        print_colored("\n⏹️  Process interrupted by user", "yellow")
    
    finally:
        # Close progress bar
        progress.close_progress_bar()
    
    # Final summary
    total_time = datetime.now() - progress.start_time
    total_time_hms = progress._seconds_to_hms(total_time.total_seconds())
    
    print_colored("\n" + "=" * 60, "cyan")
    print_colored("🏁 FINAL SUMMARY", "cyan", "bright")
    print_colored("=" * 60, "cyan")
    print_colored(f"⏱️  Total runtime: {total_time_hms}", "magenta")
    print_colored(f"📊 Total tasks: {progress.processed_count}", "blue")
    print_colored(f"✅ Successful: {progress.successful_count}", "green")
    print_colored(f"❌ Failed: {progress.failed_count}", "red")
    print_colored(f"⏭️  Skipped: {progress.skipped_count}", "yellow")
    print_colored(f"📄 Progress log: {args.log_file}", "blue")
    
    if args.dry_run:
        print_colored("🧪 DRY RUN completed - no database changes made", "yellow")
    
    success_rate = (progress.successful_count / progress.processed_count * 100) if progress.processed_count > 0 else 0
    print_colored(f"📈 Success rate: {success_rate:.1f}%", "green" if success_rate > 80 else "yellow" if success_rate > 60 else "red")
    
    return 0 if failed_tasks == 0 else 1


if __name__ == "__main__":
    exit(main()) 