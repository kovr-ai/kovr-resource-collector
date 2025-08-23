# Benchmark Processing Scripts

This directory contains scripts for processing benchmark documents using the Section 1 workflow implementation.

## Main Script: `generate_metadata_and_checks.py`

A comprehensive CLI tool that executes the complete benchmark metadata generation workflow:

1. **Extract Checks Literature** - Uses LLM to extract atomic checks from benchmark text
2. **Map to Controls** - Maps LLM-suggested controls to database controls using ControlLoader  
3. **Generate Coverage Report** - Provides detailed metrics on mapping success

### Usage Examples

#### Basic Usage
```bash
# Process from file
python generate_metadata_and_checks.py --source "OWASP Top 10 2021" --file example_benchmark.txt

# Process with direct text input
python generate_metadata_and_checks.py --source "Custom Benchmark" --text "Your benchmark content here"

# Save results to file
python generate_metadata_and_checks.py --source "OWASP Top 10 2021" --file example_benchmark.txt --output results.json
```

#### Interactive Mode
```bash
# Interactive prompts for all inputs
python generate_metadata_and_checks.py --interactive
```

#### Advanced Options
```bash
# Verbose logging with custom version and context
python generate_metadata_and_checks.py --source "Mitre ATT&CK" --version "v13" --file attack_data.txt --verbose --context "Focus on detection techniques"

# Quiet mode (no summary output)
python generate_metadata_and_checks.py --source "PCI DSS" --file pci_requirements.txt --quiet --output pci_results.json
```

#### Getting Help
```bash
# Show all available options
python generate_metadata_and_checks.py --help

# Show example benchmark sources
python generate_metadata_and_checks.py --examples
```

### Script Features

#### 🎯 **Complete Workflow Implementation**
- **Step 1**: LLM-powered check extraction with control suggestions
- **Step 2**: Smart control mapping using multiple strategies
- **Step 3**: Comprehensive coverage reporting

#### 🔧 **Flexible Input Options**
- Load from text files
- Direct text input via command line
- Interactive mode with prompts
- Support for any benchmark format

#### 📊 **Rich Output and Reporting**
- Detailed processing summary
- Coverage percentages and metrics
- Top mapped checks display
- Unmapped control suggestions tracking
- JSON export for further processing

#### 🛠️ **Production Ready**
- Comprehensive error handling
- Verbose logging options
- Progress tracking
- Configurable output formats

### Output Structure

The script generates comprehensive results including:

```json
{
  "benchmark_info": {
    "source": "OWASP Top 10 2021",
    "version": "2021", 
    "processing_date": "2024-01-15T10:30:00",
    "document_length": 15420
  },
  "extraction_metadata": {
    "total_checks_extracted": 12,
    "extraction_date": "2024-01-15T10:30:15"
  },
  "processed_checks": [
    {
      "check_id": "OWASP2021-A01-001",
      "title": "Deny by default access controls",
      "description": "Access control mechanisms should implement deny-by-default policy",
      "suggested_controls": ["NIST-800-53-AC-3", "ISO-27001-A.9.1.2"],
      "controls": ["AC-3"],
      "frameworks": ["NIST-800-53"],
      "mapping_confidence": 0.8,
      "control_reasoning": "Access control policy enforcement"
    }
  ],
  "coverage_report": {
    "total_checks_extracted": 12,
    "mapped_to_controls": 10,
    "coverage_percentages": {
      "control_mapping": 83.3,
      "benchmark_mapping": 25.0
    }
  },
  "summary": {
    "total_checks_extracted": 12,
    "checks_mapped_to_controls": 10,
    "average_mapping_confidence": 0.75,
    "unique_frameworks": 2,
    "processing_status": "completed"
  }
}
```

### Example Files

- `example_benchmark.txt` - Sample OWASP Top 10 content for testing
- `README.md` - This documentation

### Integration with Main System

The script uses the complete `llm_generator.benchmark` package and integrates with:
- `con_mon.utils.llm.client` for LLM processing
- `con_mon.compliance.data_loader.ControlLoader` for control mapping
- Your existing control database and framework mappings

### Error Handling

The script includes comprehensive error handling for:
- File not found errors
- Invalid JSON responses from LLM
- Database connection issues  
- Control mapping failures
- Interrupted processing (Ctrl+C)

All errors are logged with appropriate detail levels based on verbosity settings.

### Performance Considerations

- **Lazy Loading**: Controls and checks are loaded on-demand
- **Caching**: Database objects are cached within processing session  
- **Memory Efficient**: Processes documents of various sizes efficiently
- **Progress Tracking**: Provides feedback during long-running operations

This script provides a complete, production-ready interface to the Section 1 benchmark metadata generation workflow!
