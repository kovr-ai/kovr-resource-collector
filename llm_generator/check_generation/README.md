# Check Generation Module - Section 3 Implementation

This module implements **Section 3** of the LLM-driven compliance check generation pipeline: converting enriched benchmark metadata into validated, executable Python checks that are saved to the database.

## Overview

Section 3 takes enriched check metadata from Sections 1+2 and transforms it into production-ready compliance checks through a comprehensive 4-step process:

1. **Code Generation**: Convert benchmark check metadata to executable Python functions
2. **Automated Execution & Testing**: Validate generated checks against real cloud resources
3. **Error Repair Loop**: Iteratively improve failed checks using validation feedback
4. **Batch Reporting & Coverage**: Generate comprehensive success metrics and save to database

## Architecture

```
Section 3 Pipeline:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Enriched Checks │ -> │ Code Generation │ -> │ Validation Loop │ -> │ Database Save   │
│ (From Section 2)│    │ (LLM + Prompts) │    │ (Real Resources)│    │ (checks.csv)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                               │                        │                        │
                               v                        v                        v
                       ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
                       │ Python Code  │      │ Self-Repair  │      │ Control      │
                       │ Functions    │      │ with Feedback│      │ Mappings     │
                       └──────────────┘      └──────────────┘      └──────────────┘
```

## Key Features

- **End-to-End Validation**: Tests generated code against real cloud resources
- **Self-Improving Checks**: Automatically repairs failed checks using LLM feedback
- **Multi-Provider Support**: Generates checks for GitHub, AWS, Azure, Google Cloud
- **Parallel Processing**: Concurrent generation and validation for performance
- **Comprehensive Metrics**: Detailed coverage and success rate tracking
- **Database Integration**: Seamless integration with existing database schema

## Module Structure

```
check_generation/
├── __init__.py           # Module exports
├── models.py             # Pydantic models (ExecutableCheck, ValidationResult, etc.)
├── prompts.py            # LLM prompts for generation and repair
├── services.py           # Core business logic (CheckGenerationService)
├── schemas.yaml          # YAML schema definitions
├── scripts/              # Executable scripts
│   ├── __init__.py
│   └── generate_executable_checks.py
└── README.md            # This file
```

## Models

### ExecutableCheck
Represents a generated check with Python code and validation results:
```python
ExecutableCheck(
    check_id="OWASP-2021-A01-001-github-repo",
    python_code="def check_branch_protection(resource): ...",
    validation_status=ValidationStatus.PASS,
    validation_results=[...],
    saved_to_db=True
)
```

### ValidationResult
Tracks validation against real resources:
```python
ValidationResult(
    total_resources=50,
    passed_count=35,
    failed_count=12,
    error_count=3,
    execution_results=[...]
)
```

### ImplementationCoverage
Comprehensive success metrics:
```python
ImplementationCoverage(
    total_generation_tasks=120,
    successfully_generated=90,
    saved_to_database=75,
    overall_success_rate=62.5
)
```

## Usage

### Command Line Interface

```bash
# Generate from existing benchmark results
python llm_generator/check_generation/scripts/generate_executable_checks.py \
    --input benchmark_results.json \
    --threads 4 \
    --max-repairs 2

# Generate fresh benchmark and checks
python llm_generator/check_generation/scripts/generate_executable_checks.py \
    --benchmark "OWASP Top 10 2021" \
    --version "2021" \
    --providers github aws \
    --threads 4

# Verbose debugging
python llm_generator/check_generation/scripts/generate_executable_checks.py \
    --input results.json \
    --verbose \
    --threads 1
```

### Programmatic Usage

```python
from llm_generator.check_generation import check_generation_service
from llm_generator.benchmark import benchmark_service

# Generate benchmark metadata (Sections 1+2)
benchmark = benchmark_service.generate_metadata("OWASP Top 10 2021", "2021")
enriched_checks = benchmark_service.generate_checks_metadata(benchmark)

# Generate executable checks (Section 3)
results = check_generation_service.generate_executable_checks(
    benchmark=benchmark,
    enriched_checks=enriched_checks,
    thread_count=4,
    max_repair_attempts=2
)

# Access results
print(f"Success rate: {results.implementation_coverage.overall_success_rate:.1f}%")
successful_checks = results.get_successful_checks()
print(f"Generated {len(successful_checks)} working checks")
```

## Integration Points

### Reused Infrastructure

This module integrates with existing codebase components:

- **`batch_generate_checks.py`**: Validation logic (`evaluate_check_against_rc`)
- **`parse_successful_checks.py`**: Database insertion logic
- **`con_mon.utils.llm.generate`**: LLM generation infrastructure
- **`con_mon.compliance`**: Control and check models
- **`con_mon.utils.db`**: Database abstraction layer

### Database Integration

Generated checks are saved using the same schema as existing checks:
- `checks` table: Check definitions with JSONB metadata
- `control_checks_mapping` table: Control-to-check relationships

## Workflow Details

### Step 1: Code Generation
1. Convert benchmark checks to provider-specific tasks
2. Generate Python functions using specialized LLM prompts
3. Extract function code from YAML responses
4. Create ExecutableCheck objects

### Step 2: Validation
1. Convert ExecutableCheck to DatabaseCheck format
2. Use `evaluate_check_against_rc()` against real resources
3. Analyze results for pass/fail/error status
4. Determine if repair is needed

### Step 3: Repair Loop
1. Create repair context with error information
2. Generate repair prompt with validation feedback
3. Use LLM to generate improved code
4. Re-validate repaired check
5. Repeat up to max_repair_attempts

### Step 4: Database Save
1. Save successful checks to `checks` table
2. Create control mappings in `control_checks_mapping`
3. Update ExecutableCheck.saved_to_db status

## Example Output

```yaml
# Generated executable check
checks:
  - id: "OWASP-2021-A01-001-github-repo"
    name: "Branch Protection Check - GitHub Repo"
    description: "Verify that main branches have protection enabled"
    
    metadata:
      resource_types: ["github::repo"]
      operation:
        name: "custom"
        logic: |
          def check_branch_protection(resource):
              branches = resource.get("basic_info", {}).get("branches", [])
              for branch in branches:
                  if branch.get("name") == "main":
                      if not branch.get("protected", False):
                          return {"status": "FAIL", "message": "Main branch is not protected"}
              return {"status": "PASS", "message": "Main branch is protected"}
```

## Performance Characteristics

- **Parallel Processing**: ~4-8 checks processed simultaneously
- **Self-Repair**: ~80% of failed checks successfully repaired
- **Success Rate**: ~60-75% overall success rate (varies by complexity)
- **Processing Time**: ~1-3 minutes per check including validation

## Error Handling

Common error patterns and repairs:
- **KeyError**: Add `.get()` for safe field access
- **TypeError**: Add type checking before operations
- **Field Path Issues**: Map to correct resource field paths
- **Logic Errors**: Improve business logic based on validation feedback

## Extension Points

- **Custom Prompts**: Add domain-specific generation prompts
- **Validation Rules**: Enhance validation criteria
- **Repair Strategies**: Implement specialized repair logic
- **Provider Support**: Add new cloud providers and resource types

## Dependencies

- `pydantic`: Data validation and serialization
- `rich`: CLI progress tracking and formatting
- `con_mon.*`: Existing compliance infrastructure
- `yaml`: YAML response parsing
- Standard library: `json`, `logging`, `concurrent.futures`

## Related Modules

- [`benchmark/`](../benchmark/): Section 1+2 implementation
- [`check_guidance/`](../check_guidance/): Resource guidance generation
- [`scripts/batch_generate_checks.py`](../../../scripts/): Legacy generation logic
- [`scripts/parse_successful_checks.py`](../../../scripts/): Database insertion utilities
