#!/usr/bin/env python3
"""
Benchmark Metadata and Checks Generation Script

This script implements the complete Section 1 workflow:
1. Extract Checks Literature from benchmark documents
2. Map to Controls and Existing Benchmarks  
3. Generate Coverage Reporting

Usage Examples:
    # Process from file and save structured data
    python generate_metadata_and_checks.py --source "OWASP Top 10 2021" --file example_benchmark.txt --save-structured
    
    # Process with direct text input
    python generate_metadata_and_checks.py --source "Custom Benchmark" --text "Your benchmark text here"
    
    # Interactive mode with prompts
    python generate_metadata_and_checks.py --interactive --save-structured
    
    # Save to custom location
    python generate_metadata_and_checks.py --source "PCI DSS v4.0" --file pci_requirements.txt --save-structured --data-dir /custom/path

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
EXAMPLE_BENCHMARK_SOURCES = [
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
    
    def process_benchmark(self, 
                         benchmark_text: str,
                         benchmark_source: str,
                         benchmark_version: str = "latest",
                         extraction_context: str = "") -> Dict[str, Any]:
        """
        Execute the complete Section 1 workflow.
        
        Args:
            benchmark_text: Raw benchmark document text
            benchmark_source: Source name (e.g., "OWASP Top 10 2021") 
            benchmark_version: Version identifier
            extraction_context: Additional context for extraction
            
        Returns:
            Complete processing results with all three steps
        """
        logger.info(f"🚀 Starting benchmark processing for: {benchmark_source}")
        logger.info(f"📄 Document length: {len(benchmark_text)} characters")
        
        try:
            # Step 1: Extract Checks Literature
            logger.info("📋 Step 1: Extracting checks from benchmark text...")
            extraction_result = generate_metadata(
                benchmark_text=benchmark_text,
                benchmark_source=benchmark_source,
                benchmark_version=benchmark_version,
                extraction_context=extraction_context
            )
            
            extracted_checks = extraction_result.get('checks', [])
            logger.info(f"✅ Extracted {len(extracted_checks)} checks")
            
            if self.verbose:
                for i, check in enumerate(extracted_checks[:3], 1):  # Show first 3
                    logger.debug(f"  Check {i}: {check.get('check_id')} - {check.get('title')}")
                if len(extracted_checks) > 3:
                    logger.debug(f"  ... and {len(extracted_checks) - 3} more checks")
            
            # Step 2: Map to Controls and Existing Benchmarks
            logger.info("🔗 Step 2: Mapping checks to controls...")
            enriched_checks = generate_checks_metadata(extracted_checks)
            
            mapped_count = sum(1 for check in enriched_checks if check.get('controls'))
            logger.info(f"✅ Successfully mapped {mapped_count}/{len(enriched_checks)} checks to controls")
            
            if self.verbose:
                for check in enriched_checks[:3]:  # Show first 3
                    controls = check.get('controls', [])
                    confidence = check.get('mapping_confidence', 0)
                    logger.debug(f"  {check.get('check_id')}: {len(controls)} controls (confidence: {confidence})")
            
            # Step 3: Generate Coverage Report
            logger.info("📊 Step 3: Generating coverage report...")
            coverage_report = generate_coverage_report(enriched_checks)
            
            control_pct = coverage_report['coverage_percentages']['control_mapping']
            benchmark_pct = coverage_report['coverage_percentages']['benchmark_mapping']
            logger.info(f"✅ Coverage: {control_pct:.1f}% controls, {benchmark_pct:.1f}% benchmarks")
            
            # Combine results
            complete_result = {
                'benchmark_info': {
                    'source': benchmark_source,
                    'version': benchmark_version,
                    'processing_date': datetime.now().isoformat(),
                    'document_length': len(benchmark_text)
                },
                
                # Step 1 Results
                'extraction_metadata': extraction_result.get('metadata', {}),
                
                # Step 2 Results
                'processed_checks': enriched_checks,
                
                # Step 3 Results
                'coverage_report': coverage_report,
                
                # Summary
                'summary': {
                    'total_checks_extracted': len(extracted_checks),
                    'checks_mapped_to_controls': mapped_count,
                    'average_mapping_confidence': self._calculate_average_confidence(enriched_checks),
                    'unique_frameworks': len(set().union(*[check.get('frameworks', []) for check in enriched_checks])),
                    'processing_status': 'completed'
                }
            }
            
            logger.info("🎉 Benchmark processing completed successfully!")
            return complete_result
            
        except Exception as e:
            logger.error(f"❌ Error during benchmark processing: {e}")
            if self.verbose:
                import traceback
                logger.debug(traceback.format_exc())
            raise
    
    def _calculate_average_confidence(self, checks: list) -> float:
        """Calculate average mapping confidence across all checks."""
        confidences = [check.get('mapping_confidence', 0) for check in checks]
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    def save_results(self, results: Dict[str, Any], output_path: Path):
        """Save processing results to JSON file (legacy format)."""
        logger.info(f"💾 Saving results to: {output_path}")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Results saved successfully")
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
            raise
    
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
            # Default to llm_generator/benchmark/data
            script_dir = Path(__file__).parent
            base_data_dir = script_dir.parent / "data"
        
        # Create benchmark directory
        benchmark_dir = base_data_dir / "benchmarks" / self._sanitize_benchmark_name(benchmark_name)
        benchmark_dir.mkdir(parents=True, exist_ok=True)
        
        checks_dir = benchmark_dir / "checks"
        checks_dir.mkdir(exist_ok=True)
        
        logger.info(f"📁 Saving structured data to: {benchmark_dir}")
        
        try:
            # Save metadata.yaml
            metadata = {
                'benchmark_info': results['benchmark_info'],
                'extraction_metadata': results['extraction_metadata'],
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
                yaml.dump(results['coverage_report'], f, default_flow_style=False, sort_keys=False)
            logger.info(f"✅ Saved coverage: {coverage_file}")
            
            # Save individual check files
            checks_saved = 0
            for check in results['processed_checks']:
                check_id = check.get('check_id', f"check_{checks_saved + 1}")
                check_filename = f"{self._sanitize_filename(check_id)}.yaml"
                check_file = checks_dir / check_filename
                
                with open(check_file, 'w', encoding='utf-8') as f:
                    yaml.dump(check, f, default_flow_style=False, sort_keys=False)
                checks_saved += 1
            
            logger.info(f"✅ Saved {checks_saved} check files to: {checks_dir}")
            logger.info(f"🎉 Structured data saved successfully!")
            
            return benchmark_dir
            
        except Exception as e:
            logger.error(f"❌ Error saving structured data: {e}")
            raise
    
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
        print("\n" + "="*80)
        print("📊 BENCHMARK PROCESSING SUMMARY")
        print("="*80)
        
        # Basic info
        info = results['benchmark_info']
        print(f"📋 Benchmark: {info['source']} (v{info['version']})")
        print(f"📅 Processed: {info['processing_date'][:19].replace('T', ' ')}")
        print(f"📄 Document: {info['document_length']:,} characters")
        
        # Summary stats
        summary = results['summary']
        print(f"\n📈 RESULTS:")
        print(f"  • Checks Extracted: {summary['total_checks_extracted']}")
        print(f"  • Mapped to Controls: {summary['checks_mapped_to_controls']}")
        print(f"  • Avg Confidence: {summary['average_mapping_confidence']:.2f}")
        print(f"  • Frameworks: {summary['unique_frameworks']}")
        
        # Coverage breakdown
        coverage = results['coverage_report']['coverage_percentages']
        print(f"\n📊 COVERAGE:")
        print(f"  • Control Mapping: {coverage['control_mapping']:.1f}%")
        print(f"  • Benchmark Mapping: {coverage['benchmark_mapping']:.1f}%")
        
        # Top mapped checks
        checks = results['processed_checks']
        mapped_checks = [c for c in checks if c.get('controls')]
        
        if mapped_checks:
            print(f"\n🔗 TOP MAPPED CHECKS:")
            for i, check in enumerate(sorted(mapped_checks, 
                                           key=lambda x: x.get('mapping_confidence', 0), 
                                           reverse=True)[:5], 1):
                controls = ', '.join(check.get('controls', [])[:3])
                confidence = check.get('mapping_confidence', 0)
                print(f"  {i}. {check.get('check_id', 'N/A')} → [{controls}] ({confidence:.2f})")
        
        # Unmapped suggestions
        unmapped = []
        for check in checks:
            unmapped.extend(check.get('unmapped_suggested_controls', []))
        
        if unmapped:
            unique_unmapped = list(set(unmapped))[:10]  # Top 10 unique unmapped
            print(f"\n⚠️  UNMAPPED CONTROL SUGGESTIONS:")
            for control in unique_unmapped:
                print(f"  • {control}")
            if len(unmapped) > 10:
                print(f"  ... and {len(unmapped) - 10} more")
        
        print("\n" + "="*80)


def load_benchmark_text(file_path: Path) -> str:
    """Load benchmark text from file."""
    try:
        logger.info(f"📖 Loading benchmark text from: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read().strip()
        logger.info(f"✅ Loaded {len(text)} characters")
        return text
    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"❌ Error loading file: {e}")
        raise


def interactive_mode() -> tuple:
    """Interactive mode for inputting benchmark information."""
    print("\n🎯 INTERACTIVE BENCHMARK PROCESSING")
    print("=" * 50)
    
    # Show available examples
    print("\n📋 Example benchmark sources (all use same generic processing):")
    for i, source in enumerate(EXAMPLE_BENCHMARK_SOURCES, 1):
        print(f"  {i}. {source}")
    
    # Get benchmark source
    while True:
        source = input(f"\n📝 Enter benchmark source (or number 1-{len(EXAMPLE_BENCHMARK_SOURCES)}): ").strip()
        
        if source.isdigit() and 1 <= int(source) <= len(EXAMPLE_BENCHMARK_SOURCES):
            source = EXAMPLE_BENCHMARK_SOURCES[int(source) - 1]
            break
        elif source:
            break
        else:
            print("❌ Please enter a valid source")
    
    # Get version
    version = input("📅 Enter version (default: 'latest'): ").strip() or "latest"
    
    # Get text input method
    print("\n📄 Choose text input method:")
    print("  1. Enter text directly")
    print("  2. Load from file")
    
    while True:
        choice = input("Choose (1-2): ").strip()
        if choice in ['1', '2']:
            break
        print("❌ Please enter 1 or 2")
    
    if choice == '1':
        print("\n📝 Enter benchmark text (press Ctrl+D when done):")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        text = '\n'.join(lines).strip()
        
        if not text:
            print("❌ No text entered")
            sys.exit(1)
    
    else:
        while True:
            file_path = input("📁 Enter file path: ").strip()
            if file_path and Path(file_path).exists():
                text = load_benchmark_text(Path(file_path))
                break
            else:
                print("❌ File not found")
    
    return source, version, text


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate metadata and checks from benchmark documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=False)
    input_group.add_argument('--file', '-f', type=Path, 
                           help='Path to benchmark document file')
    input_group.add_argument('--text', '-t', type=str,
                           help='Benchmark text directly as string')
    input_group.add_argument('--interactive', '-i', action='store_true',
                           help='Interactive mode with prompts')
    
    # Benchmark info
    examples_text = f"Examples: {', '.join(EXAMPLE_BENCHMARK_SOURCES[:3])}, etc."
    parser.add_argument('--source', '-s', type=str,
                       help=f'Benchmark source name. {examples_text} (Note: All benchmarks use the same generic processing)')
    parser.add_argument('--version', '-v', type=str, default='latest',
                       help='Benchmark version (default: latest)')
    parser.add_argument('--context', '-c', type=str, default='',
                       help='Additional extraction context')
    
    # Output options
    parser.add_argument('--output', '-o', type=Path,
                       help='Output file path for results (JSON format)')
    parser.add_argument('--save-structured', action='store_true',
                       help='Save results in structured YAML format under data/benchmarks/')
    parser.add_argument('--data-dir', type=Path,
                       help='Base directory for structured data (default: llm_generator/benchmark/data)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress summary output')
    
    args = parser.parse_args()
    
    # Check if input arguments are provided
    if not (args.file or args.text or args.interactive):
        print("❌ Error: one of --file, --text, or --interactive is required")
        print("💡 Use --help for usage information")
        sys.exit(1)
    
    # Initialize processor
    processor = BenchmarkProcessor(verbose=args.verbose)
    
    try:
        # Handle input methods
        if args.interactive:
            source, version, benchmark_text = interactive_mode()
        else:
            # Validate required args for non-interactive mode
            if not args.source:
                print("❌ --source is required when not using --interactive mode")
                sys.exit(1)
            
            source = args.source
            version = args.version
            
            if args.file:
                benchmark_text = load_benchmark_text(args.file)
            else:
                benchmark_text = args.text
                
                if not benchmark_text:
                    print("❌ No benchmark text provided")
                    sys.exit(1)
        
        # Process benchmark
        results = processor.process_benchmark(
            benchmark_text=benchmark_text,
            benchmark_source=source,
            benchmark_version=version,
            extraction_context=args.context
        )
        
        # Save results if output specified
        if args.output:
            processor.save_results(results, args.output)
        
        # Save structured data if requested
        if args.save_structured:
            benchmark_dir = processor.save_structured_data(
                results, 
                source,
                args.data_dir
            )
            if not args.quiet:
                print(f"\n📁 Structured data saved to: {benchmark_dir}")
                print(f"   📋 metadata.yaml")
                print(f"   📊 coverage.yaml") 
                print(f"   📂 checks/ ({len(results['processed_checks'])} files)")
        
        # Print summary unless quiet
        if not args.quiet:
            processor.print_summary(results)
        
    except KeyboardInterrupt:
        logger.info("❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
