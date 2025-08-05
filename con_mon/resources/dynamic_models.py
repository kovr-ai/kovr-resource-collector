"""
Dynamic Pydantic model generation from YAML schema definitions.
"""
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field, create_model
from datetime import datetime
import yaml
import os
from .models import Resource


def yaml_type_to_python_type(yaml_type: str, available_models: Dict[str, Type[BaseModel]] = None) -> type:
    """Convert YAML type string to Python type, handling model references."""
    # Check if this is a reference to another model
    if available_models and yaml_type in available_models:
        return available_models[yaml_type]
    
    type_mapping = {
        'string': str,
        'integer': int,
        'boolean': bool,
        'float': float,
        'array': list,
        'object': dict,
        'datetime': datetime
    }
    return type_mapping.get(yaml_type, str)


def create_nested_model(name: str, fields_definition: Dict[str, Any], available_models: Dict[str, Type[BaseModel]] = None) -> Type[BaseModel]:
    """Create a nested Pydantic model from fields definition."""
    pydantic_fields = {}
    
    for field_name, field_def in fields_definition.items():
        if isinstance(field_def, dict):
            # This is a nested object
            nested_model = create_nested_model(f"{name}_{field_name.title()}", field_def, available_models)
            pydantic_fields[field_name] = (nested_model, Field(default_factory=dict))
        elif isinstance(field_def, list) and len(field_def) > 0:
            # This is an array with nested objects
            if isinstance(field_def[0], dict):
                item_model = create_nested_model(f"{name}_{field_name.title()}Item", field_def[0], available_models)
                pydantic_fields[field_name] = (List[item_model], Field(default_factory=list))
            else:
                item_type = yaml_type_to_python_type(field_def[0], available_models)
                pydantic_fields[field_name] = (List[item_type], Field(default_factory=list))
        else:
            # Simple field - check if it's a model reference
            field_type = yaml_type_to_python_type(field_def, available_models)
            pydantic_fields[field_name] = (Optional[field_type], None)
    
    # Create and return the nested model
    return create_model(name, **pydantic_fields)


def resolve_resource_type_reference(field_type: str, all_models: Dict[str, Type[BaseModel]]) -> Type:
    """Resolve resource type references like 'github_resource_array' to proper types."""
    if field_type == 'github_resource_array':
        # This should be List[GithubResource] - we'll handle this after all models are created
        return List[Any]  # Placeholder for now
    
    # Handle other special types here
    return yaml_type_to_python_type(field_type)


def create_resource_model_from_schema(resource_name: str, schema_definition: Dict[str, Any], all_schemas: Dict[str, Any], available_models: Dict[str, Type[BaseModel]] = None) -> Type[BaseModel]:
    """Create a dynamic Pydantic model from a resource schema definition."""
    
    # Start with empty fields - base Resource fields will be inherited only for main Resource
    base_fields = {}
    
    # Process schema fields
    fields_definition = schema_definition.get('fields', {})
    for field_name, field_def in fields_definition.items():
        if isinstance(field_def, dict):
            # Nested object
            nested_model = create_nested_model(f"{resource_name}_{field_name.title()}", field_def, available_models)
            base_fields[field_name] = (nested_model, Field(default_factory=dict))
        elif isinstance(field_def, list) and len(field_def) > 0:
            # Array
            if isinstance(field_def[0], dict):
                item_model = create_nested_model(f"{resource_name}_{field_name.title()}Item", field_def[0], available_models)
                base_fields[field_name] = (List[item_model], Field(default_factory=list))
            else:
                item_type = yaml_type_to_python_type(field_def[0], available_models)
                base_fields[field_name] = (List[item_type], Field(default_factory=list))
        elif isinstance(field_def, str):
            # Handle special field types and model references
            if field_def == 'github_resource_array':
                # This will be resolved later after all models are created
                base_fields[field_name] = (List[Any], Field(default_factory=list, description="List of GitHub resources"))
            else:
                # Simple field or model reference
                field_type = yaml_type_to_python_type(field_def, available_models)
                base_fields[field_name] = (Optional[field_type], None)
        else:
            # Simple field
            field_type = yaml_type_to_python_type(str(field_def), available_models)
            base_fields[field_name] = (Optional[field_type], None)
    
    # Determine base class based on model type
    base_class = None
    if resource_name.endswith('Resource'):
        # Main resource models inherit from Resource
        base_class = Resource
    elif resource_name.endswith('ResourceCollection'):
        # Collection models inherit from ResourceCollection (but this is handled elsewhere)
        from .models import ResourceCollection
        base_class = ResourceCollection
    # Nested models (RepositoryData, ActionsData, etc.) don't inherit from anything special
    
    # Create the model with appropriate base class
    if base_class:
        model = create_model(resource_name, __base__=base_class, **base_fields)
    else:
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
    if 'collection_type' in schema_definition:
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
    model.__is_collection__ = 'collection_type' in schema_definition
    if model.__is_collection__:
        model.__collection_type__ = schema_definition['collection_type']
    
    return model


def create_collection_model_with_resource_type(resource_name: str, schema_definition: Dict[str, Any], resource_type: Type[BaseModel], all_schemas: Dict[str, Any], available_models: Dict[str, Type[BaseModel]] = None) -> Type[BaseModel]:
    """Create a collection model with properly typed resource field."""
    
    # Import ResourceCollection base class
    from .models import ResourceCollection
    
    # Base fields for collections - these will be inherited from ResourceCollection
    base_fields = {}
    
    # Add schema-specific fields (excluding standard ResourceCollection fields)
    schema_fields = schema_definition.get('fields', {})
    for field_name, field_def in schema_fields.items():
        if field_name in ['resources', 'source_connector', 'total_count', 'fetched_at', 'metadata']:
            # Skip standard ResourceCollection fields - they'll be inherited
            # But we need to override 'resources' with the proper type
            if field_name == 'resources':
                base_fields[field_name] = (List[resource_type], Field(default_factory=list, description=f"List of {resource_type.__name__} objects"))
            continue
            
        if isinstance(field_def, dict):
            # Nested object
            nested_model = create_nested_model(f"{resource_name}_{field_name.title()}", field_def, available_models)
            base_fields[field_name] = (nested_model, Field(default_factory=dict))
        elif isinstance(field_def, list) and len(field_def) > 0:
            # Array
            if isinstance(field_def[0], dict):
                item_model = create_nested_model(f"{resource_name}_{field_name.title()}Item", field_def[0], available_models)
                base_fields[field_name] = (List[item_model], Field(default_factory=list))
            else:
                item_type = yaml_type_to_python_type(field_def[0], available_models)
                base_fields[field_name] = (List[item_type], Field(default_factory=list))
        elif isinstance(field_def, str):
            # Simple field
            field_type = yaml_type_to_python_type(field_def, available_models)
            base_fields[field_name] = (Optional[field_type], None)
        else:
            # Simple field
            field_type = yaml_type_to_python_type(str(field_def), available_models)
            base_fields[field_name] = (Optional[field_type], None)
    
    # Override resources field with proper typing
    base_fields['resources'] = (List[resource_type], Field(default_factory=list, description=f"List of {resource_type.__name__} objects"))
    
    # Create the model inheriting from ResourceCollection
    model = create_model(resource_name, __base__=ResourceCollection, **base_fields)
    
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


def create_multi_resource_collection_model(resource_name: str, schema_definition: Dict[str, Any], resource_types: List[Type[BaseModel]], all_schemas: Dict[str, Any], available_models: Dict[str, Type[BaseModel]] = None) -> Type[BaseModel]:
    """Create a collection model that can handle multiple resource types (for AWS)."""
    
    # Import ResourceCollection base class
    from .models import ResourceCollection
    
    # Base fields for collections - these will be inherited from ResourceCollection
    base_fields = {}
    
    # Add schema-specific fields (excluding standard ResourceCollection fields)
    schema_fields = schema_definition.get('fields', {})
    for field_name, field_def in schema_fields.items():
        if field_name in ['resources', 'source_connector', 'total_count', 'fetched_at', 'metadata']:
            # Skip standard ResourceCollection fields - they'll be inherited
            # But we need to override 'resources' with the proper type
            if field_name == 'resources':
                # For multi-resource collections, use Union of all resource types
                from typing import Union
                if len(resource_types) > 1:
                    union_type = Union[tuple(resource_types)]
                    base_fields[field_name] = (List[union_type], Field(default_factory=list, description=f"List of AWS resource objects"))
                elif len(resource_types) == 1:
                    base_fields[field_name] = (List[resource_types[0]], Field(default_factory=list, description=f"List of {resource_types[0].__name__} objects"))
                else:
                    base_fields[field_name] = (List[Any], Field(default_factory=list, description="List of resource objects"))
            continue
            
        if isinstance(field_def, dict):
            # Nested object
            nested_model = create_nested_model(f"{resource_name}_{field_name.title()}", field_def, available_models)
            base_fields[field_name] = (nested_model, Field(default_factory=dict))
        elif isinstance(field_def, list) and len(field_def) > 0:
            # Array - skip the resource references as they're handled above
            if field_name == 'resources':
                continue
            if isinstance(field_def[0], dict):
                item_model = create_nested_model(f"{resource_name}_{field_name.title()}Item", field_def[0], available_models)
                base_fields[field_name] = (List[item_model], Field(default_factory=list))
            else:
                item_type = yaml_type_to_python_type(field_def[0], available_models)
                base_fields[field_name] = (List[item_type], Field(default_factory=list))
        elif isinstance(field_def, str):
            # Simple field
            field_type = yaml_type_to_python_type(field_def, available_models)
            base_fields[field_name] = (Optional[field_type], None)
        else:
            # Simple field
            field_type = yaml_type_to_python_type(str(field_def), available_models)
            base_fields[field_name] = (Optional[field_type], None)
    
    # Create the model inheriting from ResourceCollection
    model = create_model(resource_name, __base__=ResourceCollection, **base_fields)
    
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
    
    def get_resources_by_service(self, service: str) -> List[Any]:
        """Get resources filtered by AWS service."""
        return [r for r in self.resources if hasattr(r, '__service__') and r.__service__ == service]
    
    def get_ec2_resources(self) -> List[Any]:
        """Get EC2 resources from the collection."""
        return self.get_resources_by_service('ec2')
    
    def get_iam_resources(self) -> List[Any]:
        """Get IAM resources from the collection."""
        return self.get_resources_by_service('iam')
    
    def get_s3_resources(self) -> List[Any]:
        """Get S3 resources from the collection."""
        return self.get_resources_by_service('s3')
    
    def get_cloudtrail_resources(self) -> List[Any]:
        """Get CloudTrail resources from the collection."""
        return self.get_resources_by_service('cloudtrail')
    
    def get_cloudwatch_resources(self) -> List[Any]:
        """Get CloudWatch resources from the collection."""
        return self.get_resources_by_service('cloudwatch')
    
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
    model.get_resources_by_service = get_resources_by_service
    model.get_ec2_resources = get_ec2_resources
    model.get_iam_resources = get_iam_resources
    model.get_s3_resources = get_s3_resources
    model.get_cloudtrail_resources = get_cloudtrail_resources
    model.get_cloudwatch_resources = get_cloudwatch_resources
    model.get_field_value = get_field_value
    model.to_dict = to_dict
    
    # Add metadata to the model
    model.__is_collection__ = True
    model.__collection_type__ = schema_definition.get('collection_type')
    model.__resource_types__ = resource_types
    
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
        
        # Process each provider section (e.g., 'github', 'aws')
        for provider_name, provider_config in yaml_data.items():
            if not isinstance(provider_config, dict):
                continue
                
            # Get the structured sections
            resources_field_schemas = provider_config.get('resources_field_schemas', {})
            resources_section = provider_config.get('resources', {})
            main_collection = provider_config.get('ResourceCollection')
            
            # Determine creation order within this provider
            data_models = []      # Models from resources_field_schemas
            resource_models = []  # Resource models from resources section
            
            # First, get data models from resources_field_schemas section
            for model_name, model_config in resources_field_schemas.items():
                if isinstance(model_config, dict):
                    data_models.append((model_name, model_config))
            
            # Then, get resource models from resources section
            for model_name, model_config in resources_section.items():
                if isinstance(model_config, dict):
                    resource_models.append((model_name, model_config))
            
            # First pass: Create nested data models
            for model_name, model_config in data_models:
                full_model_name = model_name  # Keep original name like 'RepositoryData'
                model_class = create_resource_model_from_schema(full_model_name, model_config, provider_config, dynamic_models)
                dynamic_models[full_model_name] = model_class
                model_class.__provider__ = provider_name
                model_class.__description__ = model_config.get('description', '')
            
            # Second pass: Create resource models
            for model_name, model_config in resource_models:
                if provider_name == 'github':
                    # GitHub has a single Resource model
                    full_model_name = f"{provider_name.title()}Resource"  # github -> GithubResource
                elif provider_name == 'aws':
                    # AWS has service-specific resources (EC2Resource, IAMResource, etc.)
                    if model_name == 'EC2Resource':
                        full_model_name = "AWSEC2Resource"
                    elif model_name == 'IAMResource':
                        full_model_name = "AWSIAMResource"
                    elif model_name == 'S3Resource':
                        full_model_name = "AWSS3Resource"
                    elif model_name == 'CloudTrailResource':
                        full_model_name = "AWSCloudTrailResource"
                    elif model_name == 'CloudWatchResource':
                        full_model_name = "AWSCloudWatchResource"
                    else:
                        full_model_name = f"AWS{model_name}"
                else:
                    # Default naming for other providers
                    full_model_name = f"{provider_name.title()}{model_name}"
                
                model_class = create_resource_model_from_schema(full_model_name, model_config, provider_config, dynamic_models)
                dynamic_models[full_model_name] = model_class
                model_class.__provider__ = provider_name
                model_class.__service__ = model_config.get('service', '')
                model_class.__description__ = model_config.get('description', '')
            
            # Third pass: Create collection model
            if main_collection:
                full_model_name = f"{provider_name.upper()}ResourceCollection" if provider_name == 'aws' else f"{provider_name.title()}ResourceCollection"  # aws -> AWSResourceCollection
                
                # Handle resources field with dot notation references
                resources_field = main_collection.get('fields', {}).get('resources', [])
                
                if provider_name == 'github':
                    # GitHub has a single resource type
                    resource_model_name = "GithubResource"
                    if resource_model_name in dynamic_models:
                        resource_type = dynamic_models[resource_model_name]
                        model_class = create_collection_model_with_resource_type(
                            full_model_name, main_collection, resource_type, provider_config, dynamic_models
                        )
                    else:
                        model_class = create_resource_model_from_schema(full_model_name, main_collection, provider_config, dynamic_models)
                
                elif provider_name == 'aws':
                    # AWS has multiple resource types - create a collection that can handle all of them
                    aws_resource_types = []
                    for resource_ref in resources_field:
                        if isinstance(resource_ref, str) and 'aws.resources.' in resource_ref:
                            # Extract resource name from dot notation like "aws.resources.EC2Resource"
                            resource_name = resource_ref.split('.')[-1]  # Get "EC2Resource"
                            if resource_name == 'EC2Resource':
                                aws_model_name = "AWSEC2Resource"
                            elif resource_name == 'IAMResource':
                                aws_model_name = "AWSIAMResource"
                            elif resource_name == 'S3Resource':
                                aws_model_name = "AWSS3Resource"
                            elif resource_name == 'CloudTrailResource':
                                aws_model_name = "AWSCloudTrailResource"
                            elif resource_name == 'CloudWatchResource':
                                aws_model_name = "AWSCloudWatchResource"
                            else:
                                aws_model_name = f"AWS{resource_name}"
                            
                            if aws_model_name in dynamic_models:
                                aws_resource_types.append(dynamic_models[aws_model_name])
                    
                    # Create a multi-resource collection
                    model_class = create_multi_resource_collection_model(
                        full_model_name, main_collection, aws_resource_types, provider_config, dynamic_models
                    )
                
                else:
                    # Default handling for other providers
                    model_class = create_resource_model_from_schema(full_model_name, main_collection, provider_config, dynamic_models)
                
                dynamic_models[full_model_name] = model_class
                model_class.__provider__ = provider_name
                model_class.__description__ = main_collection.get('description', '')
        
        return dynamic_models
        
    except FileNotFoundError:
        print(f"Error: Resources YAML file not found at {yaml_file_path}")
        return {}
    except Exception as e:
        print(f"Error loading dynamic models: {e}")
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