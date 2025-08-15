# Data Loader Package - Database Only

This data_loader package provides individual loaders for each model type, focusing **only on database operations** for now. Each loader handles one specific table with exact 1:1 field mapping.

## 📁 File Structure

```
con_mon/compliance/data_loader/
├── __init__.py                           # Package exports
├── README.md                             # This documentation
├── base.py                               # BaseLoader with common DB functionality
├── framework_loader.py                   # FrameworkLoader for framework table
├── control_loader.py                     # ControlLoader for control table
├── standard_loader.py                    # StandardLoader for standard table
├── standard_control_mapping_loader.py    # StandardControlMappingLoader for mappings
└── checks_loader.py                      # ChecksLoader for checks table (with JSONB)
```

## 🎯 Design Principles

1. **Database Only**: Only DB loaders for now, CSV loaders will be added later
2. **Individual Files**: One loader per model type for clean separation
3. **1:1 Field Mapping**: Direct database field to model field mapping
4. **JSONB Support**: Proper handling of JSONB fields in checks table
5. **Common Base**: Shared functionality in BaseLoader

## 📊 Loader Overview

| **Loader** | **Model** | **Table** | **Fields** | **Special Features** |
|------------|-----------|-----------|------------|---------------------|
| `FrameworkLoader` | `Framework` | `framework` | 8 fields | Simple 1:1 mapping |
| `ControlLoader` | `Control` | `control` | 17 fields | Complex control data |
| `StandardLoader` | `Standard` | `standard` | 11 fields | Array field support |
| `StandardControlMappingLoader` | `StandardControlMapping` | `standard_control_mapping` | 7 fields | Relationship mapping |
| `ChecksLoader` | `Check` | `checks` | 12 fields | JSONB field handling |

## 🔧 Usage Examples

### Basic Usage

```python
from con_mon.compliance.data_loader import FrameworkLoader, ControlLoader

# Load all frameworks
framework_loader = FrameworkLoader()
frameworks = framework_loader.load_all()

# Load all controls
control_loader = ControlLoader()
controls = control_loader.load_all()

print(f"Loaded {len(frameworks)} frameworks and {len(controls)} controls")
```

### Load by IDs

```python
from con_mon.compliance.data_loader import StandardLoader

# Load specific standards by ID
standard_loader = StandardLoader()
standards = standard_loader.load_by_ids([1, 2, 3])

print(f"Loaded {len(standards)} specific standards")
```

### JSONB Field Handling (Checks)

```python
from con_mon.compliance.data_loader import ChecksLoader

# Load checks with JSONB fields
checks_loader = ChecksLoader()
checks = checks_loader.load_all()

# Access nested JSONB data
for check in checks:
    print(f"Check: {check.name}")
    print(f"  Operation: {check.metadata.operation.name}")
    print(f"  Tags: {check.metadata.tags}")
    print(f"  Fix Steps: {len(check.fix_details.instructions)} steps")
```

## 🏗️ BaseLoader Features

The `BaseLoader` provides common functionality:

- **Database Connection**: Automatic DB connection management
- **Query Building**: Builds SELECT queries with proper field selection
- **Row Processing**: Converts raw DB rows to model instances
- **Error Handling**: Proper error handling and logging
- **ID Filtering**: Support for loading specific records by ID

## 🔄 Row Processing Flow

1. **Raw Query**: Execute SQL query to get raw database rows
2. **Row Processing**: Call `process_row()` method (can be overridden)
3. **Model Creation**: Use `model.from_row()` to create model instances
4. **Type Conversion**: Automatic handling of datetime, bool, JSON, array fields

## ⚙️ Extending Loaders

### Custom Row Processing

```python
class CustomControlLoader(ControlLoader):
    def process_row(self, raw_row: Dict[str, Any]) -> Dict[str, Any]:
        # Custom processing before model creation
        processed_row = super().process_row(raw_row)
        
        # Add custom logic here
        if processed_row.get('active') is None:
            processed_row['active'] = True
            
        return processed_row
```

### Additional Query Methods

```python
class FrameworkLoader(BaseLoader):
    # ... existing methods ...
    
    def load_active_only(self) -> List[Framework]:
        """Load only active frameworks."""
        query = f"""
        SELECT {', '.join(self.get_select_fields())} 
        FROM {self.get_table_name()} 
        WHERE active = true 
        ORDER BY id
        """
        
        raw_rows = self.db.execute_query(query)
        instances = []
        for raw_row in raw_rows:
            processed_row = self.process_row(raw_row)
            instance = self.get_model_class().from_row(processed_row)
            instances.append(instance)
            
        return instances
```

## 🚀 Benefits

1. **Clean Separation**: Each loader handles one specific table
2. **Maintainable**: Easy to understand and modify individual loaders
3. **Extensible**: Easy to add custom methods or processing
4. **Type Safe**: Full type hints and model validation
5. **Efficient**: Direct database queries with only needed fields
6. **Consistent**: Common interface across all loaders

## 📋 Future Enhancements

- **CSV Loaders**: Add CSV loading capability to each loader
- **Caching**: Add optional caching for frequently accessed data
- **Filtering**: Add more sophisticated filtering options
- **Relationships**: Add methods to load related data automatically
- **Bulk Operations**: Add bulk insert/update capabilities

This structure provides a clean, maintainable way to load compliance data from the database with proper separation of concerns and easy extensibility. 