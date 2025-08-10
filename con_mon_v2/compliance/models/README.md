# Database Models - 1:1 Schema Mapping

This models package provides **exact 1:1 mapping** with the actual database schema. CSV files are treated as the source of truth, and database interactions are eliminated in favor of CSV-based data loading.

## 📁 File Structure

```
con_mon_v2/models/
├── __init__.py                    # Package exports
├── README.md                      # This documentation
├── base.py                        # BaseModel with common functionality
├── framework.py                   # Framework model
├── control.py                     # Control model  
├── standard.py                    # Standard model
├── standard_control_mapping.py    # StandardControlMapping model
├── checks.py                      # Check model with JSONB nested models
└── helpers.py                     # Helper models for relationships
```

## 🎯 Design Principles

1. **1:1 Database Mapping**: Every field in the models matches exactly with database schema
2. **CSV Source of Truth**: Models are designed to load from CSV files, not database
3. **JSONB Representation**: Complex JSONB fields are properly modeled as nested Pydantic models
4. **No Inference**: Only fields that exist in the database are included

## 📊 Model Overview

### Core Models (1:1 DB Mapping)

| **Model** | **Table** | **Fields** | **Notes** |
|-----------|-----------|------------|-----------|
| `Framework` | `framework` | 8 fields | Perfect CSV-DB alignment |
| `Control` | `control` | 17 fields | Perfect CSV-DB alignment |
| `Standard` | `standard` | 11 fields | Perfect CSV-DB alignment |
| `StandardControlMapping` | `standard_control_mapping` | 7 fields | Perfect CSV-DB alignment |
| `Check` | `checks` | 12 fields | JSONB fields with nested models |

### JSONB Nested Models

| **Model** | **Purpose** | **Parent** |
|-----------|-------------|------------|
| `OutputStatements` | Check output messages | `Check.output_statements` |
| `FixDetails` | Fix instructions and details | `Check.fix_details` |
| `CheckMetadata` | Check execution metadata | `Check.metadata` |
| `CheckOperation` | Operation configuration | `CheckMetadata.operation` |

### Helper Models (Composite Views)

| **Model** | **Purpose** |
|-----------|-------------|
| `FrameworkWithControls` | Framework + its controls |
| `StandardWithControls` | Standard + mapped controls |
| `ControlWithStandards` | Control + mapped standards |
| `ControlWithChecks` | Control + validation checks |
| `CheckWithControls` | Check + associated controls |

## 🔧 Usage Examples

### Basic Model Usage

```python
from con_mon_v2.models import Framework, Control, Check

# Create a framework
framework = Framework(
    id=1,
    name="NIST 800-53",
    description="NIST cybersecurity framework",
    version=1,
    active=True
)

# Create a control
control = Control(
    id=1,
    framework_id=1,
    control_name="AC-1",
    control_long_name="Policy and Procedures",
    control_text="Develop, document, and disseminate...",
    family_name="Access Control"
)
```

### JSONB Field Usage

```python
from con_mon_v2.models import Check, CheckMetadata, CheckOperation, OutputStatements, FixDetails

# Create nested JSONB structures
metadata = CheckMetadata(
    tags=["compliance", "nist"],
    category="configuration",
    severity="medium",
    operation=CheckOperation(
        name="custom",
        logic="result = 'organizational mission' in fetched_value.lower()"
    ),
    field_path="repository_data.basic_info.description",
    connection_id=1,
    resource_type="con_mon_v2.mappings.github.GithubResource"
)

output_statements = OutputStatements(
    failure="Check failed: Repository description missing organizational mission",
    success="Check passed: Repository description includes organizational mission",
    partial="Check partially passed"
)

fix_details = FixDetails(
    description="Update repository description to include organizational mission",
    instructions=["Go to repository settings", "Edit description field"],
    estimated_date="2023-06-30",
    automation_available=False
)

# Create check with nested JSONB
check = Check(
    id="validate_organizational_context",
    name="validate_organizational_context", 
    description="Verifies repository description reflects organizational mission",
    output_statements=output_statements,
    fix_details=fix_details,
    metadata=metadata,
    created_by="system",
    category="configuration",
    updated_by="system",
    created_at=datetime.now(),
    updated_at=datetime.now(),
    is_deleted=False
)
```

### Helper Model Usage

```python
from con_mon_v2.models import FrameworkWithControls

# Load framework with its controls
framework_with_controls = FrameworkWithControls(
    id=1,
    name="NIST 800-53",
    controls=[control1, control2, control3]  # List of Control objects
)
```

## 🗃️ CSV Integration

The models are designed to work seamlessly with CSV data:

```python
import csv
from con_mon_v2.models import Framework

# Load from CSV
with open('data/csv/framework.csv', 'r') as f:
    reader = csv.DictReader(f)
    frameworks = [Framework(**row) for row in reader]

# Export to CSV  
framework_dicts = [fw.model_dump() for fw in frameworks]
```

## 🔄 Migration from Old Models

This replaces the previous `con_mon_v2/compliance/models.py` with:

- ✅ Exact database schema alignment
- ✅ Proper JSONB field representation  
- ✅ CSV-first data loading approach
- ✅ Elimination of database dependencies
- ✅ Clean separation of concerns

## 🚀 Benefits

1. **Accuracy**: Models exactly match database schema
2. **Performance**: CSV loading is faster than database queries
3. **Reliability**: No database connection dependencies
4. **Maintainability**: Clear, documented structure
5. **Flexibility**: Easy to extend and modify
6. **Type Safety**: Full Pydantic validation and type hints 