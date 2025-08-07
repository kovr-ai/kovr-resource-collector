"""Service utilities for con_mon_v2."""
from typing import Type, Dict, List, Any
from pydantic import BaseModel
from con_mon_v2.resources import Resource, ResourceCollection
from con_mon_v2.resources.models import FieldType
from datetime import datetime


class CheckService(object):
    """Service for validating resource fields."""
    def __init__(
            self,
            check: Any,  # Using Any to avoid circular import
            connector_type: str,
    ):
        self.check = check
        self.connector_type = connector_type

    def _create_test_model(self, model_type: Type[BaseModel], depth: int = 0) -> dict:
        """Create a test model with all required fields."""
        if depth > 5:  # Prevent infinite recursion
            return {}
            
        test_resource = {}
        for field_name, field in model_type.model_fields.items():
            if field.is_required:
                if field.annotation == str:
                    test_resource[field_name] = f"test_{field_name}"
                elif field.annotation == int:
                    test_resource[field_name] = 1
                elif field.annotation == float:
                    test_resource[field_name] = 1.0
                elif field.annotation == bool:
                    test_resource[field_name] = True
                elif field.annotation == datetime:
                    test_resource[field_name] = datetime.now()
                elif field.annotation == FieldType:
                    test_resource[field_name] = FieldType.STRING
                elif hasattr(field.annotation, "__origin__"):
                    if field.annotation.__origin__ == list:
                        # Handle list type
                        if hasattr(field.annotation, "__args__"):
                            item_type = field.annotation.__args__[0]
                            if isinstance(item_type, type) and issubclass(item_type, BaseModel):
                                # List of models
                                item_resource = self._create_test_model(item_type, depth + 1)
                                
                                # Handle ResourceField specially
                                if item_type.__name__ == 'ResourceField':
                                    field_type = FieldType.STRING
                                    item_resource.update({
                                        'field_type': field_type,
                                        'value': self._get_test_value(field_type)
                                    })
                                
                                test_resource[field_name] = [item_type(**item_resource)]
                            else:
                                # List of simple types
                                test_resource[field_name] = []
                    elif field.annotation.__origin__ == dict:
                        # Handle dict type
                        test_resource[field_name] = {}
                elif isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
                    # Create nested model
                    nested_resource = self._create_test_model(field.annotation, depth + 1)
                    
                    # Handle ResourceField specially
                    if field.annotation.__name__ == 'ResourceField':
                        field_type = FieldType.STRING
                        nested_resource.update({
                            'field_type': field_type,
                            'value': self._get_test_value(field_type)
                        })
                    # Handle data models (they all have value field)
                    elif field.annotation.__name__.endswith('Data'):
                        nested_resource['value'] = {}
                    # Handle AWS models with numeric fields
                    elif field_name in ['threshold', 'period', 'evaluation_periods']:
                        nested_resource[field_name] = 1.0 if field_name == 'threshold' else 1
                    
                    test_resource[field_name] = field.annotation(**nested_resource)
        
        return test_resource

    def _get_test_value(self, field_type: FieldType) -> Any:
        """Get a test value for a field type."""
        if field_type == FieldType.STRING:
            return "test_value"
        elif field_type == FieldType.INTEGER:
            return 1
        elif field_type == FieldType.FLOAT:
            return 1.0
        elif field_type == FieldType.BOOLEAN:
            return True
        elif field_type == FieldType.DATETIME:
            return datetime.now()
        elif field_type == FieldType.LIST:
            return []
        elif field_type == FieldType.DICT:
            return {}
        elif field_type == FieldType.OBJECT:
            return {}
        else:
            return None

    def get_resource_collection(
            self,
            credentials: dict,
    ) -> ResourceCollection:
        """Get resources from a connector."""
        # For testing, return a dummy collection
        resource_type = self.check.resource_type
        test_resource = self._create_test_model(resource_type)
        
        return ResourceCollection(
            name="test",
            description="Test collection",
            source_connector="test",
            total_count=1,
            resources=[resource_type(**test_resource)]
        )

    @property
    def resource_type(self) -> Type[BaseModel]:
        """Get the resource type to check."""
        return self.check.resource_type

    @property
    def _all_resource_field_paths(self) -> list[str]:
        """Get all field paths in the resource type."""
        def get_field_paths(model: Type[BaseModel], prefix: str = "") -> list[str]:
            paths = []
            for field_name, field in model.model_fields.items():
                field_path = f"{prefix}.{field_name}" if prefix else field_name
                paths.append(field_path)

                # If field is another Pydantic model, recursively get its fields
                if isinstance(field.annotation, type) and issubclass(field.annotation, BaseModel):
                    paths.extend(get_field_paths(field.annotation, field_path))
                # Handle list/array of Pydantic models
                elif hasattr(field.annotation, "__origin__") and field.annotation.__origin__ == list:
                    if hasattr(field.annotation, "__args__") and issubclass(field.annotation.__args__[0], BaseModel):
                        paths.extend(get_field_paths(field.annotation.__args__[0], field_path))
            return paths

        return get_field_paths(self.resource_type)

    def _validate_field_path(
            self,
            field_path: str,
            resource: Resource,
    ) -> str:
        """Validate a field path exists in a resource."""
        try:
            # Split the field path into parts
            path_parts = field_path.split('.')
            current = resource

            # Traverse the resource object following the field path
            for part in path_parts:
                if not hasattr(current, part):
                    return "not found"
                current = getattr(current, part)

            # If we got here and the value exists, it's a success
            if current is not None:
                return "success"
            return "not found"  # Field exists but no data

        except Exception as e:
            return "error"  # Field path is invalid or caused an error

    def validate_resource_field_paths(
            self,
            resource_collection: ResourceCollection,
    ) -> dict[str, dict[str, str]]:
        """Validate all field paths in a resource collection."""
        validation_report: dict[str, dict[str, str]] = dict()
        for resource in resource_collection.resources:
            validation_report[self.resource_type.__name__] = dict()
            for field_path in self._all_resource_field_paths:
                validation_str = self._validate_field_path(field_path, resource)
                validation_report[self.resource_type.__name__][field_path] = validation_str
        return validation_report
