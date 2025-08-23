# Benchmark Data Storage

This directory stores processed benchmark data in a structured format that facilitates easy access and organization.

## Directory Structure

```
data/benchmarks/<benchmark_name>/
├── metadata.yaml       # Benchmark info and extraction metadata  
├── coverage.yaml       # Coverage report with mapping statistics
└── checks/             # Individual check files
    ├── <check_id_1>.yaml
    ├── <check_id_2>.yaml
    └── <check_id_n>.yaml
```

## File Descriptions

### `metadata.yaml`
Contains benchmark processing information:
- **benchmark_info**: Source, version, processing date, document length
- **extraction_metadata**: LLM extraction results and statistics  
- **summary**: High-level processing results
- **processing_completed_at**: Final completion timestamp

### `coverage.yaml`
Contains coverage and mapping statistics:
- **total_checks_extracted**: Number of checks extracted from benchmark
- **mapped_to_controls**: Number of checks successfully mapped to existing controls
- **mapped_to_existing_benchmarks**: Number mapped to existing benchmark checks
- **coverage_percentages**: Extraction, control mapping, and benchmark mapping percentages
- **report_generated_at**: Coverage report timestamp

### `checks/<check_id>.yaml`
Individual check files containing:
- **check_id**: Globally unique identifier (e.g., "OWASP-2021-A01-001")
- **title**: Short descriptive name
- **description**: Detailed, actionable requirement
- **benchmark_source**: Source benchmark reference
- **category**: Check category (Access Control, Authentication, etc.)
- **severity**: Risk severity level (high, medium, low)
- **tags**: Classification tags for filtering
- **suggested_controls**: LLM-suggested control mappings
- **control_reasoning**: Explanation of control suggestions
- **controls**: Successfully mapped control IDs
- **frameworks**: Framework names for mapped controls
- **benchmark_mapping**: Existing benchmark check IDs (if any)
- **mapping_confidence**: Confidence score for mappings (0.0-1.0)
- **extracted_at**: Initial extraction timestamp
- **mapped_at**: Control mapping completion timestamp

## Usage Examples

### Generate and Save Structured Data
```bash
# Process OWASP Top 10 and save structured data
python generate_metadata_and_checks.py \
  --source "OWASP Top 10 2021" \
  --file owasp_top10.txt \
  --save-structured

# Process custom benchmark with structured output  
python generate_metadata_and_checks.py \
  --source "Custom Security Framework" \
  --text "Your benchmark text here" \
  --save-structured

# Save to custom data directory
python generate_metadata_and_checks.py \
  --source "PCI DSS v4.0" \
  --file pci_requirements.txt \
  --save-structured \
  --data-dir /custom/data/path
```

### Access Processed Data
```python
import yaml
from pathlib import Path

# Load benchmark metadata
with open('data/benchmarks/owasp_top_10_2021/metadata.yaml') as f:
    metadata = yaml.safe_load(f)

# Load coverage report  
with open('data/benchmarks/owasp_top_10_2021/coverage.yaml') as f:
    coverage = yaml.safe_load(f)

# Load individual checks
checks_dir = Path('data/benchmarks/owasp_top_10_2021/checks')
for check_file in checks_dir.glob('*.yaml'):
    with open(check_file) as f:
        check = yaml.safe_load(f)
        print(f"Check: {check['check_id']} - {check['title']}")
```

## Benefits

1. **Organized Storage**: Clear separation of metadata, coverage, and individual checks
2. **Easy Access**: YAML format is human-readable and machine-parsable  
3. **Scalability**: Individual check files prevent large file performance issues
4. **Traceability**: Complete audit trail from extraction to final mapping
5. **Reusability**: Structured format enables easy integration with other tools
6. **Version Control**: Small files work well with git and change tracking
