#!/usr/bin/env python3
"""
System Guidance Generation Script - Section 2 Implementation

This script processes enriched benchmark checks and generates system-compatible 
resource mappings and targeted guidance:

1. Step 1: Expand to Resource Types and Field Paths
2. Step 2: Coverage on System Compatibility  

Usage Examples:
    # Process enriched checks from benchmark processing
    python generate_system_guidance.py --benchmark-dir /path/to/owasp-top-10-2021
    
    # Process from JSON file
    python generate_system_guidance.py --checks-file processed_checks.json
    
    # Custom output directory
    python generate_system_guidance.py --benchmark-dir /path/to/benchmark --output-dir /custom/path
    
    # Verbose mode
    python generate_system_guidance.py --benchmark-dir /path/to/benchmark --verbose

Example Input Sources:
    • Output from llm_generator/benchmark processing
    • JSON files containing enriched Check objects
    • Direct benchmark directory with checks/ subdirectory
"""

import argparse
import json
import logging
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from llm_generator.check_guidance import (
    enrich_checks_with_system_resources,
    generate_system_compatibility_coverage,
)
from llm_generator.benchmark.models import Check

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SystemGuidanceProcessor:
    """Main class for processing enriched checks through Section 2 workflow."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def process_checks(
            self,
            enriched_checks: List[Check],
    ) -> Dict[str, Any]:
        """
        Execute the complete Section 2 workflow.

        Args:
            enriched_checks: List of enriched Check objects from Section 1

        Returns:
            Complete processing results with system compatibility info
        """
        logger.info(f"🚀 Starting system guidance processing for {len(enriched_checks)} checks")

        # Step 1: Expand to Resource Types and Field Paths
        logger.info("🔗 Step 1: Enriching checks with system resource types and field paths...")
        system_enriched_checks = enrich_checks_with_system_resources(enriched_checks)

        compatible_count = sum(
            1 for check in system_enriched_checks 
            if check.resource_type and check.resource_type != 'No Compatible Resource'
        )
        logger.info(f"✅ Successfully mapped {compatible_count}/{len(system_enriched_checks)} checks to system resources")

        # Step 2: Generate Coverage Report
        logger.info("📊 Step 2: Generating system compatibility coverage...")
        coverage_report = generate_system_compatibility_coverage(system_enriched_checks)

        resource_pct = coverage_report.coverage_percentages['resource_types']
        field_path_pct = coverage_report.coverage_percentages['field_paths']
        guidance_pct = coverage_report.coverage_percentages['targeted_guidance']
        logger.info(f"✅ Coverage: {resource_pct:.1f}% resources, {field_path_pct:.1f}% field paths, {guidance_pct:.1f}% guidance")

        # Combine results
        complete_result = {
            'system_enriched_checks': system_enriched_checks,
            'coverage_report': coverage_report,
            'processing_info': {
                'processing_date': datetime.now().isoformat(),
                'input_checks_count': len(enriched_checks),
                'output_checks_count': len(system_enriched_checks),
            },
            'summary': {
                'total_checks_processed': len(enriched_checks),
                'checks_with_system_compatibility': compatible_count,
                'checks_with_field_paths': coverage_report.checks_with_field_paths,
                'checks_with_guidance': coverage_report.checks_with_targeted_guidance,
                'average_field_paths_per_check': coverage_report.quality_metrics['avg_field_paths_per_check'],
                'processing_status': 'completed'
            }
        }

        logger.info("🎉 System guidance processing completed successfully!")
        return complete_result

    def load_checks_from_benchmark_dir(self, benchmark_dir: Path) -> List[Check]:
        """Load enriched checks from benchmark processing output directory."""
        checks_dir = benchmark_dir / "checks"
        if not checks_dir.exists():
            raise FileNotFoundError(f"Checks directory not found: {checks_dir}")

        checks = []
        for check_file in checks_dir.glob("*.yaml"):
            try:
                with open(check_file, 'r', encoding='utf-8') as f:
                    check_data = yaml.safe_load(f)
                    
                # Convert YAML data to Check object
                check = self._dict_to_check(check_data)
                checks.append(check)
                
            except Exception as e:
                logger.error(f"Failed to load check from {check_file}: {e}")

        logger.info(f"Loaded {len(checks)} checks from {benchmark_dir}")
        return checks

    def load_checks_from_json(self, json_file: Path) -> List[Check]:
        """Load enriched checks from JSON file."""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        checks = []
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Direct list of check objects
            checks_data = data
        elif 'processed_checks' in data:
            # Benchmark processing output format
            checks_data = data['processed_checks']
        elif 'checks' in data:
            # Alternative format
            checks_data = data['checks']
        else:
            raise ValueError("Unable to find check data in JSON file")

        for check_data in checks_data:
            try:
                check = self._dict_to_check(check_data)
                checks.append(check)
            except Exception as e:
                logger.error(f"Failed to parse check data: {e}")

        logger.info(f"Loaded {len(checks)} checks from {json_file}")
        return checks

    def _dict_to_check(self, check_data: Dict[str, Any]) -> Check:
        """Convert dictionary data to Check object."""
        return Check(**{
            key: value for key, value in check_data.items()
            if key in Check.__fields__
        })

    def save_results(self, results: Dict[str, Any], output_path: Path):
        """Save processing results to JSON file."""
        logger.info(f"💾 Saving results to: {output_path}")

        # Convert Pydantic models to dicts for JSON serialization
        serializable_results = {
            'system_enriched_checks': [check.model_dump() for check in results['system_enriched_checks']],
            'coverage_report': results['coverage_report'].model_dump(),
            'processing_info': results['processing_info'],
            'summary': results['summary']
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False, default=str)
        logger.info(f"✅ Results saved successfully")

    def save_structured_data(self, results: Dict[str, Any], benchmark_name: str, base_output_dir: Path = None):
        """
        Save processing results in structured YAML format.

        Structure:
        data/system_guidance/<benchmark_name>/
        ├── metadata.yaml       # Processing info and summary
        ├── coverage.yaml       # System compatibility coverage report
        └── checks/             # Individual system-enriched check files
            ├── <check_id_1>_system.yaml
            ├── <check_id_2>_system.yaml
            └── ...
        """
        if base_output_dir is None:
            # Default to check_guidance/data
            script_dir = Path(__file__).parent
            base_output_dir = script_dir.parent / "data"

        # Create output directory
        output_dir = base_output_dir / "system_guidance" / self._sanitize_name(benchmark_name)
        output_dir.mkdir(parents=True, exist_ok=True)

        checks_dir = output_dir / "checks"
        checks_dir.mkdir(exist_ok=True)

        logger.info(f"📁 Saving structured data to: {output_dir}")

        # Save metadata.yaml
        metadata = {
            'processing_info': results['processing_info'],
            'summary': results['summary'],
            'section': 'Section 2: System Compatibility',
            'processing_completed_at': results['processing_info']['processing_date']
        }

        metadata_file = output_dir / "metadata.yaml"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        logger.info(f"✅ Saved metadata: {metadata_file}")

        # Save coverage.yaml
        coverage_file = output_dir / "coverage.yaml"
        with open(coverage_file, 'w', encoding='utf-8') as f:
            yaml.dump(results['coverage_report'].model_dump(), f, default_flow_style=False, sort_keys=False)
        logger.info(f"✅ Saved coverage: {coverage_file}")

        # Save individual check files
        checks_saved = 0
        for check in results['system_enriched_checks']:
            check_id = check.unique_id or f"check_{checks_saved + 1}"
            check_filename = f"{self._sanitize_filename(check_id)}_system.yaml"
            check_file = checks_dir / check_filename

            with open(check_file, 'w', encoding='utf-8') as f:
                yaml.dump(check.model_dump(), f, default_flow_style=False, sort_keys=False)
            checks_saved += 1

        logger.info(f"✅ Saved {checks_saved} system-enriched check files to: {checks_dir}")
        logger.info(f"🎉 Structured data saved successfully!")

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
        print("🔗 SYSTEM COMPATIBILITY PROCESSING SUMMARY")
        print("=" * 80)

        # Basic info
        processing_info = results['processing_info']
        print(f"📅 Processed: {processing_info['processing_date'][:19].replace('T', ' ')}")
        print(f"📊 Input Checks: {processing_info['input_checks_count']}")
        print(f"📊 Output Checks: {processing_info['output_checks_count']}")

        # Summary stats
        summary = results['summary']
        print("\n📈 RESULTS:")
        print(f"  • Total Checks Processed: {summary['total_checks_processed']}")
        print(f"  • System Compatible: {summary['checks_with_system_compatibility']}")
        print(f"  • With Field Paths: {summary['checks_with_field_paths']}")
        print(f"  • With Guidance: {summary['checks_with_guidance']}")
        print(f"  • Avg Field Paths/Check: {summary['average_field_paths_per_check']:.2f}")

        # Coverage breakdown
        coverage = results['coverage_report'].coverage_percentages
        print("\n📊 SYSTEM COMPATIBILITY COVERAGE:")
        print(f"  • Resource Types: {coverage['resource_types']:.1f}%")
        print(f"  • Field Paths: {coverage['field_paths']:.1f}%")
        print(f"  • Targeted Guidance: {coverage['targeted_guidance']:.1f}%")

        # Provider breakdown
        provider_coverage = results['coverage_report'].provider_coverage
        print("\n🏢 PROVIDER BREAKDOWN:")
        print(f"  • GitHub: {provider_coverage['github_checks']} checks")
        print(f"  • AWS: {provider_coverage['aws_checks']} checks")
        print(f"  • Google: {provider_coverage['google_checks']} checks")
        print(f"  • Multi-Provider: {provider_coverage['multi_provider_checks']} checks")

        print("\n" + "=" * 80)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate system-compatible guidance from enriched benchmark checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Input options (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--benchmark-dir', type=Path,
                           help='Directory containing benchmark processing output (with checks/ subdirectory)')
    input_group.add_argument('--checks-file', type=Path,
                           help='JSON file containing enriched check data')

    # Output options
    parser.add_argument('--output-dir', type=Path,
                       help='Base directory for structured data output (default: check_guidance/data)')
    parser.add_argument('--output-file', type=Path,
                       help='JSON file to save complete results')

    # Processing options
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress summary output')

    args = parser.parse_args()

    # Initialize processor
    processor = SystemGuidanceProcessor(verbose=args.verbose)

    # Load enriched checks
    if args.benchmark_dir:
        enriched_checks = processor.load_checks_from_benchmark_dir(args.benchmark_dir)
        benchmark_name = args.benchmark_dir.name
    elif args.checks_file:
        enriched_checks = processor.load_checks_from_json(args.checks_file)
        benchmark_name = args.checks_file.stem

    # Process checks through Section 2 workflow
    results = processor.process_checks(enriched_checks)

    # Save results
    if args.output_file:
        processor.save_results(results, args.output_file)

    # Always save structured data
    output_dir = processor.save_structured_data(
        results,
        benchmark_name,
        args.output_dir
    )

    # Show results unless quiet
    if not args.quiet:
        print(f"\n📁 Structured data saved to: {output_dir}")
        print(f"   📋 metadata.yaml")
        print(f"   📊 coverage.yaml")
        print(f"   📂 checks/ ({len(results['system_enriched_checks'])} files)")
        processor.print_summary(results)


if __name__ == "__main__":
    main()
