"""
Models for checks module - handles resource validation and evaluation.
"""
from enum import Enum
from datetime import datetime
from typing import Any, Callable, Optional, List, Type, Dict
from pydantic import BaseModel, Field
from con_mon_v2.resources.models import Resource


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


class ComparisonOperation(BaseModel):
    """
    Represents a comparison operation that can be performed between fetched and config values.
    """
    name: ComparisonOperationEnum
    custom_function: Optional[Callable[[Any, Any], bool]] = Field(default=None, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True
    
    def compare(self, fetched_value: Any, config_value: Any) -> bool:
        """
        Perform the comparison between fetched value and config value.
        
        Args:
            fetched_value: The value retrieved from the resource
            config_value: The configured expected value
            
        Returns:
            bool: True if comparison passes, False otherwise
        """
        if self.name == ComparisonOperationEnum.EQUAL:
            return fetched_value == config_value
        elif self.name == ComparisonOperationEnum.NOT_EQUAL:
            return fetched_value != config_value
        elif self.name == ComparisonOperationEnum.LESS_THAN:
            return fetched_value < config_value
        elif self.name == ComparisonOperationEnum.GREATER_THAN:
            return fetched_value > config_value
        elif self.name == ComparisonOperationEnum.LESS_THAN_OR_EQUAL:
            return fetched_value <= config_value
        elif self.name == ComparisonOperationEnum.GREATER_THAN_OR_EQUAL:
            return fetched_value >= config_value
        elif self.name == ComparisonOperationEnum.CONTAINS:
            return config_value in fetched_value if hasattr(fetched_value, '__contains__') else False
        elif self.name == ComparisonOperationEnum.NOT_CONTAINS:
            return config_value not in fetched_value if hasattr(fetched_value, '__contains__') else True
        elif self.name == ComparisonOperationEnum.CUSTOM:
            if self.custom_function:
                return self.custom_function(fetched_value, config_value)
            else:
                raise ValueError("Custom operation requires a custom_function")
        else:
            raise ValueError(f"Unsupported operation: {self.name}")


class CheckMetadata(BaseModel):
    # Additional metadata fields from YAML
    tags: Optional[List[str]] = None
    severity: Optional[str] = None
    category: Optional[str] = None

    # Evaluation Metadata in DB
    field_path: str
    expected_value: Any = None
    operation: Optional[str] = None
    name: Optional[str] = None
    logic: Optional[str] = None



class CheckResultStatement(BaseModel):
    success: str
    failure: str
    partial: str


class CheckFailureFix(BaseModel):
    description: str
    instructions: List[str]
    estimated_date: str
    automation_available: bool = False


class Check(BaseModel):
    """
    Represents a single check that evaluates a resource field against a configured value.
    """
    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None

    # Database-specific fields (these are completely new)
    output_statements: CheckResultStatement = Field(
        default_factory=dict,
        description="JSONB field containing output configuration"
    )
    fix_details: CheckFailureFix = Field(
        default_factory=dict,
        description="JSONB field containing fix/remediation details"
    )
    created_by: str = Field(
        'system',
        description="User who created the check"
    )
    updated_by: str = Field(
        'system',
        description="User who last updated the check"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Last update timestamp"
    )
    is_deleted: bool = Field(
        default=False,
        description="Soft delete flag"
    )
    metadata: CheckMetadata = Field(
        default_factory=dict,
        description="Additional metadata and execution parameters"
    )

    # NIST compliance fields - updated to use IDs from CSV for better performance
    # control_ids: List[int]    # Reference to control ID from CSV
    # framework_id: int  # Reference to framework ID from CSV
    # control_id: int    # Reference to control ID from CSV
    # framework_name: str  # Reference to framework name from CSV
    # control_name: str    # Reference to control name from CSV

    @property
    def operation(self) -> ComparisonOperation:
        # TODO: implement
        return None

    @property
    def resource_type(self) -> Type[BaseModel]:
        # TODO: implement
        return None

    def evaluate(self, resources: List[Resource]) -> List["CheckResult"]:
        """
        Evaluate this check against a resource's data.
        
        Args:
            resources: List containing the resources to evaluate
            
        Returns:
            List[CheckResult]: The results of the check evaluation for each relevant resource
        """
        # Filter resources by resource_type if specified
        if self.resource_type:
            filtered_resources = []
            for resource in resources:
                # Check if the resource is an instance of the specified type
                if isinstance(resource, self.resource_type):
                    filtered_resources.append(resource)
            resources_to_check = filtered_resources
        else:
            # No filtering - use all resources
            resources_to_check = resources
        
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
                passed = self.operation.compare(actual_value, self.expected_value)
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


class CheckResult(BaseModel):
    """Result of a check evaluation."""
    passed: bool
    check: Check
    resource: Resource
    message: Optional[str] = None
    error: Optional[str] = None
