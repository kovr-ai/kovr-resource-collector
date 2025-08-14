"""
Models for resources module - represents individual data items and collections.
"""
import inspect
from typing import Any, Dict, List, Optional, Union, Type, get_origin, get_args
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo
from datetime import datetime


class InfoData(BaseModel):
    """
    Represents a single info data item that will be stored in connection.
    """
    source_connector: str


class Resource(BaseModel):
    """
    Represents a single resource item that checks will evaluate.
    This is the fundamental unit that connectors fetch and checks operate on.
    """
    id: str
    source_connector: str

    @classmethod
    def field_paths(cls, max_depth: int = 4) -> List[str]:
        """
        Dynamically generate field paths by analyzing this resource model.
        
        Args:
            max_depth: Maximum recursion depth for nested models
            
        Returns:
            List of field paths for this resource
        """
        try:
            # Generate field paths for this resource
            paths = cls._generate_paths_for_model(cls, max_depth=max_depth)
            
            # Add function-based paths
            function_paths = cls._generate_function_paths(paths)
            paths.extend(function_paths)
            
            return sorted(set(paths))
            
        except Exception as e:
            print(f"❌ Error generating field paths for {cls.__name__}: {e}")
            return []

    @classmethod
    def _generate_paths_for_model(cls, model_class: Type[BaseModel], prefix: str = "", max_depth: int = 4, current_depth: int = 0) -> List[str]:
        """
        Recursively generate field paths for a Pydantic model.
        
        Args:
            model_class: Pydantic model class to analyze
            prefix: Current path prefix
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            
        Returns:
            List of field paths
        """
        if current_depth >= max_depth:
            return []
        
        paths = []
        
        try:
            # Get model fields
            if hasattr(model_class, 'model_fields'):
                fields = model_class.model_fields
            elif hasattr(model_class, '__fields__'):
                fields = model_class.__fields__
            else:
                return []
            
            for field_name, field_info in fields.items():
                current_path = f"{prefix}.{field_name}" if prefix else field_name
                paths.append(current_path)
                
                # Get field type
                field_type = cls._get_field_type(field_info)
                
                # Handle different field types
                if cls._is_list_type(field_type):
                    # Handle list types
                    inner_type = cls._get_list_inner_type(field_type)
                    
                    # Add array access patterns
                    paths.extend([
                        f"{current_path}[*]",
                        f"{current_path}[]",
                        f"{current_path}.*"
                    ])
                    
                    # If inner type is a model, recurse into it with array patterns
                    if inner_type and cls._is_pydantic_model(inner_type):
                        inner_paths = cls._generate_paths_for_model(inner_type, "", max_depth, current_depth + 1)
                        for inner_path in inner_paths:
                            paths.extend([
                                f"{current_path}[*].{inner_path}",
                                f"{current_path}[].{inner_path}",
                                f"{current_path}.*.{inner_path}"
                            ])
                            
                elif cls._is_dict_type(field_type):
                    # Handle dict types - add some common patterns
                    paths.extend([
                        f"{current_path}.*",
                        f"{current_path}.key",
                        f"{current_path}.value"
                    ])
                    
                elif cls._is_pydantic_model(field_type):
                    # Recurse into nested models
                    nested_paths = cls._generate_paths_for_model(field_type, current_path, max_depth, current_depth + 1)
                    paths.extend(nested_paths)
                    
        except Exception as e:
            print(f"⚠️ Error analyzing model {model_class.__name__}: {e}")
        
        return paths

    @classmethod
    def _generate_function_paths(cls, base_paths: List[str]) -> List[str]:
        """
        Generate function-based field paths from base paths.
        
        Args:
            base_paths: List of base field paths
            
        Returns:
            List of function-based paths
        """
        function_paths = []
        
        # Functions to apply to array/list paths
        functions = ['len', 'any', 'all', 'count', 'sum', 'max', 'min']
        
        for path in base_paths:
            # Apply functions to paths that look like arrays
            if any(pattern in path for pattern in ['[*]', '[]', '.*']):
                for func in functions:
                    function_paths.append(f"{func}({path})")
            
            # Apply len function to any path that might be a collection
            if not any(pattern in path for pattern in ['[*]', '[]', '.*']):
                # Add len function for potential collections
                function_paths.append(f"len({path})")
        
        return function_paths

    @classmethod
    def _get_field_type(cls, field_info) -> Type:
        """Get the actual type from a field info object."""
        if hasattr(field_info, 'annotation'):
            field_type = field_info.annotation
        elif hasattr(field_info, 'type_'):
            field_type = field_info.type_
        elif isinstance(field_info, FieldInfo):
            field_type = field_info.annotation if hasattr(field_info, 'annotation') else Any
        else:
            field_type = Any
        
        # Handle Optional types (Union[T, None])
        if cls._is_optional_type(field_type):
            # Get the non-None type from Optional[T]
            field_type = cls._get_optional_inner_type(field_type)
        
        return field_type

    @classmethod
    def _is_list_type(cls, field_type: Type) -> bool:
        """Check if a type is a List type."""
        origin = get_origin(field_type)
        return origin is list or origin is List

    @classmethod
    def _is_dict_type(cls, field_type: Type) -> bool:
        """Check if a type is a Dict type."""
        origin = get_origin(field_type)
        return origin is dict or origin is Dict

    @classmethod
    def _get_list_inner_type(cls, field_type: Type) -> Type:
        """Get the inner type of a List type."""
        args = get_args(field_type)
        return args[0] if args else Any

    @classmethod
    def _is_optional_type(cls, field_type: Type) -> bool:
        """Check if a type is Optional (Union[T, None])."""
        origin = get_origin(field_type)
        if origin is Union:
            args = get_args(field_type)
            # Optional[T] is Union[T, None]
            return len(args) == 2 and type(None) in args
        return False

    @classmethod
    def _get_optional_inner_type(cls, field_type: Type) -> Type:
        """Get the non-None type from Optional[T]."""
        args = get_args(field_type)
        for arg in args:
            if arg is not type(None):
                return arg
        return Any

    @classmethod
    def _is_pydantic_model(cls, field_type: Type) -> bool:
        """Check if a type is a Pydantic model."""
        try:
            return (inspect.isclass(field_type) and 
                    issubclass(field_type, BaseModel) and
                    field_type != BaseModel)
        except (TypeError, AttributeError):
            return False


class ResourceCollection(BaseModel):
    """
    Represents a collection of resources, typically the result of a connector's fetch operation.
    """
    resources: List[Resource]
    source_connector: str
    total_count: int
    fetched_at: datetime = Field(default_factory=datetime.now)
    
    def __len__(self) -> int:
        """Return the number of resources in the collection."""
        return len(self.resources)
    
    def __iter__(self):
        """Make the collection iterable."""
        return iter(self.resources)
    
    def __getitem__(self, index: Union[int, slice]) -> Union[Resource, List[Resource]]:
        """Allow indexing and slicing of the collection."""
        return self.resources[index]

    def get_by_id(self, resource_id: str) -> Optional[Resource]:
        """Get a resource by its ID."""
        for resource in self.resources:
            if resource.id == resource_id:
                return resource
        return None

    @property
    def resource_models(self):
        return list(set([resource.__class__ for resource in self.resources]))
