#!/usr/bin/env python3
"""
Generate Executable Checks - Section 3 Implementation

This script implements the complete Section 3 pipeline:
1. Load enriched benchmark checks from Section 1+2
2. Generate executable Python code for each check  
3. Validate generated code against real resources
4. Repair failed checks through iterative improvement
5. Save successful checks to database
6. Generate comprehensive coverage reports

Usage:
    python generate_executable_checks.py --benchmark "OWASP Top 10 2021" --version "2021"
    python generate_executable_checks.py --input benchmark_results.json --threads 4
    python generate_executable_checks.py --benchmark "NIST Cybersecurity Framework" --providers github aws
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Table
from rich.panel import Panel
from rich import box

# Local imports
from llm_generator.check_generation import (
    CheckGenerationService, 
    check_generation_service,
    Section3Results
)
from llm_generator.benchmark import (
    BenchmarkService,
    benchmark_service,
    Benchmark,
    Check
)

console = Console()
logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('section3_generation.log')
        ]
    )

def load_benchmark_results(input_file: Path) -> tuple[Benchmark, List[Check]]:
    """
    Load benchmark and enriched checks from JSON file.
    
    Args:
        input_file: Path to JSON file with benchmark results from Section 1+2
        
    Returns:
        Tuple of (Benchmark, List[Check])
    """
    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Reconstruct objects from JSON
        benchmark = Benchmark(**data['benchmark'])
        enriched_checks = [Check(**check_data) for check_data in data['enriched_checks']]
        
        console.print(f"📁 Loaded {len(enriched_checks)} enriched checks from {input_file}")
        return benchmark, enriched_checks
        
    except Exception as e:
        console.print(f"❌ [red]Error loading benchmark results: {e}[/red]")
        raise

def load_existing_benchmark_files(benchmark_name: str) -> tuple[Benchmark, List[Check]]:
    """
    Load existing benchmark files from data/benchmarks/ directory.
    
    Args:
        benchmark_name: Name of the benchmark (e.g., "owasp")
        
    Returns:
        Tuple of (Benchmark, List[Check]) loaded from existing files
    """
    benchmark_dir = Path(f"data/benchmarks/{benchmark_name.lower()}")
    
    if not benchmark_dir.exists():
        raise FileNotFoundError(f"No existing benchmark found at {benchmark_dir}")
    
    console.print(f"📁 Loading existing benchmark from {benchmark_dir}")
    
    # Load metadata
    metadata_file = benchmark_dir / "metadata.yaml"
    coverage_file = benchmark_dir / "coverage.yaml"
    checks_dir = benchmark_dir / "checks"
    
    if not all([metadata_file.exists(), coverage_file.exists(), checks_dir.exists()]):
        raise FileNotFoundError(f"Incomplete benchmark files in {benchmark_dir}")
    
    # Load YAML files (skip metadata.yaml which has Python objects)
    import yaml
    
    # Load coverage (this should be clean YAML)
    with open(coverage_file, 'r') as f:
        coverage = yaml.safe_load(f)
    
    # Load check files directly
    check_files = list(checks_dir.glob("*.yaml"))
    console.print(f"📊 Found {len(check_files)} existing checks")
    
    # Create simplified Benchmark object (minimal required fields)
    benchmark = Benchmark(
        unique_id=f"{benchmark_name.lower()}-existing",
        name=benchmark_name.upper(),
        version="existing", 
        literature=f"Loaded from existing benchmark files in {benchmark_dir}",
        check_names=[],  # Not needed for Section 3
        checks=[],
        metadata={
            "total_checks_extracted": coverage['total_checks_extracted'],
            "extraction_date": datetime.now().isoformat(),
            "coverage_metrics": [],  # Empty list as expected by Benchmark model
            "coverage_data": coverage,  # Store coverage data separately
            "loaded_from": str(benchmark_dir)
        }
    )
    
    # Load actual check content from YAML files AND their resource mappings
    checks = []
    loaded_count = 0
    
    # Also need to check for check_guidance directory
    resource_guidance_dir = benchmark_dir / "check_guidance" / "checks"
    
    for check_file in check_files:
        try:
            with open(check_file, 'r') as f:
                check_data = yaml.safe_load(f)
            
            check_id = check_data.get('unique_id', f"{benchmark_name.lower()}-{loaded_count+1:03d}")
            
            # Load valid resources for this check (if available)
            valid_resources = []
            if resource_guidance_dir.exists():
                # Convert check_id to match filename pattern
                # Pattern: (GDPR,-CCPA) -> _GDPR_-CCPA (keep - after comma, no trailing _)
                import re
                filename_safe_id = re.sub(r'\(([^)]+)\)', r'_\1', check_id)
                filename_safe_id = filename_safe_id.replace(', ', '_-').replace(',', '_')
                
                # Look for corresponding resource file with various naming patterns
                resource_file_patterns = [
                    resource_guidance_dir / f"{check_id}_resources.yaml",
                    resource_guidance_dir / f"{filename_safe_id}_resources.yaml",
                    resource_guidance_dir / f"{check_data.get('name', '').replace(' ', '-')}_resources.yaml"
                ]
                
                for resource_file in resource_file_patterns:
                    if resource_file.exists():
                        try:
                            with open(resource_file, 'r') as rf:
                                resource_data = yaml.safe_load(rf)
                                valid_resources = resource_data.get('valid_resources', [])
                                console.print(f"🎯 Found {len(valid_resources)} valid resources for {check_id}")
                                break
                        except Exception as resource_err:
                            console.print(f"⚠️  Failed to load resources for {check_id}: {resource_err}")
                
                # If still not found, try glob pattern matching for more flexibility
                if not valid_resources:
                    import glob
                    pattern = str(resource_guidance_dir / f"*{check_id.split('-')[-1]}*_resources.yaml")
                    matching_files = glob.glob(pattern)
                    if matching_files:
                        try:
                            with open(matching_files[0], 'r') as rf:
                                resource_data = yaml.safe_load(rf)
                                valid_resources = resource_data.get('valid_resources', [])
                                console.print(f"🎯 Found {len(valid_resources)} valid resources for {check_id} (glob match)")
                        except Exception as resource_err:
                            console.print(f"⚠️  Failed to load resources for {check_id} (glob): {resource_err}")
            
            # Create Check object from loaded data 
            # Note: Store valid resources info in tags since Check model doesn't have metadata field
            tags = check_data.get('tags', ['existing', benchmark_name.lower()])
            if valid_resources:
                tags.append(f"valid_resources:{len(valid_resources)}")
                
            check = Check(
                unique_id=check_id,
                name=check_data.get('name', check_file.stem),
                literature=check_data.get('literature', ''),
                controls=check_data.get('controls', []),  
                frameworks=check_data.get('frameworks', ["NIST-800-171-rev2"]),
                benchmark_mapping=check_data.get('benchmark_mapping', []),
                mapping_confidence=check_data.get('mapping_confidence', 0.97),
                category=check_data.get('category', 'security'),
                severity=check_data.get('severity', 'medium'),
                tags=tags,
                extracted_at=datetime.now(),
                mapped_at=datetime.now()
            )
            
            # Store valid resources info externally for Section 3 access
            check._valid_resources = valid_resources  # Store as private attribute
            checks.append(check)
            loaded_count += 1
            
        except Exception as e:
            console.print(f"⚠️  Failed to load {check_file.name}: {e}")
            continue
    
    console.print(f"✅ Loaded benchmark: {benchmark.name} with {len(checks)} checks")
    console.print(f"📈 Previous control mapping: {coverage['coverage_percentages']['control_mapping']:.1f}%")
    
    return benchmark, checks

def generate_fresh_benchmark(
    benchmark_name: str, 
    benchmark_version: str,
    thread_count: int = 1
) -> tuple[Benchmark, List[Check]]:
    """
    Generate fresh benchmark and enriched checks using Section 1+2 pipeline.
    
    Args:
        benchmark_name: Name of the benchmark to generate
        benchmark_version: Version of the benchmark
        thread_count: Number of threads for parallel processing
        
    Returns:
        Tuple of (Benchmark, List[Check])
    """
    console.print(f"🚀 Generating fresh benchmark: {benchmark_name} {benchmark_version}")
    
    # Section 1: Generate benchmark metadata
    console.print("📊 [cyan]Section 1: Generating benchmark literature and check names...[/cyan]")
    benchmark = benchmark_service.generate_metadata(benchmark_name, benchmark_version)
    console.print(f"✅ Generated {len(benchmark.check_names)} check names")
    
    # Section 2: Enrich checks with control mappings
    console.print("🔗 [cyan]Section 2: Enriching checks with control mappings...[/cyan]")
    enriched_checks = benchmark_service.generate_checks_metadata(
        benchmark, thread_count=thread_count
    )
    console.print(f"✅ Enriched {len(enriched_checks)} checks with control mappings")
    
    # Update benchmark with coverage metrics
    coverage_metrics = benchmark_service.generate_coverage_report(enriched_checks)
    updated_benchmark = benchmark_service.update_benchmark_coverage_metrics(
        benchmark, coverage_metrics
    )
    
    console.print(f"📈 Control mapping coverage: {coverage_metrics.coverage_percentages['control_mapping']:.1f}%")
    
    return updated_benchmark, enriched_checks

def save_results(results: Section3Results, output_file: Path):
    """
    Save Section 3 results to JSON file.
    
    Args:
        results: Section 3 results to save
        output_file: Path to output JSON file
    """
    try:
        # Convert to JSON-serializable format
        output_data = {
            'section3_results': results.model_dump(),
            'generated_at': datetime.now().isoformat(),
            'summary': results.summary
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        console.print(f"💾 [green]Results saved to {output_file}[/green]")
        
    except Exception as e:
        console.print(f"❌ [red]Error saving results: {e}[/red]")

def create_coverage_table(coverage: 'ImplementationCoverage') -> Table:
    """Create a rich table showing implementation coverage"""
    table = Table(title="📊 Section 3 Implementation Coverage", box=box.ROUNDED)
    
    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Count", style="magenta")
    table.add_column("Percentage", style="green")
    
    # Input metrics
    table.add_row("Total Benchmark Checks", str(coverage.total_benchmark_checks), "100%")
    table.add_row("Total Generation Tasks", str(coverage.total_generation_tasks), "100%")
    
    # Generation metrics
    gen_pct = (coverage.successfully_generated / coverage.total_generation_tasks * 100) if coverage.total_generation_tasks > 0 else 0
    table.add_row("Successfully Generated", str(coverage.successfully_generated), f"{gen_pct:.1f}%")
    
    # Validation metrics
    val_pct = (coverage.validation_passes / coverage.total_generation_tasks * 100) if coverage.total_generation_tasks > 0 else 0
    table.add_row("Validation Passes", str(coverage.validation_passes), f"{val_pct:.1f}%")
    
    # Repair metrics
    if coverage.repair_attempts_made > 0:
        repair_pct = (coverage.successful_repairs / coverage.validation_failures * 100) if coverage.validation_failures > 0 else 0
        table.add_row("Successful Repairs", str(coverage.successful_repairs), f"{repair_pct:.1f}%")
    
    # Database metrics
    db_pct = (coverage.saved_to_database / coverage.total_generation_tasks * 100) if coverage.total_generation_tasks > 0 else 0
    table.add_row("Saved to Database", str(coverage.saved_to_database), f"{db_pct:.1f}%")
    
    # Overall success
    table.add_row("─" * 20, "─" * 10, "─" * 10)  # Separator
    table.add_row("Overall Success Rate", str(coverage.saved_to_database), f"{coverage.overall_success_rate:.1f}%")
    
    return table

def create_provider_table(results: Section3Results) -> Table:
    """Create a rich table showing results by provider"""
    table = Table(title="🔗 Results by Provider", box=box.ROUNDED)
    
    table.add_column("Provider", style="cyan")
    table.add_column("Total", style="blue")
    table.add_column("Successful", style="green")
    table.add_column("Failed", style="red")
    table.add_column("Success Rate", style="magenta")
    
    provider_stats = results.get_provider_summary()
    
    for provider, stats in provider_stats.items():
        success_rate = (stats['successful'] / stats['total'] * 100) if stats['total'] > 0 else 0
        table.add_row(
            provider.title(),
            str(stats['total']),
            str(stats['successful']),
            str(stats['failed']),
            f"{success_rate:.1f}%"
        )
    
    return table

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="🚀 Generate Executable Checks - Section 3 Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from scratch
  python generate_executable_checks.py --benchmark "OWASP Top 10 2021" --version "2021" --threads 4

  # Load from existing results
  python generate_executable_checks.py --input benchmark_results.json --threads 2
  
  # Target specific providers
  python generate_executable_checks.py --benchmark "NIST CSF" --providers github aws --max-repairs 3
  
  # Verbose output for debugging
  python generate_executable_checks.py --input results.json --verbose --threads 1
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--input", type=Path, 
                           help="JSON file with benchmark results from Section 1+2")
    input_group.add_argument("--name", type=str,
                           help="Benchmark name to generate from scratch")
    input_group.add_argument("--benchmark", type=str,
                           help="Benchmark name to generate from scratch (alias for --name)")
    
    parser.add_argument("--version", type=str, default="latest",
                       help="Benchmark version (required with --name or --benchmark)")
    
    # Processing options
    parser.add_argument("--threads", type=int, default=2,
                       help="Number of parallel threads (default: 2)")
    parser.add_argument("--max-repairs", type=int, default=2,
                       help="Maximum repair attempts per check (default: 2)")
    parser.add_argument("--providers", nargs='+', 
                       choices=["github", "aws", "azure", "google"],
                       help="Target specific providers (default: all)")
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit number of checks to process (default: all)")
    
    # Output options
    parser.add_argument("--output", type=Path, 
                       default=Path("section3_results.json"),
                       help="Output file for results (default: section3_results.json)")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Validate arguments  
    benchmark_name = args.name or args.benchmark
    if benchmark_name and args.version == "latest" and benchmark_name.lower() not in ["owasp"]:
        parser.error("--version is required when using --name or --benchmark (or use a recognized shorthand like 'owasp')")
    
    # Setup
    setup_logging(args.verbose)
    console.print(Panel.fit(
        "[bold blue]🚀 Section 3: Generate Executable Checks[/bold blue]\n"
        "[cyan]Converting benchmark metadata to validated Python checks[/cyan]",
        border_style="blue"
    ))
    
    try:
        # Step 1: Load or generate benchmark data
        if args.input:
            benchmark, enriched_checks = load_benchmark_results(args.input)
        else:
            benchmark_name = args.name or args.benchmark
            
            # Check if existing benchmark files exist first
            existing_dir = Path(f"data/benchmarks/{benchmark_name.lower()}")
            
            if existing_dir.exists():
                console.print(f"🔍 Found existing benchmark files for '{benchmark_name}' - loading instead of regenerating")
                benchmark, enriched_checks = load_existing_benchmark_files(benchmark_name)
            else:
                console.print(f"📝 No existing files found for '{benchmark_name}' - generating fresh benchmark")
                
                # Handle common shorthand names
                if benchmark_name.lower() == "owasp":
                    benchmark_name = "OWASP Top 10 2021"
                    if args.version == "latest":
                        args.version = "2021"
                
                benchmark, enriched_checks = generate_fresh_benchmark(
                    benchmark_name, args.version, args.threads
                )
        
        # Apply limit if specified
        if args.limit and args.limit < len(enriched_checks):
            enriched_checks = enriched_checks[:args.limit]
            console.print(f"⚡ Limited to first {args.limit} checks")
        
        console.print(f"🎯 Processing {len(enriched_checks)} enriched checks")
        console.print(f"🔧 Using {args.threads} threads, max {args.max_repairs} repair attempts per check")
        
        if args.providers:
            console.print(f"🎯 Targeting providers: {', '.join(args.providers)}")
        
        # Step 2: Generate executable checks
        console.print("\n🔄 [cyan]Section 3: Generating executable checks...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # Start progress tracking
            task = progress.add_task("Generating executable checks...", total=None)
            
            results = check_generation_service.generate_executable_checks(
                benchmark=benchmark,
                enriched_checks=enriched_checks,
                thread_count=args.threads,
                max_repair_attempts=args.max_repairs,
                target_providers=args.providers
            )
            
            progress.update(task, completed=True, description="Generation completed!")
        
        # Step 3: Display results
        console.print("\n" + "="*80)
        console.print(create_coverage_table(results.implementation_coverage))
        console.print()
        console.print(create_provider_table(results))
        
        # Step 4: Show error summary if there are failures
        if results.implementation_coverage.common_errors:
            console.print("\n📊 [bold red]Common Errors:[/bold red]")
            error_table = Table(title="Error Analysis", box=box.ROUNDED)
            error_table.add_column("Error Type", style="red")
            error_table.add_column("Count", style="magenta")
            
            for error_type, count in list(results.implementation_coverage.common_errors.items())[:5]:
                error_table.add_row(error_type, str(count))
            
            console.print(error_table)
        
        # Step 5: Success summary
        console.print(f"\n✅ [bold green]Successfully generated {len(results.get_successful_checks())} executable checks![/bold green]")
        if results.get_failed_checks():
            console.print(f"❌ [bold red]{len(results.get_failed_checks())} checks failed generation/validation[/bold red]")
        
        console.print(f"⏱️  [cyan]Total processing time: {results.processing_duration_minutes:.1f} minutes[/cyan]")
        console.print(f"🎯 [cyan]Overall success rate: {results.implementation_coverage.overall_success_rate:.1f}%[/cyan]")
        
        # Step 6: Save results
        save_results(results, args.output)
        
        console.print(f"\n📊 [cyan]Detailed results saved to: {args.output}[/cyan]")
        console.print("🎉 [bold green]Section 3 implementation completed![/bold green]")
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n⏹️  [yellow]Processing interrupted by user[/yellow]")
        return 1
    except Exception as e:
        console.print(f"\n💥 [red]Fatal error: {str(e)}[/red]")
        if args.verbose:
            import traceback
            console.print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit(main())
