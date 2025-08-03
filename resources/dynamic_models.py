"""
Dynamic Pydantic model generation from YAML schema definitions.
"""
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field, create_model
from datetime import datetime
import yaml
import os


def yaml_type_to_python_type(yaml_type: str) -> Type:
    """Convert YAML type strings to Python types."""
    type_mapping = {
        'string': str,
        'integer': int,
        'float': float,
        'boolean': bool,
        'array': List,
        'object': Dict[str, Any],
        'datetime': datetime
    }
    return type_mapping.get(yaml_type, str)


def create_nested_model(name: str, fields_definition: Dict[str, Any]) -> Type[BaseModel]:
    """Create a nested Pydantic model from fields definition."""
    pydantic_fields = {}
    
    for field_name, field_def in fields_definition.items():
        if isinstance(field_def, dict):
            # This is a nested object
            nested_model = create_nested_model(f"{name}_{field_name.title()}", field_def)
            pydantic_fields[field_name] = (nested_model, Field(default_factory=dict))
        elif isinstance(field_def, list) and len(field_def) > 0:
            # This is an array with nested objects
            if isinstance(field_def[0], dict):
                item_model = create_nested_model(f"{name}_{field_name.title()}Item", field_def[0])
                pydantic_fields[field_name] = (List[item_model], Field(default_factory=list))
            else:
                item_type = yaml_type_to_python_type(field_def[0])
                pydantic_fields[field_name] = (List[item_type], Field(default_factory=list))
        else:
            # Simple field
            field_type = yaml_type_to_python_type(field_def)
            pydantic_fields[field_name] = (Optional[field_type], None)
    
    return create_model(name, **pydantic_fields)


def create_resource_model_from_schema(resource_name: str, schema_definition: Dict[str, Any]) -> Type[BaseModel]:
    """Create a Pydantic model from a resource schema definition."""
    
    # Base fields that all resources have
    base_fields = {
        'id': (str, Field(description="Unique identifier for the resource")),
        'source_connector': (str, Field(description="Source connector that fetched this resource")),
        'created_at': (datetime, Field(default_factory=datetime.now)),
        'updated_at': (datetime, Field(default_factory=datetime.now)),
        'metadata': (Dict[str, Any], Field(default_factory=dict)),
        'tags': (List[str], Field(default_factory=list))
    }
    
    # Add schema-specific fields
    schema_fields = schema_definition.get('fields', {})
    for field_name, field_def in schema_fields.items():
        if isinstance(field_def, dict):
            # Nested object
            nested_model = create_nested_model(f"{resource_name}_{field_name.title()}", field_def)
            base_fields[field_name] = (nested_model, Field(default_factory=dict))
        elif isinstance(field_def, list) and len(field_def) > 0:
            # Array
            if isinstance(field_def[0], dict):
                item_model = create_nested_model(f"{resource_name}_{field_name.title()}Item", field_def[0])
                base_fields[field_name] = (List[item_model], Field(default_factory=list))
            else:
                item_type = yaml_type_to_python_type(field_def[0])
                base_fields[field_name] = (List[item_type], Field(default_factory=list))
        else:
            # Simple field
            field_type = yaml_type_to_python_type(field_def)
            base_fields[field_name] = (Optional[field_type], None)
    
    # Create the model
    model = create_model(resource_name, **base_fields)
    
    # Add useful methods
    def get_field_value(self, field_path: str) -> Any:
        """Get a field value using dot notation."""
        keys = field_path.split('.')
        value = self
        
        for key in keys:
            if hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
        return value
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the resource."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.dict()
    
    # Add methods to the model
    model.get_field_value = get_field_value
    model.add_tag = add_tag  
    model.to_dict = to_dict
    
    return model


def load_and_create_dynamic_models(yaml_file_path: str = None) -> Dict[str, Type[BaseModel]]:
    """Load YAML schemas and create dynamic Pydantic models."""
    
    if yaml_file_path is None:
        current_dir = os.path.dirname(__file__)
        yaml_file_path = os.path.join(current_dir, 'resources.yaml')
    
    try:
        with open(yaml_file_path, 'r') as file:
            yaml_data = yaml.safe_load(file)
        
        dynamic_models = {}
        
        if 'resources' in yaml_data:
            for resource_name, resource_config in yaml_data['resources'].items():
                # Create dynamic Pydantic model
                model_class = create_resource_model_from_schema(resource_name, resource_config)
                
                # Store the model
                dynamic_models[resource_name] = model_class
                
                # Add provider info to the model
                model_class.__provider__ = resource_config.get('provider', 'unknown')
                model_class.__description__ = resource_config.get('description', '')
        
        print(f"✅ Created {len(dynamic_models)} dynamic Pydantic models from {yaml_file_path}")
        return dynamic_models
        
    except Exception as e:
        print(f"❌ Error creating dynamic models: {e}")
        return {}


# Global storage for dynamic models
_dynamic_models: Dict[str, Type[BaseModel]] = {}


def get_dynamic_models() -> Dict[str, Type[BaseModel]]:
    """Get all loaded dynamic models."""
    return _dynamic_models.copy()


def initialize_dynamic_models():
    """Initialize dynamic models on module import."""
    global _dynamic_models
    _dynamic_models = load_and_create_dynamic_models()
    return _dynamic_models 