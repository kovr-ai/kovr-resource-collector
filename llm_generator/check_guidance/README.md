# Check Guidance Module - Section 2: System Compatibility Enrichment

This module implements **Section 2** of the automated check generation pipeline, focusing on making benchmark checks actionable against supported systems (GitHub, AWS, Google Cloud).

## Overview

The check guidance module transforms abstract compliance checks into system-specific, actionable guidance with validated field paths and targeted instructions.

### Input → Process → Output

```
Enriched Checks         System Resources         System-Compatible Checks
(Section 1)      →      Mapping & Validation  →  (Actionable Guidance)

Controls: AC-3           GitHub::Repo             field_paths_used:
Frameworks: NIST         AWS::EC2::Instance       - repo.branches[].protected  
Category: Access         Field Path Validation    - instance.security_groups[]
```

## Architecture

### Two-Step Workflow

1. **Step 1: Expand to Resource Types and Field Paths**
   - Map checks to compatible system resources
   - Validate field paths against real schemas
   - Generate targeted, system-specific guidance

2. **Step 2: Coverage on System Compatibility**
   - Report system compatibility success rates
   - Track field path validation coverage
   - Analyze provider distribution and quality metrics

## Module Structure

```
llm_generator/check_guidance/
├── __init__.py                 # Module exports and main functions
├── schemas.yaml               # Pydantic model definitions
├── models.py                  # Auto-generated Pydantic models
├── services.py                # Core Section 2 workflow logic
├── prompts.py                 # LLM prompts for system enrichment
├── data/                      # Structured output storage
│   ├── README.md             # Data format documentation
│   └── system_guidance/      # Generated system guidance files
│       └── <benchmark_name>/
│           ├── metadata.yaml
│           ├── coverage.yaml
│           └── checks/
└── scripts/                   # CLI tools
    ├── README.md             # Script usage documentation
    └── generate_system_guidance.py  # Main CLI script
```

## Quick Start

### Installation & Setup
```bash
# The module uses the existing project dependencies
cd /path/to/kovr-resource-collector
```

### Basic Usage
```python
from llm_generator.check_guidance import (
    enrich_checks_with_system_resources,
    generate_system_compatibility_coverage
)

# Step 1: Enrich checks with system resources
system_enriched_checks = enrich_checks_with_system_resources(enriched_checks)

# Step 2: Generate coverage report  
coverage_report = generate_system_compatibility_coverage(system_enriched_checks)

print(f"System compatibility: {coverage_report.coverage_percentages['resource_types']:.1f}%")
```

### CLI Usage
```bash
# Process benchmark output through Section 2
python llm_generator/check_guidance/scripts/generate_system_guidance.py \
    --benchmark-dir llm_generator/benchmark/data/benchmarks/owasp_top_10_2021 \
    --verbose

# Process from JSON file
python llm_generator/check_guidance/scripts/generate_system_guidance.py \
    --checks-file enriched_checks.json \
    --output-file system_guidance_results.json
```

## Key Features

### 🎯 **System Resource Mapping**
- Maps abstract compliance checks to specific system resources
- Supports GitHub repositories, AWS EC2 instances, Google Compute instances
- Extensible architecture for adding new providers and resource types

### 🛡️ **Field Path Validation** 
- Validates all field paths against actual resource schemas
- Prevents LLM hallucination of non-existent paths
- Ensures system compatibility and actionability

### 📊 **Comprehensive Coverage Metrics**
- Resource type assignment success rates
- Field path validation coverage
- Targeted guidance generation quality
- Provider-specific distribution analysis

### 🔧 **Multi-Provider Support**
- **GitHub**: Repository settings, branch protection, security configurations
- **AWS**: EC2 instances, security groups, VPC settings, IAM policies
- **Google Cloud**: Compute instances, network interfaces, service accounts

## Data Models

### SystemEnrichedCheck
Extends base Check with system compatibility fields:
```yaml
resource_type: "GitHub::Repo"
field_paths_used:
  - "repo.basic_info.branches[].protected"
  - "repo.security.branch_protection.enforce_admins"
targeted_guidance: "Verify that all main branches have protection enabled..."
system_enriched_at: "2024-01-15T10:30:00"
```

### ResourceSchema
Defines available system resources and their field paths:
```yaml
resource_type: "GitHub::Repo"
display_name: "GitHub Repository"
provider: "github"
field_paths:
  - "repo.basic_info.name"
  - "repo.basic_info.branches[].protected"
  - "repo.security.branch_protection.enforce_admins"
```

### SystemCompatibilityCoverage
Comprehensive coverage and quality metrics:
```yaml
coverage_percentages:
  resource_types: 88.0    # % with compatible resources
  field_paths: 80.0       # % with valid field paths
  targeted_guidance: 72.0 # % with actionable guidance

provider_coverage:
  github_checks: 12
  aws_checks: 8
  google_checks: 2
```

## LLM Integration

### System Enrichment Prompt
The module uses sophisticated LLM prompts that:
- Provide complete resource schemas with field paths
- Prevent hallucination through explicit path validation
- Generate targeted, implementation-specific guidance
- Reference exact field paths in actionable instructions

### Example LLM Output
```json
{
  "resource_type": "GitHub::Repo",
  "field_paths_used": [
    "repo.basic_info.branches[].protected"
  ],
  "targeted_guidance": "Check that repo.basic_info.branches[].protected is true for all branches named 'main' or 'master'. This ensures critical branches cannot be directly pushed to without review."
}
```

## Integration with Pipeline

### Section 1 → Section 2 Flow
```python
# Section 1: Generate enriched benchmark metadata
from llm_generator.benchmark import generate_metadata, generate_checks_metadata

benchmark = generate_metadata("OWASP Top 10 2021")
enriched_checks = generate_checks_metadata(benchmark)

# Section 2: Add system compatibility  
from llm_generator.check_guidance import enrich_checks_with_system_resources

system_checks = enrich_checks_with_system_resources(enriched_checks)
```

### Future Section 3 Integration
The system-enriched checks provide the foundation for Section 3 (executable Python logic generation):
- `resource_type` → Import appropriate provider modules
- `field_paths_used` → Generate specific data access code
- `targeted_guidance` → Create validation logic and error messages

## Configuration & Extensibility

### Adding New Providers
```python
# Extend ResourceSchema with new provider
new_resource = ResourceSchema(
    resource_type="Azure::VM",
    display_name="Azure Virtual Machine",
    provider="azure",
    field_paths=[
        "vm.properties.hardwareProfile.vmSize",
        "vm.properties.networkProfile.networkInterfaces[]"
    ],
    description="Azure virtual machine instance"
)
```

### Custom Field Path Extraction
The module supports pluggable field path extraction from:
- Pydantic model introspection
- OpenAPI/JSON Schema definitions  
- Custom resource configuration files
- Runtime schema discovery

## Performance & Scalability

### Efficient Processing
- **Batch Processing**: Process multiple checks efficiently
- **Caching**: Resource schemas cached for reuse
- **Validation**: Early field path validation prevents costly re-processing
- **Parallel Processing**: Support for concurrent check enrichment

### Quality Assurance
- **Field Path Validation**: 100% validation against real schemas
- **Coverage Metrics**: Detailed success/failure tracking
- **Error Recovery**: Graceful handling of enrichment failures
- **Logging**: Comprehensive processing logs for debugging

## Testing & Development

### Running Tests
```bash
# Run check guidance module tests
python -m pytest tests/check_guidance/

# Test field path validation
python -m pytest tests/check_guidance/test_field_path_validation.py

# Test system enrichment prompts  
python -m pytest tests/check_guidance/test_prompts.py
```

### Development Workflow
1. **Add Resource Type**: Define new ResourceSchema with field paths
2. **Update Prompts**: Enhance LLM prompts for new resource types
3. **Test Validation**: Verify field path validation works correctly
4. **Integration Test**: End-to-end test with real benchmark data

## Contributing

### Guidelines
- Follow existing patterns from benchmark module
- Validate all field paths against real schemas
- Include comprehensive error handling and logging
- Update documentation for new features
- Add tests for new resource types and providers

### Code Style
- Use type hints throughout
- Follow Pydantic model patterns
- Implement comprehensive logging
- Include docstrings for all public methods
