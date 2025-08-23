"""
LLM Generator Package - Benchmark Metadata Generation

This package provides LLM-powered generation capabilities for compliance benchmarks.

Currently implements:
- benchmark: Section 1 benchmark metadata generation workflow
"""

# Import benchmark functionality
from . import benchmark

# Re-export key benchmark functionality
from .benchmark import (
    benchmark_service,
    generate_metadata,
    generate_checks_metadata,
    generate_coverage_report,
    PromptFactory,
    GenericBenchmarkPrompt
)

__all__ = [
    # Submodules
    'benchmark',
    
    # Core services  
    'benchmark_service',
    'generate_metadata',
    'generate_checks_metadata', 
    'generate_coverage_report',
    'PromptFactory',
    'GenericBenchmarkPrompt'
]

__version__ = "1.0.0"
__author__ = "KOVR Compliance Team"
