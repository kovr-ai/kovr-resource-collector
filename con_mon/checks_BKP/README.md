# Checks Module

The checks module provides a YAML-driven framework for validating collected resources against predefined rules and policies.

## Overview

Checks evaluate resource data using configurable operations and expected values. They support both simple comparisons and complex custom logic, with results stored in the database for monitoring and compliance tracking.

## Adding New Checks

### 1. Define Check in YAML (`checks.yaml`)

```yaml
checks:
  - id: 1004  # Unique integer ID
    name: "my_new_check"  # Unique name (used as function name)
    description: "Human readable description of what this check validates"
    field_path: "resource.field.path"  # Dot notation path to field
    operation:
      name: "EQUAL"  # Comparison operation
    expected_value: "expected_result"  # What the field should equal
    tags: ["category", "type", "severity"]  # For filtering and organization
    severity: "high"  # high/medium/low
    category: "security"  # Logical grouping
```

### 2. Supported Operations

#### Basic Comparisons
- `EQUAL` / `"=="` - Exact equality
- `NOT_EQUAL` / `"!="` - Not equal  
- `LESS_THAN` / `"<"` - Numeric less than
- `GREATER_THAN` / `">"` - Numeric greater than
- `LESS_THAN_OR_EQUAL` / `"<="` - Numeric less than or equal
- `GREATER_THAN_OR_EQUAL` / `">="` - Numeric greater than or equal

#### Container Operations  
- `CONTAINS` - Check if expected_value exists in fetched_value
- `NOT_CONTAINS` - Check if expected_value does NOT exist in fetched_value

#### Function Support in Field Paths
- `len(field.path)` - Get length/count of arrays or strings
- Future: `max(field.path)`, `min(field.path)`, `sum(field.path)`

#### Custom Logic
```yaml
operation:
  name: "custom"
  custom_logic: |
    # Python code with access to:
    # - fetched_value: the actual field value
    # - config_value: the expected_value from YAML
    # - result: boolean variable to set (required)
    
    if isinstance(fetched_value, list):
        result = len(fetched_value) > 0
    else:
        result = False
```

## Examples

### Simple Boolean Check
```yaml
- id: 2001
  name: "repository_has_wiki"
  description: "Verify repository wiki is enabled"
  field_path: "repository_data.features.wiki_enabled"
  operation:
    name: "EQUAL"
  expected_value: true
```

### Count/Length Check  
```yaml
- id: 2002
  name: "minimum_collaborators"
  description: "Repository must have at least 2 collaborators"
  field_path: "len(collaboration_data.collaborators)"
  operation:
    name: "GREATER_THAN_OR_EQUAL"
  expected_value: 2
```

### String Contains Check
```yaml
- id: 2003
  name: "required_topic_present"
  description: "Repository must include 'production' topic"
  field_path: "repository_data.topics"
  operation:
    name: "CONTAINS"
  expected_value: "production"
```

### Complex Custom Logic
```yaml
- id: 2004
  name: "recent_activity"
  description: "Repository must have commits in last 30 days"
  field_path: "repository_data.last_commit_date"
  operation:
    name: "custom"
    custom_logic: |
      from datetime import datetime, timedelta
      
      if fetched_value:
          last_commit = datetime.fromisoformat(fetched_value.replace('Z', '+00:00'))
          thirty_days_ago = datetime.now() - timedelta(days=30)
          result = last_commit > thirty_days_ago
      else:
          result = False
  expected_value: null
```

## Field Path Syntax

### Basic Dot Notation
- `field` - Top level field
- `object.property` - Nested object property  
- `object.nested.deep` - Deep nesting

### Function Calls
- `len(array_field)` - Length of array or string
- `len(object.nested.array)` - Length of nested array

### Accessing Different Data Types
```yaml
# GitHub resource example field paths:
field_path: "repository_data.basic_info.private"          # Boolean
field_path: "repository_data.basic_info.name"             # String  
field_path: "len(repository_data.branches)"               # Array length
field_path: "repository_data.stats.stargazers_count"      # Number
field_path: "collaboration_data.collaborators"            # Array
field_path: "security_data.vulnerability_alerts"          # Nested object
```

## Check Execution

### Programmatic Usage
```python
from con_mon.checks import get_checks_by_ids

# Get all checks
all_checks = get_checks_by_ids()

# Get specific checks
selected_checks = get_checks_by_ids([1001, 1002, 2001])

# Get single check  
single_check = get_checks_by_ids(1001)

# Execute checks
for check_id, check_name, check_function in selected_checks:
    results = check_function.evaluate(resource_collection)
    for result in results:
        print(f"{result.resource.name}: {'PASS' if result.passed else 'FAIL'}")
```

### Integration with Main Workflow
```python
# In main_new.py
executed_check_results = []
for check_id, check_name, check_function in checks_to_run:
    check_results = check_function.evaluate(resource_collection)
    executed_check_results.append((check_id, check_name, check_results))
```

## Best Practices

### Check Design
- **Single Purpose**: Each check should validate one specific rule
- **Clear Names**: Use descriptive names that explain what's being checked
- **Appropriate Severity**: Set severity based on business impact
- **Good Descriptions**: Explain why the check matters and what it validates

### Performance  
- **Simple Operations First**: Use basic comparisons when possible
- **Avoid Heavy Custom Logic**: Keep custom logic lightweight
- **Efficient Field Paths**: Access nested data directly rather than processing whole objects

### Maintainability
- **Group Related Checks**: Use consistent naming and categorization
- **Document Complex Logic**: Add comments in custom logic
- **Version Control**: Track changes to check definitions
- **Test Thoroughly**: Validate checks against real data

## Error Handling

The framework handles common errors gracefully:
- **Missing Fields**: Returns appropriate default values
- **Type Errors**: Logs errors and continues with other checks
- **Invalid Operations**: Clear error messages for unsupported operations
- **Custom Logic Errors**: Catches exceptions in custom code

## Integration

Checks automatically integrate with:
- **Database Storage**: Results stored in `con_mon_results` table
- **Summary Reports**: Formatted output via helpers module
- **Connection Management**: Works with database-driven configuration
- **Resource Collections**: Evaluates against any ResourceCollection type

## Testing New Checks

1. Add check definition to `checks.yaml`
2. Restart application to reload checks
3. Run with `main_new.py` to test against real data
4. Verify results in database or console output
5. Adjust field paths and operations as needed

This modular approach makes it easy to add, modify, and maintain validation rules across different resource types and providers. 