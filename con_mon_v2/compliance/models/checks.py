"""
Check model - 1:1 mapping with database schema including JSONB nested fields.
"""

from enum import Enum
from typing import Optional, ClassVar, List, Any, Type, Callable
from datetime import datetime
from pydantic import Field, BaseModel as PydanticBaseModel

from .base import TableModel
from con_mon_v2.resources import Resource


class ComparisonOperationEnum(Enum):
    """Supported comparison operations for checks."""
    EQUAL = "=="
    NOT_EQUAL = "!="
    LESS_THAN = "<"
    GREATER_THAN = ">"
    LESS_THAN_OR_EQUAL = "<="
    GREATER_THAN_OR_EQUAL = ">="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    CUSTOM = "custom"


class ComparisonOperation(PydanticBaseModel):
    """
    Represents a comparison operation that can be performed between fetched and config values.
    """
    name: ComparisonOperationEnum
    function: Callable[[Any, Any], bool] = Field(..., exclude=True)

    class Config:
        arbitrary_types_allowed = True

    def __call__(self, fetched_value: Any, config_value: Any):
        return self.function(fetched_value, config_value)

    @classmethod
    def get_function(
        cls,
        name: ComparisonOperationEnum,
        logic: str | None = None
    ) -> Callable[[Any, Any], bool]:
        """
        Return function which matches comparison operation.

        Args:
            name: Name for standard operation function.
            logic: Optional Custom logic in case of custom for comparison.

        Returns:
            bool: True if comparison passes, False otherwise
        """
        if name == ComparisonOperationEnum.EQUAL:
            return lambda fetched_value, config_value: fetched_value == config_value
        elif name == ComparisonOperationEnum.NOT_EQUAL:
            return lambda fetched_value, config_value: fetched_value != config_value
        elif name == ComparisonOperationEnum.LESS_THAN:
            return lambda fetched_value, config_value: fetched_value < config_value
        elif name == ComparisonOperationEnum.GREATER_THAN:
            return lambda fetched_value, config_value: fetched_value > config_value
        elif name == ComparisonOperationEnum.LESS_THAN_OR_EQUAL:
            return lambda fetched_value, config_value: fetched_value <= config_value
        elif name == ComparisonOperationEnum.GREATER_THAN_OR_EQUAL:
            return lambda fetched_value, config_value: fetched_value >= config_value
        elif name == ComparisonOperationEnum.CONTAINS:
            return lambda fetched_value, config_value: config_value in fetched_value if hasattr(fetched_value, '__contains__') else False
        elif name == ComparisonOperationEnum.NOT_CONTAINS:
            return lambda fetched_value, config_value: config_value not in fetched_value if hasattr(fetched_value, '__contains__') else True
        elif name == ComparisonOperationEnum.CUSTOM:
            return cls.get_custom_function(name, logic)
        else:
            raise ValueError(f"Unsupported operation: {name}")

    @classmethod
    def get_custom_function(
        cls,
        name: ComparisonOperationEnum,
        logic: str
    ) -> Callable[[Any, Any], bool]:
        """
        Return function using the logic for comparison in logic.

        Args:
            name: Name for custom logic function.
            logic: Custom logic for comparison.

        Returns:
            bool: True if comparison passes, False otherwise
        """
        indented_logic = '\n'.join('        ' + line for line in logic.split('\n'))
        get_function_code = f"""
def get_function():
    def {name.value}(fetched_value, config_value):
        result = False
{indented_logic}
        return result
    return {name.value}
function = get_function()
        """
        local_ns = {
            'function': lambda f, c: False
        }
        safe_globals = {
            '__builtins__': {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'set': set,
                'tuple': tuple,
                'any': any,
                'all': all,
                'max': max,
                'min': min,
                'sum': sum,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
                'range': range,
                'isinstance': isinstance,
                'hasattr': hasattr,
                'getattr': getattr,
                'abs': abs,
                'round': round,
                'Exception': Exception,
            }
        }
        exec(get_function_code, safe_globals, local_ns)
        return local_ns['function']


class CheckOperation(PydanticBaseModel):
    """
    Nested model for check operation within metadata JSONB field.
    """
    name: str = Field(..., description="Operation name (e.g., 'custom', 'equals')")
    logic: Optional[str] = Field(None, description="Custom logic code for operation")


class CheckMetadata(PydanticBaseModel):
    """
    Nested model for metadata JSONB field.
    
    Represents the full nested structure:
    {
        "tags": ["compliance", "nist"],
        "category": "configuration", 
        "severity": "medium",
        "operation": {"name": "custom", "logic": "..."},
        "field_path": "repository_data.basic_info.description",
        "connection_id": 1,
        "resource_type": "con_mon_v2.mappings.github.GithubResource",
        "expected_value": null
    }
    """
    tags: Optional[List[str]] = Field(None, description="Tags array")
    category: Optional[str] = Field(None, description="Check category")
    severity: Optional[str] = Field(None, description="Severity level")
    operation: CheckOperation = Field(..., description="Operation configuration")
    field_path: str = Field(..., description="Resource field path")
    connection_id: Optional[int] = Field(None, description="Connection ID")
    resource_type: Optional[str] = Field(None, description="Resource type class path")
    expected_value: Optional[Any] = Field(None, description="Expected value for comparison")


class OutputStatements(PydanticBaseModel):
    """
    Nested model for output_statements JSONB field.
    
    Represents the nested structure:
    {
        "failure": "Check failed: ...",
        "partial": "Check partially passed",
        "success": "Check passed: ..."
    }
    """
    failure: Optional[str] = Field(None, description="Failure message")
    partial: Optional[str] = Field(None, description="Partial success message")
    success: Optional[str] = Field(None, description="Success message")


class FixDetails(PydanticBaseModel):
    """
    Nested model for fix_details JSONB field.
    
    Represents the nested structure:
    {
        "description": "Update the repository description...",
        "instructions": ["Go to settings", "Edit description"],
        "estimated_date": "2023-06-30",
        "automation_available": false
    }
    """
    description: Optional[str] = Field(None, description="Fix description")
    instructions: Optional[List[str]] = Field(None, description="Step-by-step instructions")
    estimated_date: Optional[str] = Field(None, description="Estimated completion date")
    automation_available: bool = Field(False, description="Whether automation is available")


class Check(TableModel):
    """
    Check model matching database schema exactly.
    
    Database table: checks
    Fields: id, name, description, output_statements (JSONB), fix_details (JSONB),
            created_by, category, metadata (JSONB), updated_by, created_at, 
            updated_at, is_deleted
    """
    
    # Table configuration
    table_name: ClassVar[str] = "checks"
    
    # Database fields (exact 1:1 mapping)
    id: str = Field(..., description="Check ID (string primary key)")
    name: str = Field(..., description="Check name")
    description: str = Field(..., description="Check description")
    
    # JSONB fields with full nested structure
    output_statements: OutputStatements = Field(..., description="Output statements JSONB field")
    fix_details: FixDetails = Field(..., description="Fix details JSONB field") 
    metadata: CheckMetadata = Field(..., description="Metadata JSONB field")
    
    # Regular fields
    created_by: str = Field(..., description="User who created the check")
    category: str = Field(..., description="Check category")
    updated_by: str = Field(..., description="User who last updated the check")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    is_deleted: bool = Field(False, description="Soft delete flag")

    @property
    def resource_model(self) -> Type[Resource]:
        """Get the resource type from metadata."""
        if not self.metadata.resource_type:
            raise ValueError("Resource type not specified in metadata")
        
        # Handle string resource type paths like "con_mon_v2.mappings.github.GithubResource"
        resource_type_str = self.metadata.resource_type
        
        try:
            # Split the module path and class name
            module_parts = resource_type_str.split('.')
            class_name = module_parts[-1]
            module_path = '.'.join(module_parts[:-1])
            
            # Import the module dynamically
            import importlib
            module = importlib.import_module(module_path)
            
            # Get the class from the module
            resource_class = getattr(module, class_name)
            
            # Verify it's a Resource subclass
            if not issubclass(resource_class, Resource):
                raise ValueError(f"Class {class_name} is not a Resource subclass")
            
            return resource_class
            
        except (ImportError, AttributeError, ValueError) as e:
            raise ValueError(f"Could not resolve resource type '{resource_type_str}': {e}")

    @property
    def comparison_operation(self) -> ComparisonOperation:
        """Get Comparison Operation Model generated from metadata."""
        if not self.metadata.operation:
            raise ValueError("Operation not specified in metadata")
        
        operation_data = self.metadata.operation
        operation_enum = ComparisonOperationEnum(operation_data.name)
        
        # Get the appropriate function based on operation name and logic
        if operation_enum == ComparisonOperationEnum.CUSTOM:
            if not operation_data.logic:
                raise ValueError("Logic not specified in metadata")
            # For custom operations, use the custom logic
            function = ComparisonOperation.get_custom_function(
                operation_enum,
                operation_data.logic
            )
        else:
            # For standard operations, get the standard function
            function = ComparisonOperation.get_function(
                operation_enum
            )

        # Create and return the ComparisonOperation instance
        return ComparisonOperation(
            name=operation_enum,
            function=function
        )

    @property
    def expected_value(self) -> Any:
        """Get the expected value from metadata."""
        return self.metadata.expected_value

    @property
    def field_path(self) -> str:
        """Get the field_path to fetch value from metadata."""
        return self.metadata.field_path

    def evaluate(self, resources: List[Resource]) -> List["CheckResult"]:
        """
        Evaluate this check against a resource's data.

        Args:
            resources: List containing the resources to evaluate

        Returns:
            List[CheckResult]: The results of the check evaluation for each relevant resource
        """
        # Filter resources by resource_type if specified
        resources_to_check = []
        for resource in resources:
            # Check if the resource is an instance of the specified type
            if isinstance(resource, self.resource_model):
                resources_to_check.append(resource)

        check_results = []
        for resource in resources_to_check:
            try:
                # Try to extract field value - may fail if field is missing
                actual_value = self._extract_field_value(resource, self.field_path)
            except Exception as field_error:
                # Field extraction failed - create failed result with error details
                check_result = CheckResult(
                    passed=False,
                    check=self,
                    resource=resource,
                    message=f"Check '{self.name}' failed due to missing field",
                    error=f"Field extraction failed: {str(field_error)}. Field path: {self.field_path} not found in resource {resource.id}"
                )
                check_results.append(check_result)
                continue

            try:
                # Try to compare values - may fail due to type mismatch or other issues
                passed = self.comparison_operation(actual_value, self.expected_value)
                check_result = CheckResult(
                    passed=passed,
                    check=self,
                    resource=resource,
                    message=f"Check '{self.name}' {'passed' if passed else 'failed'}. Expected: {self.expected_value}, Actual: {actual_value}"
                )
            except Exception as compare_error:
                # Comparison failed - create failed result with error details
                check_result = CheckResult(
                    passed=False,
                    check=self,
                    resource=resource,
                    message=f"Check '{self.name}' failed due to comparison error",
                    error=f"Comparison failed: {str(compare_error)}. Field path: {self.field_path}, Expected: {self.expected_value}, Actual: {actual_value}"
                )

            check_results.append(check_result)
        return check_results

    def _extract_field_value(self, resource: Resource, field_path: str) -> Any:
        """Extract value from nested dictionary using dot notation, with support for functions like len()."""

        # Check if field_path contains a function call like len()
        if field_path.startswith('len(') and field_path.endswith(')'):
            # Extract the inner field path from len(field.path)
            inner_field_path = field_path[4:-1]  # Remove 'len(' and ')'

            # Extract the value using the inner field path
            inner_value = self._extract_nested_value(resource, inner_field_path)

            # Apply len() function
            try:
                return len(inner_value) if hasattr(inner_value, '__len__') else 0
            except TypeError:
                return 0
        else:
            # Regular field path extraction
            return self._extract_nested_value(resource, field_path)

    def _extract_nested_value(self, resource: Resource, field_path: str) -> Any:
        """Extract value from nested object using dot notation."""
        keys = field_path.split('.')
        value = resource
        for key in keys:
            if hasattr(value, key):
                value = getattr(value, key)
            elif isinstance(value, dict) and key in value:
                value = value[key]
            else:
                raise AttributeError(f"Field '{key}' not found in path '{field_path}'")
        return value


class CheckResult(PydanticBaseModel):
    """Result of a check evaluation."""
    passed: bool
    check: Check
    resource: Resource
    message: Optional[str] = None
    error: Optional[str] = None
