#!/usr/bin/env python3
"""
Benchmark Metadata and Checks Generation Script

This script processes benchmark documents and saves structured data:
1. Extract Checks Literature from benchmark documents
2. Map to Controls and Existing Benchmarks  
3. Generate Coverage Reporting
4. Save results in structured YAML format under data/benchmarks/

Usage Examples:
    # Generate comprehensive benchmark processing
    python generate_metadata_and_checks.py --name "OWASP Top 10 2021"
    python generate_metadata_and_checks.py --name "PCI DSS v4.0" 
    python generate_metadata_and_checks.py --name "NIST Cybersecurity Framework"
    
    # With specific version
    python generate_metadata_and_checks.py --name "OWASP Top 10" --version "2021"
    
    # Multi-threaded processing for faster completion
    python generate_metadata_and_checks.py --name "OWASP Top 10 2021" --threads 8
    
    # Custom data directory
    python generate_metadata_and_checks.py --name "ISO 27001" --data-dir /custom/path

Example Benchmark Sources (all use the same generic processing):
    • OWASP Top 10 2021
    • Mitre ATT&CK v13
    • PCI DSS v4.0
    • NIST Cybersecurity Framework v1.1
    • ISO 27001:2022
    • SOC 2 Type II
    • Any custom benchmark name you choose
"""

import argparse
import json
import logging
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from llm_generator.benchmark import (
    generate_metadata,
    generate_checks_metadata,
    generate_coverage_report,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Example usage constants for supported benchmarks
EXAMPLE_benchmark_nameS = [
    "OWASP Top 10 2021",
    "Mitre ATT&CK v13",
    "PCI DSS v4.0",
    "NIST Cybersecurity Framework v1.1",
    "ISO 27001:2022",
    "SOC 2 Type II"
]


class BenchmarkProcessor:
    """Main class for processing benchmark documents through the complete workflow."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    def process_benchmark(
            self,
            benchmark_name: str,
            benchmark_version: str | None = None,
            thread_count: int = 1,
    ) -> Dict[str, Any]:
        """
        Execute the complete Section 1 workflow.

        Args:
            benchmark_name: Source name (e.g., "OWASP Top 10 2021")
            benchmark_version: Version identifier
            thread_count: Number of threads to use for parallel processing

        Returns:
            Complete processing results with all three steps
        """
        logger.info(f"🚀 Starting benchmark processing for: {benchmark_name}")

        # Step 1: Extract Checks Literature
        logger.info("📋 Step 1: Extracting checks from benchmark text...")
        benchmark = generate_metadata(
            benchmark_name=benchmark_name,
            benchmark_version=benchmark_version,
        )

        logger.info(f"✅ Extracted {len(benchmark.check_names)} check names")
        if not benchmark.check_names:
            raise RuntimeError(f'No check names found for Benchmark {benchmark_name}:{benchmark_version}')

        # Step 2: Map to Controls and Existing Benchmarks
        logger.info("🔗 Step 2: Mapping checks to controls...")
        if thread_count > 1:
            logger.info(f"🧵 Using {thread_count} threads for parallel processing")
        enriched_checks = generate_checks_metadata(benchmark, thread_count)

        mapped_count = sum(1 for check in enriched_checks if check.controls)
        logger.info(f"✅ Successfully mapped {mapped_count}/{len(enriched_checks)} checks to controls")

        # Step 3: Generate Coverage Report
        logger.info("📊 Step 3: Generating coverage report...")
        coverage_report = generate_coverage_report(enriched_checks)

        control_pct = coverage_report.coverage_percentages.control_mapping
        benchmark_pct = coverage_report.coverage_percentages.benchmark_mapping
        logger.info(f"✅ Coverage: {control_pct:.1f}% controls, {benchmark_pct:.1f}% benchmarks")

        # Combine results as structured object
        complete_result = {
            'benchmark': benchmark,
            'processed_checks': enriched_checks,
            'coverage_report': coverage_report,
            'benchmark_info': {
                'name': benchmark_name,
                'version': benchmark_version,
                'processing_date': datetime.now().isoformat(),
            },
            'summary': {
                'total_checks_extracted': len(benchmark.check_names),
                'checks_mapped_to_controls': mapped_count,
                'average_mapping_confidence': self._calculate_average_confidence(enriched_checks),
                'unique_frameworks': len(set().union(*[check.frameworks or [] for check in enriched_checks])),
                'processing_status': 'completed'
            }
        }

        logger.info("🎉 Benchmark processing completed successfully!")
        return complete_result


    def _calculate_average_confidence(self, checks: list) -> float:
        """Calculate average mapping confidence across all checks."""
        confidences = [check.mapping_confidence or 0 for check in checks]
        return sum(confidences) / len(confidences) if confidences else 0.0

    def save_results(self, results: Dict[str, Any], output_path: Path):
        """Save processing results to JSON file (legacy format)."""
        logger.info(f"💾 Saving results to: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ Results saved successfully")

    def save_structured_data(self, results: Dict[str, Any], benchmark_name: str, base_data_dir: Path = None):
        """
        Save processing results in structured YAML format.

        Structure:
        data/benchmarks/<benchmark_name>/
        ├── metadata.yaml       # Benchmark info and extraction metadata
        ├── coverage.yaml       # Coverage report
        └── checks/             # Individual check files
            ├── <check_id_1>.yaml
            ├── <check_id_2>.yaml
            └── ...
        """
        if base_data_dir is None:
            # Default to centralized data/benchmarks directory at project root
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent.parent  # Navigate up to project root
            base_data_dir = project_root / "data"

        # Create benchmark directory
        benchmark_dir = base_data_dir / "benchmarks" / self._sanitize_benchmark_name(benchmark_name)
        benchmark_dir.mkdir(parents=True, exist_ok=True)

        checks_dir = benchmark_dir / "checks"
        checks_dir.mkdir(exist_ok=True)

        logger.info(f"📁 Saving structured data to: {benchmark_dir}")

        # Save metadata.yaml
        benchmark = results['benchmark']
        metadata = {
            'benchmark_info': results['benchmark_info'],
            'extraction_metadata': benchmark.metadata,
            'summary': results['summary'],
            'processing_completed_at': results['benchmark_info']['processing_date']
        }

        metadata_file = benchmark_dir / "metadata.yaml"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
        logger.info(f"✅ Saved metadata: {metadata_file}")

        # Save coverage.yaml
        coverage_file = benchmark_dir / "coverage.yaml"
        with open(coverage_file, 'w', encoding='utf-8') as f:
            yaml.dump(results['coverage_report'].model_dump(), f, default_flow_style=False, sort_keys=False)
        logger.info(f"✅ Saved coverage: {coverage_file}")

        # Save individual check files
        checks_saved = 0
        for check in results['processed_checks']:
            check_id = check.unique_id or f"check_{checks_saved + 1}"
            check_filename = f"{self._sanitize_filename(check_id)}.yaml"
            check_file = checks_dir / check_filename

            with open(check_file, 'w', encoding='utf-8') as f:
                yaml.dump(check.model_dump(), f, default_flow_style=False, sort_keys=False)
            checks_saved += 1

        logger.info(f"✅ Saved {checks_saved} check files to: {checks_dir}")
        logger.info(f"🎉 Structured data saved successfully!")

        return benchmark_dir

    def _sanitize_benchmark_name(self, name: str) -> str:
        """Sanitize benchmark name for use as directory name."""
        # Replace spaces and special characters with underscores
        import re
        sanitized = re.sub(r'[^\w\-_.]', '_', name.lower())
        sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
        return sanitized.strip('_')

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for file system compatibility."""
        import re
        sanitized = re.sub(r'[^\w\-_.]', '_', filename)
        sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
        return sanitized.strip('_')

    def print_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of processing results."""
        print("\n" + "=" * 80)
        print("📊 BENCHMARK PROCESSING SUMMARY")
        print("=" * 80)

        # Basic info
        benchmark_info = results['benchmark_info']
        benchmark = results['benchmark']
        print(f"📋 Benchmark: {benchmark_info['name']}:{benchmark_info['version']}")
        print(f"📅 Processed: {benchmark_info['processing_date'][:19].replace('T', ' ')}")
        print(f"📄 Literature: {benchmark.metadata.total_checks_extracted} check names extracted")

        # Summary stats
        summary = results['summary']
        print("\n📈 RESULTS:")
        print(f"  • Checks Extracted: {summary['total_checks_extracted']}")
        print(f"  • Mapped to Controls: {summary['checks_mapped_to_controls']}")
        print(f"  • Avg Confidence: {summary['average_mapping_confidence']:.2f}")
        print(f"  • Frameworks: {summary['unique_frameworks']}")

        # Coverage breakdown
        coverage = results['coverage_report'].coverage_percentages
        print("\n📊 COVERAGE:")
        print(f"  • Extraction: {coverage.extraction:.1f}%")
        print(f"  • Control Mapping: {coverage.control_mapping:.1f}%")
        print(f"  • Benchmark Mapping: {coverage.benchmark_mapping:.1f}%")

        # Top mapped checks
        checks = results['processed_checks']
        mapped_checks = [c for c in checks if c.controls]

        if mapped_checks:
            print(f"\n🔗 TOP MAPPED CHECKS:")
            for i, check in enumerate(sorted(
                    mapped_checks,
                    key=lambda x: x.mapping_confidence or 0,
                    reverse=True
            )[:5], 1):
                controls = ', '.join(check.controls[:3] if check.controls else [])
                confidence = check.mapping_confidence or 0
                print(f"  {i}. {check.unique_id or 'N/A'} → [{controls}] ({confidence:.2f})")

        print("\n" + "=" * 80)


# Removed load_benchmark_text function - no longer needed in 3-step architecture



def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate metadata and checks from benchmark documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Benchmark info (required)
    examples_text = f"Examples: {', '.join(EXAMPLE_benchmark_nameS[:3])}, etc."
    parser.add_argument('--name', '-n', type=str, required=True,
                       help=f'Benchmark name. {examples_text}')
    
    # Optional settings
    parser.add_argument('--version', '-v', type=str, default='latest',
                       help='Benchmark version (default: latest)')
    parser.add_argument('--data-dir', type=Path,
                       help='Base directory for structured data (default: data/ at project root)')
    
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
    if args.threads > 32:
        logger.warning(f"⚠️  Large thread count ({args.threads}) may overwhelm LLM API. Consider using fewer threads.")
    
    # Initialize processor
    processor = BenchmarkProcessor(verbose=args.verbose)

    benchmark_name = args.name
    benchmark_version = args.version

    # Process benchmark using 3-step architecture
    results = processor.process_benchmark(
        benchmark_name=benchmark_name,
        benchmark_version=benchmark_version,
        thread_count=args.threads
    )

    # Always save structured data (main purpose of the script)
    benchmark_dir = processor.save_structured_data(
        results,
        benchmark_name,
        args.data_dir
    )

    # Show results unless quiet
    if not args.quiet:
        print(f"\n📁 Structured data saved to: {benchmark_dir}")
        print(f"   📋 metadata.yaml")
        print(f"   📊 coverage.yaml")
        print(f"   📂 checks/ ({len(results['processed_checks'])} files)")
        processor.print_summary(results)



if __name__ == "__main__":
    main()
