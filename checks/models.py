"""
Models for checks module - handles resource validation and evaluation.
"""
from enum import Enum
from typing import Any, Callable, Optional
from pydantic import BaseModel, Field


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


class Check(BaseModel):
    """
    Represents a single check that evaluates a resource field against a configured value.
    """
    name: str
    field_path: str = Field(..., description="e.g., 'price', 'metadata.status', 'tags[0]'")
    operation: ComparisonOperation
    expected_value: Any
    description: Optional[str] = None
    
    def evaluate(self, resource_data: dict) -> "CheckResult":
        """
        Evaluate this check against a resource's data.
        
        Args:
            resource_data: Dictionary containing the resource's field values
            
        Returns:
            CheckResult: The result of the check evaluation
        """
        actual_value = self._extract_field_value(resource_data, self.field_path)
        passed = self.operation.compare(actual_value, self.expected_value)
        
        return CheckResult(
            passed=passed,
            check=self,
            message=f"Check '{self.name}' {'passed' if passed else 'failed'}"
        )
    
    def _extract_field_value(self, data: dict, field_path: str) -> Any:
        """Extract value from nested dictionary using dot notation."""
        keys = field_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value


class CheckResult(BaseModel):
    """Result of a check evaluation."""
    passed: bool
    check: Check
    message: Optional[str] = None
    error: Optional[str] = None
