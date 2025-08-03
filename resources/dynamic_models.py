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


def resolve_resource_type_reference(field_type: str, all_models: Dict[str, Type[BaseModel]]) -> Type:
    """Resolve resource type references like 'github_resource_array' to proper types."""
    if field_type == 'github_resource_array':
        # This should be List[GithubResource] - we'll handle this after all models are created
        return List[Any]  # Placeholder for now
    
    # Handle other special types here
    return yaml_type_to_python_type(field_type)


def create_resource_model_from_schema(resource_name: str, schema_definition: Dict[str, Any], all_schemas: Dict[str, Any] = None) -> Type[BaseModel]:
    """Create a Pydantic model from a resource schema definition."""
    
    # Check if this is a collection type
    is_collection = 'collection_type' in schema_definition
    
    if is_collection:
        # Base fields for collections
        base_fields = {
            'source_connector': (str, Field(description="Source connector that fetched this collection")),
            'total_count': (int, Field(description="Total number of resources in the collection")),
            'fetched_at': (datetime, Field(default_factory=datetime.now, description="When this collection was fetched")),
            'metadata': (Dict[str, Any], Field(default_factory=dict, description="Collection metadata"))
        }
    else:
        # Base fields for individual resources
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
        elif isinstance(field_def, str):
            # Handle special field types
            if field_def == 'github_resource_array':
                # This will be resolved later after all models are created
                base_fields[field_name] = (List[Any], Field(default_factory=list, description="List of GitHub resources"))
            else:
                # Simple field
                field_type = yaml_type_to_python_type(field_def)
                base_fields[field_name] = (Optional[field_type], None)
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
        if hasattr(self, 'tags') and tag not in self.tags:
            self.tags.append(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.model_dump()
    
    # Add collection-specific methods
    if is_collection:
        def __len__(self) -> int:
            """Return the number of resources in the collection."""
            return len(self.resources) if hasattr(self, 'resources') else 0
        
        def __iter__(self):
            """Make the collection iterable."""
            return iter(self.resources) if hasattr(self, 'resources') else iter([])
        
        def __getitem__(self, index: Union[int, slice]):
            """Allow indexing and slicing of the collection."""
            if hasattr(self, 'resources'):
                return self.resources[index]
            raise IndexError("Collection has no resources")
        
        def add_resource(self, resource) -> None:
            """Add a resource to the collection."""
            if hasattr(self, 'resources'):
                self.resources.append(resource)
                self.total_count = len(self.resources)
        
        # Add collection methods to the model
        model.__len__ = __len__
        model.__iter__ = __iter__
        model.__getitem__ = __getitem__
        model.add_resource = add_resource
    
    # Add common methods to the model
    model.get_field_value = get_field_value
    model.add_tag = add_tag  
    model.to_dict = to_dict
    
    # Add metadata to the model
    model.__is_collection__ = is_collection
    if is_collection:
        model.__collection_type__ = schema_definition.get('collection_type')
    
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
        all_schemas = yaml_data.get('resources', {})
        
        # First pass: Create all models
        if 'resources' in yaml_data:
            for resource_name, resource_config in all_schemas.items():
                # Create dynamic Pydantic model
                model_class = create_resource_model_from_schema(resource_name, resource_config, all_schemas)
                
                # Store the model
                dynamic_models[resource_name] = model_class
                
                # Add provider info to the model
                model_class.__provider__ = resource_config.get('provider', 'unknown')
                model_class.__description__ = resource_config.get('description', '')
        
        # Second pass: Resolve resource type references and recreate models with proper types
        for resource_name, model_class in dynamic_models.items():
            schema_config = all_schemas[resource_name]
            if 'collection_type' in schema_config:
                # This is a collection - recreate with proper resource type
                collection_type = schema_config['collection_type']
                if collection_type in dynamic_models:
                    resource_type = dynamic_models[collection_type]
                    
                    # Recreate the model with proper resource type
                    model_class = create_collection_model_with_resource_type(
                        resource_name, schema_config, resource_type, all_schemas
                    )
                    
                    # Update the stored model
                    dynamic_models[resource_name] = model_class
                    
                    # Add provider info to the model
                    model_class.__provider__ = schema_config.get('provider', 'unknown')
                    model_class.__description__ = schema_config.get('description', '')
                    model_class.__resource_type__ = resource_type
        
        print(f"✅ Created {len(dynamic_models)} dynamic Pydantic models from {yaml_file_path}")
        return dynamic_models
        
    except Exception as e:
        print(f"❌ Error creating dynamic models: {e}")
        return {}


def create_collection_model_with_resource_type(resource_name: str, schema_definition: Dict[str, Any], resource_type: Type[BaseModel], all_schemas: Dict[str, Any]) -> Type[BaseModel]:
    """Create a collection model with properly typed resource field."""
    
    # Base fields for collections
    base_fields = {
        'resources': (List[resource_type], Field(default_factory=list, description=f"List of {resource_type.__name__} objects")),
        'source_connector': (str, Field(description="Source connector that fetched this collection")),
        'total_count': (int, Field(description="Total number of resources in the collection")),
        'fetched_at': (datetime, Field(default_factory=datetime.now, description="When this collection was fetched")),
        'metadata': (Dict[str, Any], Field(default_factory=dict, description="Collection metadata"))
    }
    
    # Add schema-specific fields (excluding resources since we handled it above)
    schema_fields = schema_definition.get('fields', {})
    for field_name, field_def in schema_fields.items():
        if field_name == 'resources':
            continue  # Already handled above
            
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
        elif isinstance(field_def, str):
            # Simple field
            field_type = yaml_type_to_python_type(field_def)
            base_fields[field_name] = (Optional[field_type], None)
        else:
            # Simple field
            field_type = yaml_type_to_python_type(field_def)
            base_fields[field_name] = (Optional[field_type], None)
    
    # Create the model
    model = create_model(resource_name, **base_fields)
    
    # Add collection-specific methods
    def __len__(self) -> int:
        """Return the number of resources in the collection."""
        return len(self.resources)
    
    def __iter__(self):
        """Make the collection iterable."""
        return iter(self.resources)
    
    def __getitem__(self, index: Union[int, slice]):
        """Allow indexing and slicing of the collection."""
        return self.resources[index]
    
    def add_resource(self, resource) -> None:
        """Add a resource to the collection."""
        self.resources.append(resource)
        self.total_count = len(self.resources)
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return self.model_dump()
    
    # Add methods to the model
    model.__len__ = __len__
    model.__iter__ = __iter__
    model.__getitem__ = __getitem__
    model.add_resource = add_resource
    model.get_field_value = get_field_value
    model.to_dict = to_dict
    
    # Add metadata to the model
    model.__is_collection__ = True
    model.__collection_type__ = schema_definition.get('collection_type')
    
    return model


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