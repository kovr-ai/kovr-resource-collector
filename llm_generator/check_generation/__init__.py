"""
Check Generation Module - Section 3 Implementation

This module implements Section 3 of the LLM-driven compliance check generation pipeline:
- Step 1: Code Generation (convert enriched metadata to executable Python checks)
- Step 2: Automated Execution & Testing (validate against real resources)  
- Step 3: Error Repair Loop (iterative improvement of failed checks)
- Step 4: Batch Reporting & Coverage Update (comprehensive metrics)

Provides complete end-to-end implementation from benchmark metadata to validated database checks.
"""

from .services import (
    CheckGenerationService,
    check_generation_service,
    generate_executable_checks,
    execute_and_validate_checks,
    repair_failed_checks,
    generate_implementation_coverage
)

from .models import (
    ExecutableCheck,
    GenerationTask,
    ValidationResult,
    RepairContext,
    ImplementationCoverage,
    Section3Results
)

__all__ = [
    # Services
    'CheckGenerationService',
    'check_generation_service',
    'generate_executable_checks',
    'execute_and_validate_checks', 
    'repair_failed_checks',
    'generate_implementation_coverage',
    
    # Models
    'ExecutableCheck',
    'GenerationTask',
    'ValidationResult',
    'RepairContext',
    'ImplementationCoverage',
    'Section3Results'
]
