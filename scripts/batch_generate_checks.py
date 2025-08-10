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
from datetime import datetime
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
    generate_checks_for_all_providers,
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
        try:
            with open(self.status_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats['total'] += 1
                    if row['status'] == 'success':
                        stats['success'] += 1
                    elif row['status'] == 'error':
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
        
        # Convert Check object to database format
        check_data = {
            'id': check.id,
            'name': check.name,
            'description': check.description,
            'output_statements': json.dumps(check.output_statements.model_dump()),
            'fix_details': json.dumps(check.fix_details.model_dump()),
            'metadata': json.dumps(check.metadata.model_dump()),
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
    max_attempts: int = 3
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Process a single control for a specific provider/resource"""
    
    provider_name = connector_type.value
    control_name = control.control_name
    
    try:
        console.print(f"🔄 [cyan]Processing {control_name} | {provider_name} | {resource_model_name}[/cyan]")
        
        # Generate check
        check = generate_check(
            control_name=control.control_name,
            control_text=control.control_text or "",
            control_title=control.control_long_name or control.control_name,
            control_id=control.id,
            connector_type=connector_type,
            resource_model_name=resource_model_name
        )
        
        # Log prompts (if available)
        if hasattr(check, '_raw_yaml'):
            prompt_logger.log_prompt(
                control_name, provider_name, resource_model_name,
                "Prompt not captured", check._raw_yaml
            )
        
        # Evaluate check
        check_results = evaluate_check_against_rc(check)
        
        # Check if valid
        successful_evaluations = sum(1 for r in check_results if r.passed is not None)
        
        if successful_evaluations > 0:
            # Save to database
            if save_check_to_database(check, control.id):
                status_tracker.update_status(
                    control.id, control_name, provider_name, 
                    resource_model_name, 'success', check.id
                )
                return True, check.id, None
            else:
                error_msg = "Database save failed"
                status_tracker.update_status(
                    control.id, control_name, provider_name,
                    resource_model_name, 'error', None, error_msg
                )
                return False, None, error_msg
        else:
            error_msg = "Check validation failed - no successful evaluations"
            status_tracker.update_status(
                control.id, control_name, provider_name,
                resource_model_name, 'error', None, error_msg
            )
            return False, None, error_msg
            
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
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
    table.add_column("Percentage", style="green")
    
    if stats.total_controls > 0:
        processed_pct = (stats.processed_controls / stats.total_controls) * 100
        success_pct = (stats.successful_checks / max(1, stats.successful_checks + stats.failed_checks)) * 100
    else:
        processed_pct = 0
        success_pct = 0
    
    table.add_row("Total Controls", str(stats.total_controls), "100%")
    table.add_row("Processed Controls", str(stats.processed_controls), f"{processed_pct:.1f}%")
    table.add_row("Successful Checks", str(stats.successful_checks), f"{success_pct:.1f}%")
    table.add_row("Failed Checks", str(stats.failed_checks), f"{100-success_pct:.1f}%")
    table.add_row("Error Checks", str(stats.error_checks), "")
    
    if stats.start_time:
        elapsed = datetime.now() - stats.start_time
        table.add_row("Elapsed Time", str(elapsed).split('.')[0], "")
    
    return table

def show_progress_stats(status_tracker: StatusTracker):
    """Show current progress statistics"""
    stats = status_tracker.get_statistics()
    
    table = Table(title="📈 Current Progress", box=box.ROUNDED)
    table.add_column("Status", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_column("Percentage", style="green")
    
    total = stats['total']
    if total > 0:
        success_pct = (stats['success'] / total) * 100
        error_pct = (stats['error'] / total) * 100
        pending_pct = (stats['pending'] / total) * 100
    else:
        success_pct = error_pct = pending_pct = 0
    
    table.add_row("✅ Success", str(stats['success']), f"{success_pct:.1f}%")
    table.add_row("❌ Errors", str(stats['error']), f"{error_pct:.1f}%")
    table.add_row("⏳ Pending", str(stats['pending']), f"{pending_pct:.1f}%")
    table.add_row("📊 Total", str(total), "100%")
    
    console.print(table)

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
    
    # Show progress and exit if requested
    if args.show_progress:
        show_progress_stats(status_tracker)
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
                
            # TODO: Implement error retry logic
            console.print("⚠️  [yellow]Error retry not implemented yet[/yellow]")
            return 0
            
        else:
            # Normal processing
            start_from = status_tracker.get_last_processed_control()
            if start_from:
                console.print(f"🔄 [yellow]Resuming from control ID: {start_from + 1}[/yellow]")
                start_from += 1
            
            # Load controls
            controls = load_controls(args.limit, start_from)
            stats.total_controls = len(controls)
            
            if not controls:
                console.print("ℹ️  [blue]No controls to process[/blue]")
                return 0
            
            # Get provider mappings
            provider_resources = get_provider_resources_mapping()
            total_tasks = sum(len(resources) for resources in provider_resources.values()) * len(controls)
            
            console.print(f"🎯 [green]Processing {len(controls)} controls across {len(provider_resources)} providers[/green]")
            console.print(f"📋 [blue]Total tasks: {total_tasks}[/blue]")
            
            # Process with threading
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("Processing checks...", total=total_tasks)
                
                with ThreadPoolExecutor(max_workers=args.threads) as executor:
                    futures = []
                    
                    # Submit all tasks
                    for control in controls:
                        for connector_type, resource_models in provider_resources.items():
                            for resource_model in resource_models:
                                future = executor.submit(
                                    process_single_control_provider,
                                    control, connector_type, resource_model,
                                    status_tracker, prompt_logger
                                )
                                futures.append(future)
                    
                    # Process completed tasks
                    for future in as_completed(futures):
                        try:
                            success, check_id, error_msg = future.result()
                            if success:
                                stats.successful_checks += 1
                            else:
                                stats.failed_checks += 1
                                if error_msg:
                                    stats.error_checks += 1
                        except Exception as e:
                            stats.error_checks += 1
                            console.print(f"[red]❌ Task failed: {str(e)}[/red]")
                        
                        progress.advance(task)
            
            # Final statistics
            console.print("\n" + "="*60)
            console.print(create_progress_table(stats))
            
            # Success summary
            if stats.successful_checks > 0:
                console.print(f"\n✅ [bold green]Successfully generated {stats.successful_checks} checks![/bold green]")
            if stats.failed_checks > 0:
                console.print(f"❌ [bold red]{stats.failed_checks} checks failed[/bold red]")
            if stats.error_checks > 0:
                console.print(f"⚠️  [bold yellow]{stats.error_checks} checks had errors[/bold yellow]")
            
            console.print(f"\n📁 [cyan]Prompts saved to: data/generate_checks/prompts/[/cyan]")
            console.print(f"📊 [cyan]Status tracking: {status_tracker.status_file}[/cyan]")
    
    except KeyboardInterrupt:
        console.print("\n⏹️  [yellow]Processing interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n💥 [red]Fatal error: {str(e)}[/red]")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 