#!/usr/bin/env python3
"""
Resource Selection Generation Script

This script processes benchmark checks and identifies valid resource types:
1. Load enriched checks from benchmark processing output
2. Determine valid/invalid resource types for each check using LLM
3. Save results in structured YAML format under check_guidance/data/benchmark/

Usage Examples:
    # Generate resource selection for OWASP checks
    python generate_resource_selection.py --name "owasp"
    python generate_resource_selection.py --name "nist" 
    python generate_resource_selection.py --name "iso27001"
    
    # Multi-threaded processing for faster completion
    python generate_resource_selection.py --name "owasp" --threads 8
    
    # Custom data directory
    python generate_resource_selection.py --name "owasp" --data-dir /custom/path

Prerequisites:
    Before running this script, ensure benchmark data has been generated:
    python llm_generator/benchmark/scripts/generate_metadata_and_checks.py --name "<benchmark_name>"
"""

import argparse
import json
import logging
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from llm_generator.check_guidance.services import ResourceSelectionService
from llm_generator.benchmark.models import Check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResourceSelectionProcessor:
    """Main processor for resource selection workflow."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        self.service = ResourceSelectionService()

    def process_benchmark_checks(
            self,
            benchmark_name: str,
            thread_count: int = 1,
            data_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Process all checks from a benchmark through resource selection.

        Args:
            benchmark_name: Name of the benchmark (e.g., 'owasp', 'nist')
            thread_count: Number of threads for parallel processing
            data_dir: Optional custom data directory

        Returns:
            Results dictionary with processed checks
        """
        logger.info(f"🚀 Starting resource selection for benchmark: {benchmark_name}")

        # Load checks from benchmark processing output
        checks = self._load_benchmark_checks(benchmark_name, data_dir)
        logger.info(f"📋 Loaded {len(checks)} checks from benchmark data")

        # Process checks through resource selection
        if thread_count == 1:
            # Single-threaded processing
            enriched_checks = []
            for i, check in enumerate(checks):
                logger.info(f"Processing check {i + 1}/{len(checks)}: {check.unique_id}")
                enriched_check = self.service.select_valid_resources(check)
                enriched_checks.append(enriched_check)
                break
        else:
            # Multi-threaded processing
            logger.info(f"🧵 Using {thread_count} threads for parallel processing")
            enriched_checks = []
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                # Submit all tasks
                future_to_check = {
                    executor.submit(self.service.select_valid_resources, check): check 
                    for check in checks
                }
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_check):
                    completed += 1
                    check = future_to_check[future]

                    result = future.result()
                    enriched_checks.append(result)
                    logger.info(f"✅ Completed {completed}/{len(checks)}: {check.unique_id}")

        # Generate summary statistics
        total_checks = len(enriched_checks)
        total_valid_resources = sum(len(check.valid_resources) for check in enriched_checks)
        total_invalid_resources = sum(len(check.invalid_resources) for check in enriched_checks)
        avg_valid_per_check = total_valid_resources / total_checks if total_checks > 0 else 0

        # Compile results
        results = {
            'benchmark_name': benchmark_name,
            'processing_info': {
                'processing_date': datetime.now().isoformat(),
                'input_checks_count': len(checks),
                'output_checks_count': len(enriched_checks),
                'thread_count': thread_count,
                'processing_status': 'completed'
            },
            'enriched_checks': enriched_checks,
            'summary': {
                'total_checks': total_checks,
                'total_valid_resources': total_valid_resources,
                'total_invalid_resources': total_invalid_resources,
                'avg_valid_resources_per_check': round(avg_valid_per_check, 2)
            }
        }

        logger.info(f"🎉 Resource selection completed! {total_checks} checks processed")
        return results

    def _load_benchmark_checks(self, benchmark_name: str, data_dir: Optional[Path] = None) -> List[Check]:
        """Load enriched checks from benchmark processing output."""
        if data_dir is None:
            # Default to benchmark data directory
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent.parent / "benchmark" / "data"

        # Construct path to benchmark checks
        benchmark_dir = data_dir / "benchmarks" / benchmark_name
        checks_dir = benchmark_dir / "checks"

        if not checks_dir.exists():
            raise FileNotFoundError(
                f"Benchmark checks directory not found: {checks_dir}\n"
                f"Please run: python llm_generator/benchmark/scripts/generate_metadata_and_checks.py --name \"{benchmark_name}\""
            )

        # Load all check files
        checks = []
        check_files = list(checks_dir.glob("*.yaml"))
        
        if not check_files:
            raise FileNotFoundError(
                f"No check files found in: {checks_dir}\n"
                f"Please run: python llm_generator/benchmark/scripts/generate_metadata_and_checks.py --name \"{benchmark_name}\""
            )

        for check_file in check_files:
            with open(check_file, 'r', encoding='utf-8') as f:
                check_data = yaml.safe_load(f)
            
            # Convert to Check object
            check = self._dict_to_check(check_data)
            checks.append(check)

        logger.info(f"📂 Loaded {len(checks)} checks from {checks_dir}")
        return checks

    def _dict_to_check(self, check_data: Dict[str, Any]) -> Check:
        """Convert dictionary data to Check object."""
        # Extract only fields that exist in the Check model
        valid_fields = {}
        check_fields = Check.model_fields
        
        for key, value in check_data.items():
            if key in check_fields:
                valid_fields[key] = value
        
        return Check(**valid_fields)

    def save_structured_data(
            self, 
            results: Dict[str, Any], 
            benchmark_name: str, 
            base_data_dir: Optional[Path] = None
    ) -> Path:
        """
        Save processing results in structured YAML format.

        Structure:
        check_guidance/data/benchmark/<benchmark_name>/
        ├── metadata.yaml       # Processing info and summary
        └── checks/             # Individual enriched check files
            ├── <check_id_1>_resources.yaml
            ├── <check_id_2>_resources.yaml
            └── ...
        """
        if base_data_dir is None:
            # Default to check_guidance/data
            script_dir = Path(__file__).parent
            base_data_dir = script_dir.parent / "data"

        # Create output directory
        output_dir = base_data_dir / "benchmark" / self._sanitize_name(benchmark_name)
        output_dir.mkdir(parents=True, exist_ok=True)

        checks_dir = output_dir / "checks"
        checks_dir.mkdir(exist_ok=True)

        logger.info(f"💾 Saving structured data to: {output_dir}")

        # Save metadata.yaml
        metadata = {
            'benchmark_name': results['benchmark_name'],
            'processing_info': results['processing_info'],
            'summary': results['summary'],
            'workflow_stage': 'Resource Selection (Step 1)',
            'output_description': 'SystemEnrichedCheck objects with valid/invalid resource mappings'
        }

        metadata_file = output_dir / "metadata.yaml"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        logger.info(f"✅ Saved metadata: {metadata_file}")

        # Save individual check files
        checks_saved = 0
        for check in results['enriched_checks']:
            check_id = check.unique_id or f"check_{checks_saved + 1}"
            check_filename = f"{self._sanitize_filename(check_id)}_resources.yaml"
            check_file = checks_dir / check_filename

            with open(check_file, 'w', encoding='utf-8') as f:
                yaml.dump(check.model_dump(), f, default_flow_style=False, sort_keys=False)
            checks_saved += 1

        logger.info(f"✅ Saved {checks_saved} enriched check files to: {checks_dir}")
        return output_dir

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for use as directory name."""
        import re
        sanitized = re.sub(r'[^\w\-_.]', '_', name.lower())
        sanitized = re.sub(r'_+', '_', sanitized)
        return sanitized.strip('_')

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for file system compatibility."""
        import re
        sanitized = re.sub(r'[^\w\-_.]', '_', filename)
        sanitized = re.sub(r'_+', '_', sanitized)
        return sanitized.strip('_')

    def print_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of processing results."""
        print("\n" + "=" * 80)
        print("🔍 RESOURCE SELECTION PROCESSING SUMMARY")
        print("=" * 80)

        # Basic info
        processing_info = results['processing_info']
        print(f"📅 Processed: {processing_info['processing_date'][:19].replace('T', ' ')}")
        print(f"📊 Benchmark: {results['benchmark_name']}")
        print(f"📊 Input Checks: {processing_info['input_checks_count']}")
        print(f"📊 Output Checks: {processing_info['output_checks_count']}")
        print(f"🧵 Threads: {processing_info['thread_count']}")

        # Summary stats
        summary = results['summary']
        print(f"\n📈 RESOURCE ANALYSIS:")
        print(f"  • Total Checks: {summary['total_checks']}")
        print(f"  • Total Valid Resources: {summary['total_valid_resources']}")
        print(f"  • Total Invalid Resources: {summary['total_invalid_resources']}")
        print(f"  • Avg Valid Resources/Check: {summary['avg_valid_resources_per_check']}")

        print("\n" + "=" * 80)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate resource selection analysis for benchmark checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Benchmark name (required)
    parser.add_argument('--name', '-n', type=str, required=True,
                       help='Benchmark name (e.g., "owasp", "nist", "iso27001")')
    
    # Optional settings
    parser.add_argument('--data-dir', type=Path,
                       help='Base directory for structured data (default: llm_generator/check_guidance/data)')
    
    # Processing options
    parser.add_argument('--threads', type=int, default=1,
                       help='Number of threads to use for parallel check processing (default: 1)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress summary output')

    args = parser.parse_args()
    
    # Validate thread count
    if args.threads < 1:
        logger.error("❌ Thread count must be at least 1")
        sys.exit(1)
    if args.threads > 8:
        logger.warning(f"⚠️  Large thread count ({args.threads}) will overwhelm LLM API. Consider using fewer than 8 threads.")
    
    # Initialize processor
    processor = ResourceSelectionProcessor(verbose=args.verbose)

    # Process benchmark checks through resource selection
    results = processor.process_benchmark_checks(
        benchmark_name=args.name,
        thread_count=args.threads,
        data_dir=args.data_dir
    )

    # Always save structured data
    output_dir = processor.save_structured_data(
        results,
        args.name,
        args.data_dir
    )

    # Show results unless quiet
    if not args.quiet:
        print(f"\n📁 Structured data saved to: {output_dir}")
        print(f"   📋 metadata.yaml")
        print(f"   📂 checks/ ({len(results['enriched_checks'])} files)")
        processor.print_summary(results)


if __name__ == "__main__":
    main()
