"""
Benchmark Generator Package - Section 1 Implementation

This package implements the complete benchmark metadata generation process:
- Step 1: Extract Checks Literature
- Step 2: Map to Controls and Existing Benchmarks
- Step 3: Coverage Reporting

Only services and models (dynamically generated) are exported from here.
"""

# Import core services
from .services import (
    BenchmarkService,
    benchmark_service,
    generate_metadata,
    generate_checks_metadata, 
    generate_coverage_report,
    update_benchmark_coverage_metrics
)
from .models import MODEL_NAMES, Benchmark, Check, CoverageMetrics

# Package exports
__all__ = [
    # Services
    'BenchmarkService',
    'benchmark_service',
    # Models
    'Benchmark',
    'Check',
    'CoverageMetrics',
    # Service Methods (Section 1 Steps)
    'generate_metadata',                    # Step 1: Extract Checks Literature
    'generate_checks_metadata',             # Step 2: Map to Controls
    'generate_coverage_report',             # Step 3: Coverage Reporting
    'update_benchmark_coverage_metrics',    # Step 4: Update Benchmark with Coverage
] + MODEL_NAMES
