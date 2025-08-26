# Check Guidance Scripts

This directory contains scripts for processing enriched benchmark checks through Section 2 workflow to generate system-compatible guidance.

## Main Script: `generate_system_guidance.py`

A comprehensive CLI tool that executes the complete system compatibility enrichment workflow:

1. **Expand to Resource Types and Field Paths** - Maps checks to system resources with validated field paths
2. **Coverage on System Compatibility** - Provides detailed metrics on system compatibility success

### Usage Examples

#### Process from Benchmark Output
```bash
# Process checks from benchmark processing output
python generate_system_guidance.py --benchmark-dir data/benchmarks/owasp_top_10_2021

# With verbose logging
python generate_system_guidance.py --benchmark-dir /path/to/benchmark --verbose

# Custom output directory
python generate_system_guidance.py --benchmark-dir /path/to/benchmark --output-dir /custom/path
```

#### Process from JSON File
```bash
# Process from exported JSON file
python generate_system_guidance.py --checks-file processed_checks.json

# Save results to specific file
python generate_system_guidance.py --checks-file checks.json --output-file system_results.json
```

#### Quiet Mode
```bash
# Suppress summary output (useful for automation)
python generate_system_guidance.py --benchmark-dir /path/to/benchmark --quiet
```

#### Getting Help
```bash
# Show all available options
python generate_system_guidance.py --help
```

### Input Requirements

The script accepts enriched checks from Section 1 in two formats:

#### 1. Benchmark Directory Structure
```
benchmark_dir/
├── metadata.yaml
├── coverage.yaml
└── checks/
    ├── check_1.yaml
    ├── check_2.yaml
    └── ...
```

#### 2. JSON File Format
```json
{
  "processed_checks": [
    {
      "unique_id": "OWASP-2021-A01-001",
      "name": "Branch protection enabled",
      "controls": ["NIST-800-53-AC-3"],
      "frameworks": ["NIST-800-53"],
      "category": "Access Control",
      ...
    }
  ]
}
```

### Output Structure

The script generates structured YAML output:

```
data/system_guidance/<benchmark_name>/
├── metadata.yaml       # Processing metadata and summary
├── coverage.yaml       # System compatibility coverage metrics
└── checks/             # System-enriched individual check files
    ├── <check_id_1>_system.yaml
    ├── <check_id_2>_system.yaml
    └── ...
```

### Script Features

#### 🎯 **Complete Section 2 Implementation**
- **Step 1**: System resource type mapping with field path validation
- **Step 2**: Comprehensive system compatibility coverage reporting

#### 🔧 **Flexible Input Options**
- Load from benchmark processing output directories
- Load from JSON files with enriched check data
- Support for multiple input formats and structures

#### 📊 **Comprehensive Coverage Reporting**
- Resource type assignment percentages
- Field path validation coverage
- Targeted guidance generation success rates
- Provider-specific breakdowns (GitHub, AWS, Google)
- Quality metrics (avg field paths per check, guidance length)

#### 🛡️ **Field Path Validation**
- Validates all field paths against actual resource schemas
- Prevents hallucination of non-existent field paths
- Provides warnings for invalid path assignments
- Ensures system compatibility accuracy

#### 🏢 **Multi-Provider Support**
- **GitHub**: Repository management, branch protection, security settings
- **AWS**: EC2 instances, security groups, VPC configurations
- **Google Cloud**: Compute instances, network interfaces, service accounts

### Example Output

#### Processing Summary
```
================================================================================
🔗 SYSTEM COMPATIBILITY PROCESSING SUMMARY
================================================================================
📅 Processed: 2024-01-15 10:30:00
📊 Input Checks: 25
📊 Output Checks: 25

📈 RESULTS:
  • Total Checks Processed: 25
  • System Compatible: 22
  • With Field Paths: 20
  • With Guidance: 18
  • Avg Field Paths/Check: 2.3

📊 SYSTEM COMPATIBILITY COVERAGE:
  • Resource Types: 88.0%
  • Field Paths: 80.0%
  • Targeted Guidance: 72.0%

🏢 PROVIDER BREAKDOWN:
  • GitHub: 12 checks
  • AWS: 8 checks
  • Google: 2 checks
  • Multi-Provider: 5 checks
```

#### System-Enriched Check Example
```yaml
unique_id: "OWASP-2021-A01-001"
name: "Branch protection enabled"
resource_type: "GitHub::Repo"
field_paths_used:
  - "repo.basic_info.branches[].protected"
  - "repo.security.branch_protection.enforce_admins"
targeted_guidance: >
  Verify that all branches named 'main' or 'master' in GitHub repositories
  have the 'protected' flag set to true. Additionally, ensure that
  repo.security.branch_protection.enforce_admins is enabled to prevent
  administrators from bypassing branch protection rules.
```

### Integration Workflow

1. **Section 1**: Generate enriched benchmark metadata using `llm_generator/benchmark`
2. **Section 2**: Process with `generate_system_guidance.py` to add system compatibility
3. **Section 3**: (Future) Generate executable Python logic from system-enriched checks

### Error Handling

- Graceful handling of invalid JSON input
- Validation of field paths against resource schemas
- Fallback to basic compatibility for failed enrichments
- Comprehensive logging of processing issues
- Recovery strategies for partial processing failures
