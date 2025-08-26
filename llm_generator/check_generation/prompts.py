"""
Check Generation Prompts - Section 3 LLM Prompts

This module provides specialized prompts for Section 3 implementation:
- Code generation prompts (convert metadata to Python functions)
- Error repair prompts (improve failed checks using validation feedback)  
- Field path validation prompts (verify resource structure compatibility)

Adapted from existing generation logic in con_mon.utils.llm.generate
"""

from typing import List, Dict, Any, Optional
import json

from ..benchmark.models import Check
from .models import ValidationResult, RepairContext

# Re-export the working prompt classes for convenience
from con_mon.utils.llm.prompt import CheckPrompt, CheckPromptWithResults
from con_mon.connectors.models import ConnectorType

# Make them available at module level
__all__ = ['CheckPrompt', 'CheckPromptWithResults', 'ConnectorType',
          'get_code_generation_prompt', 'get_repair_prompt', 'get_field_path_validation_prompt']


def get_code_generation_prompt(
    benchmark_check: Check,
    provider: str,
    resource_type: str,
    field_paths: List[str],
    resource_schema: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate prompt for converting benchmark check metadata to executable Python code.
    
    Args:
        benchmark_check: Source benchmark check with enriched metadata
        provider: Target provider (github, aws, azure, google)
        resource_type: Target resource type (repo, ec2_instance, etc.)
        field_paths: Available field paths for the resource
        resource_schema: Optional schema showing resource structure
        
    Returns:
        Formatted prompt for LLM code generation
    """
    
    # Format field paths for prompt
    field_paths_str = "\n".join([f"  - {path}" for path in field_paths[:20]])  # Limit to avoid token overflow
    if len(field_paths) > 20:
        field_paths_str += f"\n  ... and {len(field_paths) - 20} more fields"
    
    # Format resource schema if available
    schema_str = ""
    if resource_schema:
        schema_str = f"""
Resource Schema Example:
```json
{json.dumps(resource_schema, indent=2)[:1000]}{'...' if len(json.dumps(resource_schema, indent=2)) > 1000 else ''}
```
"""
    
    # Extract control information if available
    controls_str = ""
    if benchmark_check.controls:
        controls_str = f"\nMapped Controls: {', '.join(benchmark_check.controls)}"
    
    frameworks_str = ""
    if benchmark_check.frameworks:
        frameworks_str = f"\nFrameworks: {', '.join(benchmark_check.frameworks)}"
    
    prompt = f"""
You are an expert security engineer generating executable compliance checks for cloud infrastructure.

TASK: Convert the following benchmark check into executable Python code that validates {provider} {resource_type} resources.

BENCHMARK CHECK DETAILS:
Name: {benchmark_check.name}
Description: {benchmark_check.literature or benchmark_check.name}
Category: {benchmark_check.category}
Severity: {benchmark_check.severity}{controls_str}{frameworks_str}

TARGET PLATFORM:
Provider: {provider}
Resource Type: {resource_type}

AVAILABLE FIELD PATHS:
{field_paths_str}

{schema_str}

REQUIREMENTS:
1. Generate a Python function that takes a single resource object as input
2. Use only the field paths listed above - these are verified to exist in the resource
3. Return a dictionary with: {{"status": "PASS"|"FAIL", "message": "detailed message"}}
4. Handle missing fields gracefully using .get() or safe navigation
5. Include descriptive error messages that help users understand compliance issues
6. Use meaningful variable names and add comments explaining the logic
7. Follow the security principle being checked - don't just check existence, check actual compliance

EXAMPLE OUTPUT FORMAT:
```yaml
checks:
  - id: "{benchmark_check.unique_id}-{provider}-{resource_type}"
    name: "{benchmark_check.name} - {provider.title()} {resource_type.title()}"
    description: "{benchmark_check.literature[:100]}..."
    
    output_statements:
      pass: "Resource complies with {benchmark_check.name}"
      fail: "Resource violates {benchmark_check.name}: {{violation_details}}"
    
    fix_details:
      description: "How to fix this compliance issue"
      steps:
        - "Step 1: Specific remediation action"
        - "Step 2: Verification step"
    
    metadata:
      resource_types:
        - "{provider}::{resource_type}"
      
      tags: ["{benchmark_check.category}", "automated", "{provider}"]
      
      operation:
        name: "custom"
        logic: |
          def check_{resource_type}_compliance(resource):
              \"\"\"
              Check {benchmark_check.name} compliance for {provider} {resource_type}.
              
              Args:
                  resource: {provider} {resource_type} resource object
                  
              Returns:
                  dict: {{"status": "PASS"|"FAIL", "message": str}}
              \"\"\"
              
              # YOUR IMPLEMENTATION HERE
              # Use the field paths and implement the security check
              # Remember to handle missing fields gracefully
              
              return {{"status": "PASS", "message": "Compliance check passed"}}
      
      field_path: "relevant.field.path.from.above.list"
```

CRITICAL NOTES:
- Only use field paths from the provided list
- Focus on the actual security requirement, not just field existence
- Make the logic robust and production-ready
- Consider edge cases and error handling
- The function will be executed against real {provider} resources

Generate the complete check definition now:
"""
    
    return prompt


def get_repair_prompt(
    benchmark_check: Check,
    provider: str,
    resource_type: str,
    field_paths: List[str],
    repair_context: RepairContext,
    current_python_code: str
) -> str:
    """
    Generate prompt for repairing failed check code using validation feedback.
    
    Args:
        benchmark_check: Original benchmark check metadata
        provider: Target provider 
        resource_type: Target resource type
        field_paths: Available field paths
        repair_context: Context with error information and previous attempts
        current_python_code: Current failing Python code
        
    Returns:
        Formatted repair prompt for LLM
    """
    
    # Analyze validation results to extract error patterns
    error_summary = _analyze_validation_errors(repair_context.validation_results)
    
    # Format field paths
    field_paths_str = "\n".join([f"  - {path}" for path in field_paths[:25]])
    
    prompt = f"""
You are an expert security engineer fixing a failing compliance check.

ORIGINAL CHECK DETAILS:
Name: {benchmark_check.name}
Description: {benchmark_check.literature or benchmark_check.name}
Provider: {provider}
Resource Type: {resource_type}

CURRENT FAILING CODE:
```python
{current_python_code}
```

VALIDATION ERRORS (Attempt {repair_context.attempt_number}/{repair_context.max_attempts}):
{error_summary}

IDENTIFIED ISSUES:
Error Patterns: {', '.join(repair_context.error_patterns) if repair_context.error_patterns else 'None'}
Field Path Issues: {', '.join(repair_context.field_path_issues) if repair_context.field_path_issues else 'None'}

AVAILABLE FIELD PATHS (Verified to exist):
{field_paths_str}

REPAIR REQUIREMENTS:
1. Analyze the validation errors and fix the root causes
2. Only use field paths from the verified list above
3. Add proper error handling for missing or null fields
4. Use safe navigation (.get()) for optional fields
5. Ensure the function returns the exact format: {{"status": "PASS"|"FAIL", "message": str}}
6. Test your logic mentally against the error scenarios
7. Make the check more robust and handle edge cases

COMMON FIXES:
- KeyError: Use .get() instead of direct dictionary access
- TypeError: Check if field exists and is correct type before operations
- AttributeError: Verify object structure before calling methods
- Logic errors: Review the business logic against the security requirement

Generate the COMPLETE CORRECTED check definition in YAML format:

```yaml
checks:
  - id: "{benchmark_check.unique_id}-{provider}-{resource_type}"
    name: "{benchmark_check.name} - {provider.title()} {resource_type.title()}"
    description: "{benchmark_check.literature[:100] if benchmark_check.literature else benchmark_check.name}..."
    
    output_statements:
      pass: "Resource complies with {benchmark_check.name}"
      fail: "Resource violates {benchmark_check.name}: {{violation_details}}"
    
    fix_details:
      description: "How to fix this compliance issue"
      steps:
        - "Corrective action based on the check requirement"
    
    metadata:
      resource_types:
        - "{provider}::{resource_type}"
      
      tags: ["{benchmark_check.category}", "automated", "{provider}", "repaired"]
      
      operation:
        name: "custom"
        logic: |
          def check_{resource_type}_compliance(resource):
              \"\"\"
              REPAIRED: {benchmark_check.name} compliance for {provider} {resource_type}.
              Attempt {repair_context.attempt_number}: Fixed validation errors.
              \"\"\"
              
              # CORRECTED IMPLEMENTATION - Address the errors above
              
              return {{"status": "PASS", "message": "Compliance check passed"}}
      
      field_path: "most.relevant.field.path"
```

Focus on fixing the specific errors while maintaining the security check integrity.
"""
    
    return prompt


def get_field_path_validation_prompt(
    provider: str,
    resource_type: str,
    proposed_field_paths: List[str],
    available_field_paths: List[str]
) -> str:
    """
    Generate prompt to validate if proposed field paths exist in resource schema.
    
    Args:
        provider: Target provider
        resource_type: Target resource type  
        proposed_field_paths: Field paths used in check logic
        available_field_paths: Known available field paths
        
    Returns:
        Validation prompt for field path compatibility
    """
    
    proposed_str = "\n".join([f"  - {path}" for path in proposed_field_paths])
    available_str = "\n".join([f"  - {path}" for path in available_field_paths[:50]])
    
    prompt = f"""
Validate field path compatibility for {provider} {resource_type} resources.

PROPOSED FIELD PATHS (from check logic):
{proposed_str}

AVAILABLE FIELD PATHS (verified to exist):
{available_str}

TASK: For each proposed field path, determine if it exists in the available paths or can be safely derived.

RESPONSE FORMAT:
```json
{{
  "validation_results": [
    {{
      "proposed_path": "path.from.check",
      "status": "valid|invalid|partial", 
      "available_match": "exact.matching.path or null",
      "suggestion": "alternative.path or fix recommendation",
      "confidence": 0.95
    }}
  ],
  "overall_compatibility": 0.85,
  "recommendations": [
    "Use field.path.x instead of proposed.field.y",
    "Add null checking for optional field.z"
  ]
}}
```

Analyze compatibility now:
"""
    
    return prompt


def _analyze_validation_errors(validation_results: List[ValidationResult]) -> str:
    """
    Analyze validation results to extract error patterns for repair prompts.
    
    Args:
        validation_results: List of validation attempts with errors
        
    Returns:
        Formatted error summary string
    """
    if not validation_results:
        return "No validation results available"
    
    # Get latest validation result
    latest_result = validation_results[-1]
    
    error_details = []
    error_details.append(f"Total Resources: {latest_result.total_resources}")
    error_details.append(f"Passed: {latest_result.passed_count}")
    error_details.append(f"Failed: {latest_result.failed_count}")  
    error_details.append(f"Errors: {latest_result.error_count}")
    
    if latest_result.execution_results:
        # Extract sample errors
        error_messages = []
        for result in latest_result.execution_results[:5]:  # Sample first 5
            if result.error:
                error_messages.append(f"  - Resource {result.resource_id}: {result.error}")
            elif result.status == "FAIL":
                error_messages.append(f"  - Resource {result.resource_id}: {result.message}")
        
        if error_messages:
            error_details.append("\nSample Errors:")
            error_details.extend(error_messages)
    
    # Add historical context if multiple attempts
    if len(validation_results) > 1:
        error_details.append(f"\nPrevious attempts: {len(validation_results) - 1}")
        for i, result in enumerate(validation_results[:-1]):
            error_details.append(f"  Attempt {i+1}: {result.error_count} errors, {result.passed_count} passed")
    
    return "\n".join(error_details)


def get_success_criteria_prompt() -> str:
    """
    Get prompt defining success criteria for check validation.
    
    Returns:
        Success criteria definition
    """
    return """
VALIDATION SUCCESS CRITERIA:

A check is considered VALID if:
1. Python code executes without exceptions on >80% of resources
2. Returns proper format: {"status": "PASS"|"FAIL", "message": str}
3. Produces at least some meaningful results (not all errors)
4. Logic correctly implements the security requirement
5. Handles edge cases gracefully

A check is considered INVALID if:
1. Causes Python exceptions on most resources (KeyError, TypeError, etc.)
2. Returns invalid response format
3. Uses non-existent field paths
4. Logic is incorrect or too simplistic
5. Fails on all resources due to implementation errors

REPAIR ATTEMPTS:
- Maximum 2-3 repair attempts per check
- Each repair should address specific validation errors
- Focus on robustness and proper error handling
- Preserve the original security requirement intent
"""
