# System Guidance Data Storage

This directory stores system-compatible guidance data processed through Section 2 workflow, making benchmark checks actionable against supported systems (GitHub, AWS, Google).

## Directory Structure

```
data/system_guidance/<benchmark_name>/
├── metadata.yaml       # Processing info and summary statistics
├── coverage.yaml       # System compatibility coverage report
└── checks/             # Individual system-enriched check files
    ├── <check_id_1>_system.yaml
    ├── <check_id_2>_system.yaml
    └── <check_id_n>_system.yaml
```

## File Descriptions

### `metadata.yaml`
Contains system guidance processing information:
- **processing_info**: Processing date, input/output counts
- **summary**: High-level system compatibility results
- **section**: Identifies this as Section 2 output
- **processing_completed_at**: Final completion timestamp

### `coverage.yaml`
Contains system compatibility coverage and quality metrics:
- **total_checks**: Number of checks processed
- **checks_with_resource_types**: Number with compatible system resources
- **checks_with_field_paths**: Number with valid field path mappings
- **checks_with_targeted_guidance**: Number with actionable guidance
- **coverage_percentages**: Resource types, field paths, and guidance coverage %
- **provider_coverage**: Breakdown by GitHub, AWS, Google providers
- **quality_metrics**: Average field paths per check, guidance quality metrics

### `checks/<check_id>_system.yaml`
Individual system-enriched check files containing:
- **Base Check Fields**: All original fields from Section 1 (unique_id, name, literature, controls, etc.)
- **System Compatibility Fields**:
  - **resource_type**: Compatible system resource (e.g., "GitHub::Repo", "AWS::EC2::Instance")
  - **field_paths_used**: Actual field paths for verification (e.g., ["repo.basic_info.branches[].protected"])
  - **targeted_guidance**: System-specific actionable instructions
  - **system_enriched_at**: Timestamp of system enrichment

## Example System-Enriched Check

```yaml
unique_id: "OWASP-2021-A01-001"
name: "Branch protection enabled"
literature: "Repositories must enforce branch protection on main branches."
controls:
  - "NIST-800-53-AC-3"
frameworks:
  - "NIST-800-53"
benchmark_mapping:
  - "GH-BENCHMARK-0005"
category: "Access Control"
severity: "high"
tags: ["github", "repository", "branch-protection"]

# Section 2: System compatibility fields
resource_type: "GitHub::Repo"
field_paths_used:
  - "repo.basic_info.branches[].protected"
  - "repo.security.branch_protection.enforce_admins"
targeted_guidance: >
  Verify that all branches named 'main' or 'master' in GitHub repositories
  have the 'protected' flag set to true. Check that 
  repo.security.branch_protection.enforce_admins is enabled to ensure
  administrators cannot bypass branch protection rules.
system_enriched_at: "2024-01-15T10:30:00"
```

## Usage Patterns

### Loading System-Enriched Checks
```python
import yaml
from pathlib import Path

# Load all system-enriched checks for a benchmark
benchmark_dir = Path("data/system_guidance/owasp_top_10_2021")
checks_dir = benchmark_dir / "checks"

system_checks = []
for check_file in checks_dir.glob("*_system.yaml"):
    with open(check_file) as f:
        check_data = yaml.safe_load(f)
        system_checks.append(check_data)
```

### Processing Coverage Report
```python
import yaml

# Load coverage metrics
coverage_file = Path("data/system_guidance/owasp_top_10_2021/coverage.yaml")
with open(coverage_file) as f:
    coverage = yaml.safe_load(f)
    
print(f"Resource Types Coverage: {coverage['coverage_percentages']['resource_types']:.1f}%")
print(f"Field Paths Coverage: {coverage['coverage_percentages']['field_paths']:.1f}%")
```

## Integration with Section 1

System guidance data builds upon benchmark processing output:

1. **Input**: Enriched checks from `llm_generator/benchmark/data/benchmarks/<name>/checks/`
2. **Process**: System compatibility enrichment via Section 2 workflow
3. **Output**: System-actionable checks in `llm_generator/check_guidance/data/system_guidance/<name>/checks/`

## Quality Assurance

### Field Path Validation
- All field paths are validated against actual resource schemas
- Invalid or hallucinated paths are filtered out
- Warning logs identify any path validation issues

### Coverage Metrics
- **Resource Types**: % of checks mapped to compatible system resources
- **Field Paths**: % of checks with valid field path assignments
- **Targeted Guidance**: % of checks with comprehensive actionable guidance

### Provider Support
- **GitHub**: Repository, branch protection, security settings
- **AWS**: EC2 instances, security groups, VPC configurations  
- **Google**: Compute instances, network interfaces, service accounts
