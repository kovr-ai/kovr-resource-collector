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
    generate_metadata,
    generate_checks_metadata,
    generate_coverage_report,
)

__all__ = [
    # Submodules
    'benchmark',
    
    # Core services
    'generate_metadata',
    'generate_checks_metadata', 
    'generate_coverage_report',
]

__version__ = "1.0.0"
__author__ = "KOVR Compliance Team"
