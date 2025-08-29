"""
Check model - 1:1 mapping with database schema including JSONB nested fields.
"""

import re
from enum import Enum
from typing import Optional, ClassVar, List, Any, Type, Callable
from datetime import datetime
from pydantic import Field, BaseModel as PydanticBaseModel

from .base import TableModel
from con_mon.resources import Resource


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

    def __call__(self, fetched_value: Any, config_value: Any) -> bool | None:
        response = self.function(fetched_value, config_value)
        if response not in [True, False, None]:
            return None
        return response

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
            return lambda fetched_value, config_value: config_value in fetched_value if hasattr(fetched_value,
                                                                                                '__contains__') else False
        elif name == ComparisonOperationEnum.NOT_CONTAINS:
            return lambda fetched_value, config_value: config_value not in fetched_value if hasattr(fetched_value,
                                                                                                    '__contains__') else True
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

        Raises:
            ValueError: If logic is empty or contains only whitespace/comments
        """
        # Validate that logic is not empty
        if not logic or not logic.strip():
            raise ValueError("Custom logic cannot be empty")

        # Check if logic contains only comments and whitespace
        logic_lines = [line.strip() for line in logic.split('\n') if line.strip()]
        if not logic_lines or all(line.startswith('#') for line in logic_lines):
            raise ValueError("Custom logic cannot contain only comments and whitespace")

        indented_logic = '\n'.join('            ' + line for line in logic.split('\n'))

        get_function_code = f"""
def get_function():
    def {name.value}(fetched_value, config_value):
        result = False
        try:
{indented_logic}
        except Exception as e:
            # Log the error if needed (for debugging)
            # Return None to indicate execution failure (vs False for logic failure)
            result = None
            raise e
        return result
    return {name.value}
function = get_function()
        """
        local_ns = {
            'function': lambda f, c: False,
        }
        safe_globals = {
            '__builtins__': {
                're': re,
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
                'NameError': NameError,
                'TypeError': TypeError,
                'ValueError': ValueError,
                'AttributeError': AttributeError,
                'KeyError': KeyError,
                'IndexError': IndexError,
                'ZeroDivisionError': ZeroDivisionError,
            }
        }
        exec(get_function_code, safe_globals, local_ns)
        return local_ns['function']


class CheckOperation(PydanticBaseModel):
    """
    Nested model for check operation within metadata JSONB field.
    """
    name: ComparisonOperationEnum = Field(..., description="Operation name (e.g., 'custom', 'equals')")
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
        "resource_type": "con_mon.mappings.github.GithubResource",
        "expected_value": null
    }
    """
    tags: Optional[List[str]] = Field(None, description="Tags array")
    category: Optional[str] = Field(None, description="Check category")
    severity: Optional[str] = Field(None, description="Severity level")
    operation: CheckOperation = Field(..., description="Operation configuration")
    field_path: str = Field(..., description="Resource field path")
    resource_type: str = Field(None, description="Resource type class path")
    expected_value: Any = Field(None, description="Expected value for comparison")


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
    failure: str = Field(..., description="Failure message")
    partial: str = Field(..., description="Partial success message")
    success: str = Field(..., description="Success message")


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
    description: str = Field(..., description="Fix description")
    instructions: List[str] = Field(..., description="Step-by-step instructions")
    estimated_time: Optional[str] = Field("1-2 weeks",
                                          description="Estimated time for fix in format W weeks D days H hours")
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

    # Field Extraction Functions

    @classmethod
    def _extract_field_value(cls, resource: Resource, field_path: str) -> Any:
        """Extract value from nested dictionary using dot notation, with support for functions and array operations."""

        # Check if field_path contains a function call
        function_patterns = [
            ('len(', ')'),
            ('any(', ')'),
            ('all(', ')'),
            ('count(', ')'),
            ('sum(', ')'),
            ('max(', ')'),
            ('min(', ')')
        ]

        for func_start, func_end in function_patterns:
            if field_path.startswith(func_start) and field_path.endswith(func_end):
                # Extract the inner field path from function(field.path)
                inner_field_path = field_path[len(func_start):-len(func_end)]

                # Extract the value using the inner field path
                inner_value = cls._extract_nested_value(resource, inner_field_path)

                # Apply the appropriate function
                function_name = func_start[:-1]  # Remove the '('
                return cls._apply_function(function_name, inner_value)

        # Regular field path extraction (including wildcard support)
        return cls._extract_nested_value(resource, field_path)

    @classmethod
    def _apply_function(cls, function_name: str, value: Any) -> Any:
        """Apply built-in functions to extracted values."""
        try:
            if function_name == 'len':
                return len(value) if hasattr(value, '__len__') else 0

            elif function_name == 'any':
                if isinstance(value, (list, tuple)):
                    return any(bool(item) for item in value)
                return bool(value)

            elif function_name == 'all':
                if isinstance(value, (list, tuple)):
                    return all(bool(item) for item in value)
                return bool(value)

            elif function_name == 'count':
                if isinstance(value, (list, tuple)):
                    return sum(1 for item in value if bool(item))
                return 1 if bool(value) else 0

            elif function_name == 'sum':
                if isinstance(value, (list, tuple)):
                    # Only sum numeric values
                    numeric_values = [item for item in value if isinstance(item, (int, float))]
                    return sum(numeric_values)
                return value if isinstance(value, (int, float)) else 0

            elif function_name == 'max':
                if isinstance(value, (list, tuple)) and value:
                    # Only get max of numeric values
                    numeric_values = [item for item in value if isinstance(item, (int, float))]
                    return max(numeric_values) if numeric_values else 0
                return value if isinstance(value, (int, float)) else 0

            elif function_name == 'min':
                if isinstance(value, (list, tuple)) and value:
                    # Only get min of numeric values
                    numeric_values = [item for item in value if isinstance(item, (int, float))]
                    return min(numeric_values) if numeric_values else 0
                return value if isinstance(value, (int, float)) else 0

            else:
                raise ValueError(f"Unsupported function: {function_name}")

        except (TypeError, ValueError, AttributeError):
            # Return safe defaults on error
            if function_name in ['len', 'count', 'sum']:
                return 0
            elif function_name in ['any', 'all']:
                return False
            elif function_name in ['max', 'min']:
                return 0
            else:
                return None

    @classmethod
    def _extract_nested_value(cls, resource: Resource, field_path: str) -> Any:
        """Extract value from nested object using dot notation with wildcard array support."""

        # Check if the field path contains any wildcard array access patterns
        if (('.*.' in field_path or field_path.endswith('.*')) or
                ('[*]' in field_path) or
                ('[]' in field_path)):
            return cls._extract_array_values(resource, field_path)

        # Regular dot notation extraction
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

    @classmethod
    def _extract_array_values(cls, resource: Resource, field_path: str) -> List[Any]:
        """
        Extract values from arrays using various wildcard syntaxes:
        - 'branches.*.protection_details' (dot-star)
        - 'branches[*].protection_details' (bracket-star)
        - 'branches[].protection_details' (empty brackets)
        - 'webhooks[*].events[*]' (nested patterns)
        """

        # Normalize the field path to handle different bracket patterns
        normalized_path = cls._normalize_wildcard_path(field_path)

        # Split path into segments that may contain wildcards
        segments = cls._parse_path_segments(normalized_path)

        # Process the path recursively to handle nested wildcards
        return cls._extract_recursive_array_values(resource, segments)

    @classmethod
    def _normalize_wildcard_path(cls, field_path: str) -> str:
        """
        Normalize different wildcard syntaxes to a consistent format.
        Converts [*] and [] patterns to .* for consistent processing.
        """
        import re

        # Convert [*] to .*
        normalized = re.sub(r'\[\*\]', '.*', field_path)

        # Convert [] to .*
        normalized = re.sub(r'\[\]', '.*', normalized)

        return normalized

    @classmethod
    def _parse_path_segments(cls, field_path: str) -> List[dict]:
        """
        Parse field path into segments that identify arrays and field access.
        Returns list of segments with metadata about wildcards.
        """
        segments = []
        parts = field_path.split('.')

        i = 0
        while i < len(parts):
            part = parts[i]

            if part == '*':
                # This is a wildcard - the previous segment should be marked as an array
                if segments:
                    segments[-1]['is_array'] = True
                    segments[-1]['wildcard_type'] = 'star'

                # Add remaining path as the field to extract from each array element
                remaining_parts = parts[i + 1:]
                if remaining_parts:
                    segments.append({
                        'path': '.'.join(remaining_parts),
                        'is_array': False,
                        'is_remaining_path': True
                    })
                break
            else:
                segments.append({
                    'field': part,
                    'is_array': False,
                    'wildcard_type': None,
                    'is_remaining_path': False
                })

            i += 1

        return segments

    @classmethod
    def _extract_recursive_array_values(cls, resource: Resource, segments: List[dict]) -> List[Any]:
        """
        Recursively extract values following the parsed segments.
        Handles nested wildcards and complex path structures.
        """
        if not segments:
            return [resource] if resource is not None else []

        current_segment = segments[0]
        remaining_segments = segments[1:]

        # Handle remaining path segment (everything after a wildcard)
        if current_segment.get('is_remaining_path'):
            remaining_path = current_segment['path']
            if remaining_path:
                # Check if the remaining path has more wildcards
                if (('.*.' in remaining_path or remaining_path.endswith('.*')) or
                        ('[*]' in remaining_path) or
                        ('[]' in remaining_path)):
                    # Recursively handle nested wildcards
                    return cls._extract_array_values(resource, remaining_path)
                else:
                    # Simple field extraction
                    try:
                        return [cls._extract_nested_value(resource, remaining_path)]
                    except (AttributeError, TypeError):
                        return []
            else:
                return [resource] if resource is not None else []

        # Navigate to the field
        field_name = current_segment['field']
        try:
            if hasattr(resource, field_name):
                field_value = getattr(resource, field_name)
            elif isinstance(resource, dict) and field_name in resource:
                field_value = resource[field_name]
            else:
                raise AttributeError(f"Field '{field_name}' not found")
        except (AttributeError, TypeError):
            return []

        # If this segment is an array, extract from each element
        if current_segment.get('is_array'):
            if not isinstance(field_value, (list, tuple)):
                # If it's not an array but marked as one, treat as single item
                field_value = [field_value] if field_value is not None else []

            results = []
            for item in field_value:
                if remaining_segments:
                    # Continue processing with remaining segments
                    sub_results = cls._extract_recursive_array_values(item, remaining_segments)
                    results.extend(sub_results)
                else:
                    # No more segments, return the item itself
                    if item is not None:
                        results.append(item)

            return results
        else:
            # Not an array, continue with next segment
            if remaining_segments:
                return cls._extract_recursive_array_values(field_value, remaining_segments)
            else:
                return [field_value] if field_value is not None else []

    @property
    def resource_model(self) -> Type[Resource]:
        """Get the resource type from metadata."""
        if not self.metadata.resource_type:
            raise ValueError("Resource type not specified in metadata")

        # Handle string resource type paths like "con_mon.mappings.github.GithubResource"
        resource_type_str = self.metadata.resource_type

        try:
            # Split the module path and class name
            module_parts = resource_type_str.split('.')
            class_name = module_parts[-1]
            module_path = '.'.join(module_parts[:-1])

            # Import the module dynamically (resource_type_str already contains full path)
            import importlib
            module = importlib.import_module(module_path.replace('_v2', ''))

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

    def is_invalid(self, check_results: List['CheckResult']) -> bool:
        """
        Validate based on any errors in check results if check should be used in production.
        Return True if check is invalid and should be regenerated.

        A check is considered invalid if:
        1. No results available (can't evaluate)
        2. All results have passed=None (evaluation errors/exceptions)
        3. There are critical errors that prevent proper evaluation

        A check is considered VALID (should not be regenerated) if:
        1. At least one result has passed=True or passed=False (successful evaluation)
        2. The check logic executed properly, even if it failed compliance

        Args:
            check_results: List of CheckResult objects from evaluating the check

        Returns:
            bool: True if check is invalid and should be regenerated, False if acceptable
        """
        print(f"🔍 check_is_invalid called with {len(check_results) if check_results else 0} results")
        print(f"🔍 Check name: {self.name}")
        print(f"🔍 Check field_path: {self.field_path}")
        print(f"🔍 Check resource_model: {self.resource_model}")
        print(f"🔍 Check operation: {self.metadata.operation.name}")
        if self.metadata.operation.logic:
            print(f"🔍 Check logic:")
            # Print logic with line numbers for better debugging
            logic_lines = self.metadata.operation.logic.split('\n')
            for i, line in enumerate(logic_lines, 1):
                print(f"    {i:2d}: {line}")
        else:
            print(f"🔍 Check logic: None (standard operation)")

        if not check_results:
            print("❌ No check results - considering invalid")
            return True

        print(f"🔍 Original results count: {len(check_results)}")

        # Filter results by resource model
        original_count = len(check_results)
        check_results = [
            check_result
            for check_result in check_results
            if check_result.resource_model == self.resource_model
        ]
        filtered_count = len(check_results)

        print(f"🔍 After filtering by resource_model: {filtered_count} results (was {original_count})")

        if not check_results:
            print("🟡 No results after resource model filtering - considering valid (no applicable resources)")
            return False

        # Debug: Print all results
        print(f"🔍 Analyzing {len(check_results)} check results:")
        for i, result in enumerate(check_results):
            print(f"   Result {i + 1}: passed={result.passed}, error={result.error}")
            if result.error:
                print(f"      Error details: {result.error}")
            print(f"      Message: {result.message}")

        # Count results with actual boolean values (successful evaluations)
        successful_evaluations = 0
        error_evaluations = 0

        for check_result in check_results:
            if check_result.passed is not None:  # Either True or False
                successful_evaluations += 1
                print(f"   ✅ Successful evaluation: passed={check_result.passed}")
            else:
                error_evaluations += 1
                print(f"   ❌ Error evaluation: {check_result.error}")

        print(f"🔍 Summary: {successful_evaluations} successful, {error_evaluations} errors")

        # Check is VALID if we have at least some successful evaluations
        # Even if all evaluations failed (passed=False), the check logic worked
        if successful_evaluations > 0:
            print(f"✅ Check is VALID - has {successful_evaluations} successful evaluations")
            return False

        # Check is INVALID if all evaluations failed with errors
        print(f"❌ Check is INVALID - all {error_evaluations} evaluations had errors")
        return True

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
                fetched_value = self._extract_field_value(resource, self.field_path)
            except Exception as field_error:
                # Field extraction failed - create failed result with error details
                check_result = CheckResult(
                    passed=None,
                    check=self,
                    resource=resource,
                    message=f"Check '{self.name}' failed due to missing field",
                    error=f"Field extraction failed: {str(field_error)}. Field path: {self.field_path} not found in resource {resource.id}"
                )
                check_results.append(check_result)
                continue

            try:
                # Try to compare values - may fail due to type mismatch or other issues
                passed = self.comparison_operation(fetched_value, self.expected_value)
                check_result = CheckResult(
                    passed=passed,
                    check=self,
                    resource=resource,
                    message=f"Check '{self.name}' {'passed' if passed else 'failed'}. Expected: {self.expected_value}, Fetched: {fetched_value}"
                )
            except Exception as compare_error:
                # Comparison failed - create failed result with error details
                check_result = CheckResult(
                    passed=None,
                    check=self,
                    resource=resource,
                    message=f"Check '{self.name}' failed due to comparison error",
                    error=f"Comparison failed: {str(compare_error)}. Field path: {self.field_path}, Expected: {self.expected_value}, Fetched: {fetched_value}"
                )

            check_results.append(check_result)
        return check_results

    def result_summary(
            self,
            check_results: List['CheckResult']
    ) -> str:
        status_count_map = {
            True: 0,
            False: 0,
            None: 0,
        }
        for cr in check_results:
            if cr.check != self:
                raise ValueError(f'Passed check_result {cr} is not valid for {self}')
            status_count_map[cr.passed] += 1
        if len(check_results) == status_count_map[None]:
            return 'check execution failed'
        if len(check_results) == status_count_map[True]:
            return self.output_statements.success
        if len(check_results) == status_count_map[False]:
            return self.output_statements.failure
        return self.output_statements.partial


class CheckResult(PydanticBaseModel):
    """Result of a check evaluation."""
    passed: bool | None
    check: Check
    resource: Resource
    message: Optional[str] = None
    error: Optional[str] = None

    @property
    def resource_model(self) -> Type[Resource]:
        return self.resource.__class__
