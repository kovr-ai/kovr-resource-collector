"""
Check Guidance Module - Section 2: System Compatibility Enrichment

This module provides functionality to enrich benchmark checks with system-compatible
resource types and field paths, making them actionable against supported systems.

Main Functions:
    enrich_checks_with_system_resources: Step 1 - Expand to Resource Types and Field Paths
    generate_system_compatibility_coverage: Step 2 - Coverage on System Compatibility

Usage:
    from llm_generator.check_guidance import (
        enrich_checks_with_system_resources,
        generate_system_compatibility_coverage
    )
    
    # Step 1: Enrich checks with system resources
    system_enriched_checks = enrich_checks_with_system_resources(enriched_checks)
    
    # Step 2: Generate coverage report
    coverage_report = generate_system_compatibility_coverage(system_enriched_checks)
"""

from .services import (
    enrich_checks_with_system_resources,
    generate_system_compatibility_coverage,
    check_guidance_service
)

from .models import (
    SystemEnrichedCheck,
    ResourceSchema, 
    SystemCompatibilityCoverage
)

__all__ = [
    # Main workflow functions
    'enrich_checks_with_system_resources',
    'generate_system_compatibility_coverage',
    
    # Service instance
    'check_guidance_service',
    
    # Model classes
    'SystemEnrichedCheck',
    'ResourceSchema',
    'SystemCompatibilityCoverage'
]
