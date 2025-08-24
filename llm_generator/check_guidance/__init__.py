"""
Check Guidance Module - Resource Selection (Step 1)

This module provides functionality to determine which resource types are valid
for compliance checks, making them actionable against supported systems.

Main Functions:
    select_valid_resources_for_check: Step 1 - Identify compatible resource types

Usage:
    from llm_generator.check_guidance import select_valid_resources_for_check
    
    # Determine valid resource types for a check
    enriched_check = select_valid_resources_for_check(check)
    # Returns: SystemEnrichedCheck object with valid_resources and invalid_resources
"""

from .services import (
    select_valid_resources_for_check,
    resource_selection_service
)

from .models import (
    ResourceSchema, 
)

__all__ = [
    # Main workflow functions
    'select_valid_resources_for_check',
    
    # Service instance
    'resource_selection_service',
    
    # Model classes
    'ResourceSchema',
]
