#!/usr/bin/env python3
"""
Batch Check Generation Script with Rich UI

Generates compliance checks for all providers and resource types using LLM.
Features:
- Multi-provider support (GitHub, AWS, etc.)
- Threading for faster processing
- Progress tracking with status CSV
- Rich colorful UI
- Prompt logging (input/output)
- Resume from last saved control
- Error retry functionality
"""

import argparse
import csv
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich import box

# con_mon_v2 imports
from con_mon_v2.compliance import ControlLoader
from con_mon_v2.compliance.models import Check, Control
from con_mon_v2.utils.llm.generate import (
    generate_check,
    evaluate_check_against_rc,
    get_provider_resources_mapping
)
from con_mon_v2.connectors.models import ConnectorType
from con_mon_v2.utils.db import get_db

console = Console()

@dataclass
class ProcessingStats:
    """Track processing statistics"""
    total_controls: int = 0
    processed_controls: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    error_checks: int = 0
    skipped_controls: int = 0
    start_time: datetime = None
    completed_tasks: int = 0
    total_tasks: int = 0
    
    def get_elapsed_time(self) -> str:
        """Get formatted elapsed time"""
        if not self.start_time:
            return "00:00:00"
        elapsed = datetime.now() - self.start_time
        return str(elapsed).split('.')[0]
    
    def get_estimated_completion(self) -> str:
        """Get estimated time to completion"""
        if not self.start_time or self.completed_tasks == 0:
            return "Calculating..."
        
        elapsed = datetime.now() - self.start_time
        elapsed_seconds = elapsed.total_seconds()
        
        # Calculate average time per task
        avg_time_per_task = elapsed_seconds / self.completed_tasks
        
        # Calculate remaining tasks
        remaining_tasks = self.total_tasks - self.completed_tasks
        
        if remaining_tasks <= 0:
            return "Completed!"
        
        # Estimate remaining time
        estimated_remaining_seconds = avg_time_per_task * remaining_tasks
        
        # Format remaining time
        remaining_hours = int(estimated_remaining_seconds // 3600)
        remaining_minutes = int((estimated_remaining_seconds % 3600) // 60)
        remaining_secs = int(estimated_remaining_seconds % 60)
        estimated_remaining = f"{remaining_hours:02d}:{remaining_minutes:02d}:{remaining_secs:02d}"
        
        # Calculate estimated completion time
        completion_time = datetime.now() + timedelta(seconds=estimated_remaining_seconds)
        completion_str = completion_time.strftime('%H:%M:%S')
        
        return f"{estimated_remaining} (ETA: {completion_str})"
    
    def get_processing_rate(self) -> str:
        """Get current processing rate"""
        if not self.start_time or self.completed_tasks == 0:
            return "0.0 tasks/min"
        
        elapsed = datetime.now() - self.start_time
        elapsed_minutes = elapsed.total_seconds() / 60
        
        if elapsed_minutes == 0:
            return "∞ tasks/min"
        
        rate = self.completed_tasks / elapsed_minutes
        return f"{rate:.1f} tasks/min"

class StatusTracker:
    """Tracks and persists processing status"""
    
    def __init__(self, status_file: str = None):
        if status_file is None:
            # Use project root data/generate_checks/ for status file
            status_file = project_root / "data" / "generate_checks" / "batch_status.csv"
        
        self.status_file = Path(status_file)
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        
        # Initialize CSV if it doesn't exist
        if not self.status_file.exists():
            with open(self.status_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'control_id', 'control_name', 'provider', 'resource_type', 
                    'status', 'check_id', 'error_message', 'timestamp', 'attempts'
                ])
    
    def update_status(self, control_id: int, control_name: str, provider: str, 
                     resource_type: str, status: str, check_id: str = None, 
                     error_message: str = None, attempts: int = 1):
        """Update processing status"""
        with self.lock:
            with open(self.status_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    control_id, control_name, provider, resource_type,
                    status, check_id or '', error_message or '',
                    datetime.now().isoformat(), attempts
                ])
    
    def get_last_processed_control(self) -> Optional[int]:
        """Get the last successfully processed control ID"""
        if not self.status_file.exists():
            return None
            
        try:
            with open(self.status_file, 'r') as f:
                reader = csv.DictReader(f)
                last_control_id = None
                for row in reader:
                    if row['status'] == 'success':
                        last_control_id = int(row['control_id'])
                return last_control_id
        except:
            return None
    
    def get_error_entries(self) -> List[Dict[str, Any]]:
        """Get all error entries for retry"""
        if not self.status_file.exists():
            return []
            
        errors = []
        try:
            with open(self.status_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] == 'error':
                        errors.append(row)
        except:
            pass
        return errors
    
    def get_statistics(self) -> Dict[str, int]:
        """Get processing statistics from status file"""
        if not self.status_file.exists():
            return {'total': 0, 'success': 0, 'error': 0, 'pending': 0}
            
        stats = {'total': 0, 'success': 0, 'error': 0, 'pending': 0}
        
        # Track unique tasks to avoid double-counting retries
        unique_tasks = {}  # task_key -> latest_status
        
        try:
            with open(self.status_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Create unique task key: control_id-provider-resource_type
                    task_key = f"{row['control_id']}-{row['provider']}-{row['resource_type']}"
                    
                    # Keep only the latest status for each unique task
                    unique_tasks[task_key] = row['status']
            
            # Count unique tasks by their latest status
            for task_key, status in unique_tasks.items():
                stats['total'] += 1
                if status == 'success':
                    stats['success'] += 1
                elif status == 'error':
                    stats['error'] += 1
                else:
                    stats['pending'] += 1
                    
        except:
            pass
        return stats

class PromptLogger:
    """Logs LLM input and output prompts"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            # Use project root data/generate_checks/prompts/ for prompts
            base_dir = project_root / "data" / "generate_checks" / "prompts"
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def log_prompt(self, control_name: str, provider: str, resource_type: str,
                   input_prompt: str, output_response: str):
        """Log input and output prompts"""
        # Create directory structure: data/generate_checks/prompts/control/provider/resource/
        prompt_dir = self.base_dir / control_name / provider / resource_type
        prompt_dir.mkdir(parents=True, exist_ok=True)
        
        # Save input prompt
        input_file = prompt_dir / f"input_{control_name}_{provider}_{resource_type}.txt"
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"INPUT PROMPT - {control_name} | {provider} | {resource_type}\n")
            f.write("=" * 80 + "\n")
            f.write(input_prompt)
            f.write("\n" + "=" * 80 + "\n")
        
        # Save output response
        output_file = prompt_dir / f"output_{control_name}_{provider}_{resource_type}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"OUTPUT RESPONSE - {control_name} | {provider} | {resource_type}\n")
            f.write("=" * 80 + "\n")
            f.write(output_response)
            f.write("\n" + "=" * 80 + "\n")

class ErrorTracker:
    """Tracks detailed error information for failed checks"""
    
    def __init__(self, base_dir: str = None):
        if base_dir is None:
            base_dir = project_root / "data" / "generate_checks" / "errors"
        
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.error_file = self.base_dir / "error_details.csv"
        self.lock = threading.Lock()
        
        # Initialize error CSV if it doesn't exist
        if not self.error_file.exists():
            with open(self.error_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'control_id', 'control_name', 'provider', 'resource_type',
                    'check_id', 'check_name', 'field_path', 'operation_name', 'custom_logic',
                    'error_type', 'error_message', 'check_results_count', 'passed_count', 
                    'failed_count', 'error_count', 'sample_errors', 'attempt_number'
                ])
    
    def log_error(self, control: Control, provider: str, resource_type: str, 
                  check: Check, check_results: List, attempt_number: int = 1):
        """Log detailed error information for a failed check"""
        try:
            # Extract check metadata
            field_path = getattr(check.metadata, 'field_path', 'Unknown')
            operation_name = getattr(check.metadata.operation, 'name', 'Unknown') if hasattr(check.metadata, 'operation') else 'Unknown'
            custom_logic = getattr(check.metadata.operation, 'logic', 'Unknown') if hasattr(check.metadata, 'operation') else 'Unknown'
            
            # Analyze check results
            total_results = len(check_results)
            passed_count = sum(1 for r in check_results if r.passed is True)
            failed_count = sum(1 for r in check_results if r.passed is False)
            error_count = sum(1 for r in check_results if r.passed is None)
            
            # Collect sample errors (first 3 unique errors)
            sample_errors = []
            seen_errors = set()
            for result in check_results:
                if result.error and str(result.error) not in seen_errors:
                    sample_errors.append(str(result.error))
                    seen_errors.add(str(result.error))
                    if len(sample_errors) >= 3:
                        break
            
            # Determine error type
            if error_count > 0:
                error_type = "Logic Error"
                error_message = "; ".join(sample_errors) if sample_errors else "Unknown logic error"
            elif failed_count == total_results:
                error_type = "All Failed"
                error_message = "All resources failed compliance check"
            elif passed_count == 0 and failed_count == 0:
                error_type = "No Results"
                error_message = "No evaluation results generated"
            else:
                error_type = "Validation Failed"
                error_message = f"Insufficient valid results: {passed_count} passed, {failed_count} failed, {error_count} errors"
            
            # Write to CSV
            with self.lock:
                with open(self.error_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().isoformat(),
                        control.id,
                        control.control_name,
                        provider,
                        resource_type,
                        check.id,
                        check.name,
                        field_path,
                        operation_name,
                        custom_logic[:500] if len(str(custom_logic)) > 500 else custom_logic,  # Truncate long logic
                        error_type,
                        error_message,
                        total_results,
                        passed_count,
                        failed_count,
                        error_count,
                        "; ".join(sample_errors),
                        attempt_number
                    ])
                    
        except Exception as e:
            console.print(f"[red]❌ Failed to log error details: {str(e)}[/red]")
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of error types"""
        if not self.error_file.exists():
            return {}
        
        error_counts = {}
        try:
            with open(self.error_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    error_type = row['error_type']
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
        except:
            pass
        return error_counts

def setup_database_mode(db_mode: str):
    """Setup database mode by setting environment variable"""
    if db_mode.lower() == 'csv':
        os.environ['DATABASE_TYPE'] = 'csv'
        console.print("🗃️  [cyan]Database mode set to CSV[/cyan]")
    elif db_mode.lower() == 'pgs':
        os.environ['DATABASE_TYPE'] = 'postgresql'
        console.print("🐘 [cyan]Database mode set to PostgreSQL[/cyan]")
    else:
        console.print(f"[red]❌ Invalid database mode: {db_mode}[/red]")
        raise ValueError(f"Invalid database mode: {db_mode}")

def load_controls(limit: Optional[int] = None, start_from: Optional[int] = None) -> List[Control]:
    """Load controls from database"""
    console.print("📋 [yellow]Loading controls from database...[/yellow]")
    
    loader = ControlLoader()
    all_controls = loader.load_all()
    
    # Filter active controls
    active_controls = [c for c in all_controls if c.active]
    
    # Apply start_from filter
    if start_from:
        active_controls = [c for c in active_controls if c.id >= start_from]
    
    # Apply limit
    if limit:
        active_controls = active_controls[:limit]
    
    console.print(f"✅ [green]Loaded {len(active_controls)} active controls[/green]")
    return active_controls

def save_check_to_database(check: Check, control_id: int) -> bool:
    """Save check to database and create control mapping"""
    try:
        db = get_db()
        
        # Convert Check object to database format with proper JSON serialization
        def serialize_for_json(obj):
            """Custom serializer for complex objects"""
            if hasattr(obj, 'value'):  # Handle Enum types like ComparisonOperationEnum
                return obj.value
            elif hasattr(obj, 'model_dump'):  # Handle Pydantic models
                return obj.model_dump()
            elif hasattr(obj, '__dict__'):  # Handle other objects
                return obj.__dict__
            else:
                return str(obj)
        
        # Convert complex fields to JSON with custom serializer
        output_statements_json = json.dumps(check.output_statements.model_dump(), default=serialize_for_json)
        fix_details_json = json.dumps(check.fix_details.model_dump(), default=serialize_for_json)
        metadata_json = json.dumps(check.metadata.model_dump(), default=serialize_for_json)
        
        check_data = {
            'id': check.id,
            'name': check.name,
            'description': check.description,
            'output_statements': output_statements_json,
            'fix_details': fix_details_json,
            'metadata': metadata_json,
            'created_by': check.created_by,
            'category': check.category,
            'updated_by': check.updated_by,
            'created_at': check.created_at.isoformat(),
            'updated_at': check.updated_at.isoformat(),
            'is_deleted': check.is_deleted
        }
        
        # Insert check
        db.execute_insert('checks', check_data)
        
        # Create control-check mapping
        mapping_data = {
            'control_id': control_id,
            'check_id': check.id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_deleted': False
        }
        
        db.execute_insert('control_checks_mapping', mapping_data)
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Database save failed: {str(e)}[/red]")
        return False

def process_single_control_provider(
    control: Control,
    connector_type: ConnectorType,
    resource_model_name: str,
    status_tracker: StatusTracker,
    prompt_logger: PromptLogger,
    error_tracker: ErrorTracker,
    max_attempts: int = 2  # Changed from 3 to 2 to match individual script
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Process a single control for a specific provider/resource with self-improvement"""
    
    provider_name = connector_type.value
    control_name = control.control_name
    
    try:
        console.print(f"🔄 [cyan]Processing {control_name} | {provider_name} | {resource_model_name}[/cyan]")
        
        # Generate initial check
        console.print(f"🔄 [yellow]Generating initial check...[/yellow]")
        check = generate_check(
            control_name=control.control_name,
            control_text=control.control_text or "",
            control_title=control.control_long_name or control.control_name,
            control_id=control.id,
            connector_type=connector_type,
            resource_model_name=resource_model_name
        )
        console.print(f"✅ [green]Generated initial check: {check.name}[/green]")
        
        # Log prompts (if available)
        if hasattr(check, '_raw_yaml'):
            input_prompt = getattr(check, '_input_prompt', 'Input prompt not available')
            prompt_logger.log_prompt(
                control_name, provider_name, resource_model_name,
                input_prompt, check._raw_yaml
            )
        
        # Evaluate initial check
        console.print(f"📊 [yellow]Evaluating initial check against resources...[/yellow]")
        check_results = evaluate_check_against_rc(check)
        console.print(f"📊 [cyan]Got {len(check_results)} evaluation results[/cyan]")
        
        # Track all results for learning
        all_check_results = check_results.copy()
        current_results = check_results
        counter = 0
        
        console.print(f"🔄 [yellow]Starting validation loop (max {max_attempts} attempts)...[/yellow]")
        
        # Self-improvement loop - same logic as individual script
        while check.is_invalid(current_results):
            counter += 1
            console.print(f"🔄 [yellow]Attempt {counter}/{max_attempts}: Check is invalid, regenerating with feedback...[/yellow]")
            
            # Log error details for this failed attempt
            error_tracker.log_error(control, provider_name, resource_model_name, check, current_results, counter)
            
            if counter >= max_attempts:
                console.print(f"❌ [red]Giving up after {max_attempts} attempts[/red]")
                error_msg = f"Check validation failed after {max_attempts} attempts"
                status_tracker.update_status(
                    control.id, control_name, provider_name,
                    resource_model_name, 'error', None, error_msg
                )
                # Log final error with all accumulated results
                error_tracker.log_error(control, provider_name, resource_model_name, check, all_check_results, counter)
                return False, None, error_msg
            
            console.print(f"🧠 [yellow]Regenerating check with {len(all_check_results)} accumulated results as feedback...[/yellow]")
            
            # Generate improved check with feedback
            improved_check = generate_check(
                control_name=control.control_name,
                control_text=control.control_text or "",
                control_title=control.control_long_name or control.control_name,
                control_id=control.id,
                connector_type=connector_type,
                resource_model_name=resource_model_name,
                check_results=all_check_results  # Pass accumulated results for learning
            )
            
            if not improved_check:
                console.print("❌ [red]No improved check generated[/red]")
                error_msg = "Failed to generate improved check"
                status_tracker.update_status(
                    control.id, control_name, provider_name,
                    resource_model_name, 'error', None, error_msg
                )
                error_tracker.log_error(control, provider_name, resource_model_name, check, all_check_results, counter)
                return False, None, error_msg
            
            console.print(f"✅ [green]Generated improved check: {improved_check.name}[/green]")
            check = improved_check
            
            # Log improved prompts
            if hasattr(check, '_raw_yaml'):
                input_prompt = getattr(check, '_input_prompt', f'Improved attempt {counter} - Input prompt not available')
                prompt_logger.log_prompt(
                    control_name, provider_name, resource_model_name,
                    input_prompt, check._raw_yaml
                )
            
            # Evaluate improved check
            console.print(f"📊 [yellow]Evaluating improved check...[/yellow]")
            current_results = evaluate_check_against_rc(check)
            console.print(f"📊 [cyan]Got {len(current_results)} new evaluation results[/cyan]")
            
            # Add to accumulated results for next iteration
            all_check_results.extend(current_results)
            console.print(f"📈 [cyan]Total accumulated results: {len(all_check_results)}[/cyan]")
        
        # Check passed validation
        console.print(f"✅ [green]Check {check.name} is valid! Saving to database...[/green]")
        
        # Save to database
        if save_check_to_database(check, control.id):
            console.print(f"💾 [green]Successfully saved check to database[/green]")
            status_tracker.update_status(
                control.id, control_name, provider_name, 
                resource_model_name, 'success', check.id
            )
            return True, check.id, None
        else:
            error_msg = "Database save failed"
            console.print(f"❌ [red]{error_msg}[/red]")
            status_tracker.update_status(
                control.id, control_name, provider_name,
                resource_model_name, 'error', None, error_msg
            )
            return False, None, error_msg
            
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        console.print(f"❌ [red]{error_msg}[/red]")
        status_tracker.update_status(
            control.id, control_name, provider_name,
            resource_model_name, 'error', None, error_msg
        )
        return False, None, error_msg

def create_progress_table(stats: ProcessingStats) -> Table:
    """Create a rich table showing progress statistics"""
    table = Table(title="📊 Processing Statistics", box=box.ROUNDED)
    
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Count", style="magenta")
    table.add_column("Details", style="green")
    
    if stats.total_controls > 0:
        processed_pct = (stats.processed_controls / stats.total_controls) * 100
        success_pct = (stats.successful_checks / max(1, stats.successful_checks + stats.failed_checks)) * 100
        task_completion_pct = (stats.completed_tasks / max(1, stats.total_tasks)) * 100
    else:
        processed_pct = 0
        success_pct = 0
        task_completion_pct = 0
    
    table.add_row("Total Controls", str(stats.total_controls), "100%")
    table.add_row("Processed Controls", str(stats.processed_controls), f"{processed_pct:.1f}%")
    table.add_row("Total Tasks", str(stats.total_tasks), "100%")
    table.add_row("Completed Tasks", str(stats.completed_tasks), f"{task_completion_pct:.1f}%")
    table.add_row("Successful Checks", str(stats.successful_checks), f"{success_pct:.1f}%")
    table.add_row("Failed Checks", str(stats.failed_checks), f"{100-success_pct:.1f}%")
    table.add_row("Error Checks", str(stats.error_checks), "")
    
    # Time tracking information
    table.add_row("─" * 15, "─" * 10, "─" * 15)  # Separator
    table.add_row("Elapsed Time", stats.get_elapsed_time(), "")
    table.add_row("Processing Rate", stats.get_processing_rate(), "")
    table.add_row("Est. Remaining", stats.get_estimated_completion(), "")
    
    return table

def show_progress_stats(status_tracker: StatusTracker, limit: int = None, threads: int = 1):
    """Show crisp live progress statistics with clean screen updates"""
    
    import contextlib
    import io
    
    # Suppress all other output during monitoring for crisp display
    @contextlib.contextmanager
    def suppress_output():
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        try:
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    # Clear screen immediately and suppress any initial output
    os.system('clear' if os.name == 'posix' else 'cls')
    
    try:
        while True:
            # Clear screen for crisp display
            print('\033[H\033[J', end='')  # ANSI escape sequence to clear screen
            
            # Get current stats (suppress database loading messages)
            with suppress_output():
                stats = status_tracker.get_statistics()
                time_stats = _calculate_time_stats_from_status(status_tracker, limit=limit, threads=threads)
            
            # Build the entire display as a single string to avoid flicker
            display_lines = [
                "🚀 BATCH CHECK GENERATION - LIVE MONITOR",
                "=" * 60,
                ""
            ]
            
            # Main stats
            total_processed = stats['success'] + stats['error']
            completion_pct = (total_processed / stats['total'] * 100) if stats['total'] > 0 else 0
            
            display_lines.extend([
                f"📊 Tasks Processed: {total_processed}",
                f"✅ Successful: {stats['success']}",
                f"❌ Failed: {stats['error']}",
                "",
                f"⏱️  Processing Rate: {time_stats['rate']}",
                f"🎯 ETA (All Tasks): {time_stats['estimated_remaining']}",
                f"🎯 ETA (All Success): {time_stats['success_eta']}"
            ])
            
            if stats['total'] > total_processed:
                display_lines.insert(-3, f"📈 Total Expected: {stats['total']}")
            
            # Scope info
            scope_parts = []
            if limit:
                scope_parts.append(f"Limited to {limit} controls")
            if threads > 1:
                scope_parts.append(f"Using {threads} threads")
            
            if scope_parts:
                display_lines.extend(["", f"🎯 Scope: {' | '.join(scope_parts)}"])
            
            display_lines.extend(["", "-" * 60])
            
            # Two progress bars instead of one
            total_processed = stats['success'] + stats['error']
            completion_pct = (total_processed / stats['total'] * 100) if stats['total'] > 0 else 0
            success_pct = (stats['success'] / total_processed * 100) if total_processed > 0 else 0
            
            # Progress bar 1: Overall completion (tasks processed vs total)
            bar_length = 35
            completion_filled = int(bar_length * min(completion_pct, 100) / 100)
            completion_bar = '█' * completion_filled + '░' * (bar_length - completion_filled)
            display_lines.append(f"Overall:  |{completion_bar}| {completion_pct:.1f}% ({total_processed}/{stats['total']})")
            
            # Progress bar 2: Success rate (successful vs processed)  
            success_filled = int(bar_length * min(success_pct, 100) / 100)
            success_bar = '█' * success_filled + '░' * (bar_length - success_filled)
            display_lines.append(f"Success:  |{success_bar}| {success_pct:.1f}% ({stats['success']}/{total_processed})")
            
            display_lines.append("")
            
            display_lines.extend(["", "⏹️  Press Ctrl+C to exit monitor"])
            
            # Check if completed
            if "Completed!" in time_stats['estimated_remaining']:
                display_lines.extend(["", "🎉 PROCESSING COMPLETE!"])
                
            # Print entire display at once
            print('\n'.join(display_lines), flush=True)
            
            if "Completed!" in time_stats['estimated_remaining']:
                time.sleep(2)
                break
            
            time.sleep(3)  # Update every 3 seconds
                
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped by user")
    
    # Final summary (clear screen first for clean finish)
    print('\033[H\033[J', end='')  # Clear screen
    
    with suppress_output():
        final_stats = status_tracker.get_statistics()
    
    summary_lines = [
        "🏁 FINAL SUMMARY",
        "=" * 60,
        ""
    ]
    
    if final_stats['success'] > 0:
        summary_lines.append(f"✅ {final_stats['success']} checks generated successfully")
    
    if final_stats['error'] > 0:
        summary_lines.extend([
            f"❌ {final_stats['error']} checks failed",
            ""
        ])
    
    summary_lines.extend([
        "",
        "📁 Results: data/csv/checks.csv",
        f"📊 Status: {status_tracker.status_file}"
    ])
    
    print('\n'.join(summary_lines), flush=True)
    
    # Show error summary if there are errors
    if final_stats['error'] > 0:
        _show_error_summary()

def _calculate_time_stats_from_status(status_tracker: StatusTracker, limit: int = None, threads: int = 1) -> dict:
    """Calculate time statistics from status file with smart estimation"""
    try:
        if not status_tracker.status_file.exists():
            return {
                'rate': 'No data',
                'estimated_remaining': 'No data',
                'estimated_completion': 'No data',
                'success_eta': 'No data',
                'last_update': 'No data'
            }
        
        # Read status file to get timestamps and processed controls
        timestamps = []
        success_timestamps = []  # Track only successful completion timestamps
        total_entries = 0
        success_count = 0
        error_count = 0
        last_timestamp = None
        processed_control_ids = set()
        
        # Track unique tasks to avoid double-counting retries
        unique_tasks = {}  # task_key -> latest_status
        
        with open(status_tracker.status_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                total_entries += 1
                
                # Create unique task key: control_id-provider-resource_type
                task_key = f"{row['control_id']}-{row['provider']}-{row['resource_type']}"
                unique_tasks[task_key] = row['status']
                
                if row['status'] == 'success':
                    success_count += 1
                    # Track successful completion timestamps for success rate calculation
                    try:
                        success_timestamp = datetime.fromisoformat(row['timestamp'])
                        success_timestamps.append(success_timestamp)
                    except:
                        pass
                elif row['status'] == 'error':
                    error_count += 1
                
                # Track which controls have been processed
                try:
                    control_id = int(row['control_id'])
                    processed_control_ids.add(control_id)
                except:
                    pass
                
                try:
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    timestamps.append(timestamp)
                    if not last_timestamp or timestamp > last_timestamp:
                        last_timestamp = timestamp
                except:
                    continue
        
        # Count unique tasks by their latest status
        unique_success_count = 0
        unique_error_count = 0
        for task_key, status in unique_tasks.items():
            if status == 'success':
                unique_success_count += 1
            elif status == 'error':
                unique_error_count += 1
        
        # Only count successful entries as truly "completed" for progress calculation
        completed_entries = unique_success_count
        
        if len(timestamps) < 2:
            return {
                'rate': 'Insufficient data',
                'estimated_remaining': 'Calculating...' if unique_error_count > 0 else 'No data',
                'estimated_completion': 'Calculating...' if unique_error_count > 0 else 'No data',
                'success_eta': 'Calculating...' if unique_error_count > 0 else 'No data',
                'last_update': last_timestamp.strftime('%H:%M:%S') if last_timestamp else 'No data'
            }
        
        # Calculate processing rate based on all processed entries (both successful and failed)
        timestamps.sort()
        start_time = timestamps[0]
        end_time = timestamps[-1]
        duration = (end_time - start_time).total_seconds()
        
        if duration > 0:
            # Use total entries processed (successful + failed) for rate calculation
            # since both represent actual processing work done
            total_processed = unique_success_count + unique_error_count
            rate_per_second = total_processed / duration
            rate_per_minute = rate_per_second * 60
            rate_str = f"{rate_per_minute:.1f} tasks/min"
        else:
            rate_str = "∞ tasks/min"
        
        # Calculate success rate for second ETA
        success_eta_str = "No successful tasks yet"
        if len(success_timestamps) >= 2 and unique_error_count > 0:
            success_timestamps.sort()
            success_start = success_timestamps[0]
            success_end = success_timestamps[-1]
            success_duration = (success_end - success_start).total_seconds()
            
            if success_duration > 0:
                success_rate_per_second = len(success_timestamps) / success_duration
                success_rate_per_minute = success_rate_per_second * 60
                
                # Account for threading for success rate
                success_rate_with_threads = success_rate_per_second * threads
                
                # Time to complete all remaining failed tasks successfully
                remaining_failed_tasks = unique_error_count
                if remaining_failed_tasks > 0:
                    success_eta_seconds = remaining_failed_tasks / success_rate_with_threads
                    success_eta_hours = int(success_eta_seconds // 3600)
                    success_eta_minutes = int((success_eta_seconds % 3600) // 60)
                    success_eta_secs = int(success_eta_seconds % 60)
                    
                    success_completion_time = datetime.now() + timedelta(seconds=success_eta_seconds)
                    success_completion_str = success_completion_time.strftime('%H:%M:%S')
                    
                    success_eta_str = f"{success_eta_hours:02d}:{success_eta_minutes:02d}:{success_eta_secs:02d} (ETA: {success_completion_str})"
                else:
                    success_eta_str = "All tasks successful!"
        
        # Smart calculation of remaining work (existing logic)
        try:
            from con_mon_v2.utils.llm.generate import get_provider_resources_mapping
            from con_mon_v2.compliance import ControlLoader
            
            provider_resources = get_provider_resources_mapping()
            tasks_per_control = sum(len(resources) for resources in provider_resources.values())
            
            # Get all active controls
            controls = ControlLoader().load_all()
            active_controls = [c for c in controls if c.active]
            
            # Determine scope based on parameters
            if limit:
                # Case 1: Limited run - only estimate for the specified limit
                # Get the last processed control to determine where to start
                last_processed_control = status_tracker.get_last_processed_control()
                start_from = (last_processed_control + 1) if last_processed_control else 1
                
                # Filter controls to match the limit scope
                remaining_controls = [c for c in active_controls if c.id >= start_from][:limit]
                
                # Calculate remaining tasks for limited scope
                remaining_control_ids = {c.id for c in remaining_controls}
                already_processed_in_scope = len(processed_control_ids & remaining_control_ids)
                remaining_controls_to_process = len(remaining_control_ids) - already_processed_in_scope
                
                # Add back error entries that need to be retried
                remaining_tasks = remaining_controls_to_process * tasks_per_control + unique_error_count
                scope_description = f"limited to {limit} controls"
                
            else:
                # Case 2: Full run - estimate for all remaining unprocessed controls
                all_active_control_ids = {c.id for c in active_controls}
                unprocessed_control_ids = all_active_control_ids - processed_control_ids
                
                # Add back error entries that need to be retried
                remaining_tasks = len(unprocessed_control_ids) * tasks_per_control + unique_error_count
                scope_description = f"all remaining controls ({len(unprocessed_control_ids)} controls)"
            
            if remaining_tasks > 0 and rate_per_second > 0:
                # Account for threading - parallel processing reduces time
                estimated_remaining_seconds = remaining_tasks / (rate_per_second * threads)
                
                # Format remaining time
                remaining_hours = int(estimated_remaining_seconds // 3600)
                remaining_minutes = int((estimated_remaining_seconds % 3600) // 60)
                remaining_secs = int(estimated_remaining_seconds % 60)
                estimated_remaining = f"{remaining_hours:02d}:{remaining_minutes:02d}:{remaining_secs:02d}"
                
                # Calculate estimated completion time
                completion_time = datetime.now() + timedelta(seconds=estimated_remaining_seconds)
                completion_str = completion_time.strftime('%H:%M:%S')
                
                # Update rate display to show threading benefit
                if threads > 1:
                    effective_rate = rate_per_minute * threads
                    rate_str = f"{rate_per_minute:.1f} tasks/min × {threads} threads = {effective_rate:.1f} tasks/min"
                
            else:
                estimated_remaining = "Completed!" if remaining_tasks <= 0 and unique_error_count == 0 else "Calculating..."
                completion_str = "Completed!" if remaining_tasks <= 0 and unique_error_count == 0 else "Calculating..."
                
            # Add scope information to completion string
            if remaining_tasks > 0 or unique_error_count > 0:
                completion_str += f" ({scope_description})"
                if unique_error_count > 0:
                    completion_str += f" + {unique_error_count} retries"
            
        except Exception as e:
            estimated_remaining = f"Error: {str(e)[:30]}..."
            completion_str = "Unable to calculate"
        
        return {
            'rate': rate_str,
            'estimated_remaining': estimated_remaining,
            'estimated_completion': completion_str,
            'success_eta': success_eta_str,
            'last_update': last_timestamp.strftime('%H:%M:%S on %m/%d') if last_timestamp else 'No data'
        }
        
    except Exception as e:
        return {
            'rate': f'Error: {str(e)[:20]}...',
            'estimated_remaining': 'Error calculating',
            'estimated_completion': 'Error calculating',
            'success_eta': 'Error calculating',
            'last_update': 'Error'
        }

def _show_error_summary():
    """Show error summary table"""
    error_tracker = ErrorTracker()
    error_summary = error_tracker.get_error_summary()
    if error_summary:
        console.print("\n📊 [bold red]Error Summary:[/bold red]")
        error_table = Table(title="Error Types", box=box.ROUNDED)
        error_table.add_column("Error Type", style="red")
        error_table.add_column("Count", style="magenta")
        error_table.add_column("Percentage", style="yellow")
        
        total_errors = sum(error_summary.values())
        for error_type, count in error_summary.items():
            percentage = (count / total_errors) * 100 if total_errors > 0 else 0
            error_table.add_row(error_type, str(count), f"{percentage:.1f}%")
        
        console.print(error_table)

def main():
    """Main batch processing function"""
    parser = argparse.ArgumentParser(
        description="🚀 Batch Check Generation with Rich UI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python batch_generate_checks.py --limit 10 --db csv --threads 4
  python batch_generate_checks.py --error --db pgs
  python batch_generate_checks.py --show-progress
  python batch_generate_checks.py --fresh --attempts 3 --limit 5
        """
    )
    
    parser.add_argument("--limit", type=int, 
                       help="Number of controls to process (starts from last saved)")
    parser.add_argument("--db", choices=["csv", "pgs"], default="csv",
                       help="Database mode: csv or pgs (default: csv)")
    parser.add_argument("--error", action="store_true",
                       help="Retry only failed/error entries")
    parser.add_argument("--show-progress", action="store_true",
                       help="Show current progress statistics and exit")
    parser.add_argument("--threads", type=int, default=2,
                       help="Number of threads for processing (default: 2)")
    parser.add_argument("--fresh", action="store_true",
                       help="Start fresh, ignoring previous progress (clears status file)")
    parser.add_argument("--attempts", type=int, default=2,
                       help="Maximum number of regeneration attempts per check (default: 2)")
    
    args = parser.parse_args()
    
    # Setup rich console
    console.print(Panel.fit(
        "[bold blue]🚀 Batch Check Generation System[/bold blue]\n"
        "[cyan]Multi-provider compliance check generation with LLM[/cyan]",
        border_style="blue"
    ))
    
    # Initialize components
    status_tracker = StatusTracker()
    prompt_logger = PromptLogger()
    error_tracker = ErrorTracker()
    
    # Handle fresh start option
    if args.fresh:
        console.print("🆕 [yellow]Fresh start requested - clearing previous progress...[/yellow]")
        if status_tracker.status_file.exists():
            status_tracker.status_file.unlink()
            console.print("✅ [green]Previous status file cleared[/green]")
        # Reinitialize status tracker to create fresh CSV
        status_tracker = StatusTracker()
    
    # Show progress and exit if requested
    if args.show_progress:
        show_progress_stats(status_tracker, args.limit, args.threads)
        return 0
    
    # Setup database mode
    setup_database_mode(args.db)
    
    # Initialize statistics
    stats = ProcessingStats(start_time=datetime.now())
    
    try:
        if args.error:
            # Process error entries
            console.print("🔄 [yellow]Processing error entries...[/yellow]")
            error_entries = status_tracker.get_error_entries()
            console.print(f"Found {len(error_entries)} error entries to retry")
            
            if not error_entries:
                console.print("✅ [green]No error entries found[/green]")
                return 0
            
            # Load controls for error retry
            console.print("📋 [yellow]Loading controls for error retry...[/yellow]")
            loader = ControlLoader()
            all_controls = loader.load_all()
            control_dict = {c.id: c for c in all_controls}
            
            # Get provider mappings
            provider_resources = get_provider_resources_mapping()
            
            # Group error entries by control_id and resource info
            retry_tasks = []
            for entry in error_entries:
                control_id = int(entry['control_id'])
                provider = entry['provider']
                resource_type = entry['resource_type']
                
                # Find matching control
                if control_id not in control_dict:
                    console.print(f"⚠️ [yellow]Control ID {control_id} not found, skipping[/yellow]")
                    continue
                
                # Find matching connector type
                connector_type = None
                for ct, resources in provider_resources.items():
                    if ct.value == provider and resource_type in resources:
                        connector_type = ct
                        break
                
                if not connector_type:
                    console.print(f"⚠️ [yellow]Provider {provider} with resource {resource_type} not found, skipping[/yellow]")
                    continue
                
                retry_tasks.append({
                    'control': control_dict[control_id],
                    'connector_type': connector_type,
                    'resource_type': resource_type,
                    'attempts': int(entry.get('attempts', 1))
                })
            
            if not retry_tasks:
                console.print("⚠️ [yellow]No valid retry tasks found[/yellow]")
                return 0
            
            console.print(f"🎯 [green]Processing {len(retry_tasks)} retry tasks[/green]")
            stats.total_tasks = len(retry_tasks)
            stats.total_controls = len(set(task['control'].id for task in retry_tasks))
            
            # Process retry tasks with threading
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Retrying failed checks...", total=len(retry_tasks))
                
                with ThreadPoolExecutor(max_workers=args.threads) as executor:
                    futures = []
                    
                    # Submit retry tasks
                    for retry_task in retry_tasks:
                        future = executor.submit(
                            process_single_control_provider,
                            retry_task['control'], 
                            retry_task['connector_type'], 
                            retry_task['resource_type'],
                            status_tracker, 
                            prompt_logger, 
                            error_tracker, 
                            args.attempts
                        )
                        futures.append(future)
                    
                    # Process completed retry tasks
                    for future in as_completed(futures):
                        try:
                            success, check_id, error_msg = future.result()
                            stats.completed_tasks += 1
                            if success:
                                stats.successful_checks += 1
                                console.print(f"✅ [green]Retry successful: {check_id}[/green]")
                            else:
                                stats.failed_checks += 1
                                if error_msg:
                                    stats.error_checks += 1
                                    console.print(f"❌ [red]Retry failed: {error_msg}[/red]")
                        except Exception as e:
                            stats.completed_tasks += 1
                            stats.error_checks += 1
                            console.print(f"[red]❌ Retry task failed: {str(e)}[/red]")
                        
                        progress.advance(task)
            
            # Retry summary
            console.print("\n" + "="*60)
            console.print(f"🔄 [bold cyan]Error Retry Summary[/bold cyan]")
            console.print(f"✅ [green]Successful retries: {stats.successful_checks}[/green]")
            console.print(f"❌ [red]Failed retries: {stats.failed_checks}[/red]")
            console.print(f"⚠️ [yellow]Error retries: {stats.error_checks}[/yellow]")
            
            return 0
            
        else:
            # Normal processing
            start_from = None if args.fresh else status_tracker.get_last_processed_control()
            if start_from:
                console.print(f"🔄 [yellow]Resuming from control ID: {start_from + 1}[/yellow]")
                start_from += 1
            elif args.fresh:
                console.print("🆕 [green]Starting fresh from the beginning[/green]")
            
            # Load controls
            controls = load_controls(args.limit, start_from)
            stats.total_controls = len(controls)
            
            if not controls:
                console.print("ℹ️  [blue]No controls to process[/blue]")
                return 0
            
            # Get provider mappings
            provider_resources = get_provider_resources_mapping()
            stats.total_tasks = sum(len(resources) for resources in provider_resources.values()) * len(controls)
            
            console.print(f"🎯 [green]Processing {len(controls)} controls across {len(provider_resources)} providers[/green]")
            console.print(f"📋 [blue]Total tasks: {stats.total_tasks}[/blue]")
            console.print(f"🔄 [cyan]Max regeneration attempts per check: {args.attempts}[/cyan]")
            console.print(f"🕒 [yellow]Started at: {stats.start_time.strftime('%H:%M:%S')}[/yellow]")
            
            # Process with threading
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Processing checks...", total=stats.total_tasks)
                
                # Add a periodic update to show time statistics
                def update_progress_description():
                    elapsed = stats.get_elapsed_time()
                    rate = stats.get_processing_rate()
                    eta = stats.get_estimated_completion()
                    progress.update(task, description=f"Processing checks... ⏱️ {elapsed} | 🚀 {rate} | ⏰ {eta}")
                
                with ThreadPoolExecutor(max_workers=args.threads) as executor:
                    futures = []
                    
                    # Submit all tasks
                    for control in controls:
                        for connector_type, resource_models in provider_resources.items():
                            for resource_model in resource_models:
                                future = executor.submit(
                                    process_single_control_provider,
                                    control, connector_type, resource_model,
                                    status_tracker, prompt_logger, error_tracker, args.attempts  # Pass max_attempts
                                )
                                futures.append(future)
                    
                    # Process completed tasks
                    for future in as_completed(futures):
                        try:
                            success, check_id, error_msg = future.result()
                            stats.completed_tasks += 1  # Track completed tasks
                            if success:
                                stats.successful_checks += 1
                            else:
                                stats.failed_checks += 1
                                if error_msg:
                                    stats.error_checks += 1
                        except Exception as e:
                            stats.completed_tasks += 1  # Track completed tasks even on exception
                            stats.error_checks += 1
                            console.print(f"[red]❌ Task failed: {str(e)}[/red]")
                        
                        progress.advance(task)
                        # Update progress description with time info every 5 tasks
                        if stats.completed_tasks % 5 == 0 or stats.completed_tasks == stats.total_tasks:
                            update_progress_description()
            
            # Final statistics
            console.print("\n" + "="*60)
            console.print(create_progress_table(stats))
            
            # Error summary
            error_summary = error_tracker.get_error_summary()
            if error_summary:
                console.print("\n📊 [bold red]Error Summary:[/bold red]")
                error_table = Table(title="Error Types", box=box.ROUNDED)
                error_table.add_column("Error Type", style="red")
                error_table.add_column("Count", style="magenta")
                error_table.add_column("Percentage", style="yellow")
                
                total_errors = sum(error_summary.values())
                for error_type, count in error_summary.items():
                    percentage = (count / total_errors) * 100 if total_errors > 0 else 0
                    error_table.add_row(error_type, str(count), f"{percentage:.1f}%")
                
                console.print(error_table)
            
            # Success summary
            if stats.successful_checks > 0:
                console.print(f"\n✅ [bold green]Successfully generated {stats.successful_checks} checks![/bold green]")
            if stats.failed_checks > 0:
                console.print(f"❌ [bold red]{stats.failed_checks} checks failed[/bold red]")
            if stats.error_checks > 0:
                console.print(f"⚠️  [bold yellow]{stats.error_checks} checks had errors[/bold yellow]")
            
            console.print(f"\n📁 [cyan]Prompts saved to: data/generate_checks/prompts/[/cyan]")
            console.print(f"📊 [cyan]Status tracking: {status_tracker.status_file}[/cyan]")
            console.print(f"🐛 [cyan]Error details: {error_tracker.error_file}[/cyan]")
    
    except KeyboardInterrupt:
        console.print("\n⏹️  [yellow]Processing interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n💥 [red]Fatal error: {str(e)}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 