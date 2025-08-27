"""
Validate with Mock Data Service Implementation
"""

import json
import traceback
from typing import Any, Dict, List
from pathlib import Path
from pydantic import BaseModel
from llm_generator_v2.services import Service


class ValidateWithMockDataService(Service):
    """Service for validating Python logic against mock resource data"""
    
    def __init__(self):
        super().__init__("validate_with_mock_data")
        self.mock_data_cache = {}

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}.yaml"

    def _get_output_filename(self, output_: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id."""
        # For validation errors, we'll use a generic name since the output structure is different
        return f"validation_errors.yaml"

    def _match_input_output(self, input_, output_):
        return input_.check.unique_id == input_.check.unique_id  # Since output is just errors, match by input unique_id
    
    def _process_input(self, input_data: Any) -> Any:
        """Process a single input and validate Python logic"""
        # Convert Pydantic model to dict if needed
        if hasattr(input_data, 'model_dump'):
            input_dict = input_data.model_dump()
        else:
            input_dict = input_data
        
        check_data = input_dict["check"]
        resource_name = check_data["resource"]["name"]
        field_path = check_data["resource"]["field_path"]
        logic = check_data["resource"]["logic"]
        
        # Load mock data for this resource
        mock_data = self._load_mock_data_for_resource(resource_name)
        
        validation_results = []
        
        for resource_id, resource_data in mock_data.items():
            try:
                # Extract value using field path
                fetched_value = self._extract_field_value(resource_data, field_path)
                
                # Execute Python logic
                result = self._execute_logic(logic, fetched_value)
                
                validation_results.append({
                    "resource_id": resource_id,
                    "success": True,
                    "result": result,
                    "error": None,
                    "fetched_value_type": str(type(fetched_value).__name__),
                    "fetched_value_sample": str(fetched_value)[:100] if fetched_value is not None else "None"
                })
                
            except Exception as e:
                validation_results.append({
                    "resource_id": resource_id,
                    "success": False,
                    "result": False,
                    "error": str(e),
                    "fetched_value_type": "error",
                    "fetched_value_sample": "error"
                })
        
        # Calculate summary statistics
        total_tests = len(validation_results)
        successful_tests = sum(1 for r in validation_results if r["success"])
        failed_tests = total_tests - successful_tests
        success_rate = successful_tests / total_tests if total_tests > 0 else 0.0
        
        # Determine overall validation status
        if success_rate >= 0.8:
            validation_status = "passed"
        elif success_rate >= 0.5:
            validation_status = "partial"
        else:
            validation_status = "failed"
        
        # Create output using output model (simple errors[] structure)
        from . import OutputValidationResult
        
        # Collect errors from failed tests
        errors = []
        for result in validation_results:
            if not result["success"]:
                errors.append(f"Resource {result['resource_id']}: {result['error']}")
        
        # If too many errors, summarize
        if len(errors) > 10:
            errors = errors[:10] + [f"... and {len(errors) - 10} more errors"]
        
        output = OutputValidationResult(errors=errors)
        
        return output
    
    def _load_mock_data_for_resource(self, resource_name: str) -> Dict[str, Any]:
        """Load mock data for a specific resource type"""
        if resource_name in self.mock_data_cache:
            return self.mock_data_cache[resource_name]
        
        # Determine provider from resource name
        provider = self._get_provider_from_resource_name(resource_name)
        
        # Load mock data file
        mock_file_path = Path(__file__).parent.parent.parent.parent.parent / "tests" / "mocks" / provider / "response.json"
        
        if not mock_file_path.exists():
            # Return empty mock data if file doesn't exist
            self.mock_data_cache[resource_name] = {}
            return {}
        
        try:
            with open(mock_file_path, 'r') as f:
                mock_data = json.load(f)
            
            self.mock_data_cache[resource_name] = mock_data
            return mock_data
            
        except Exception as e:
            print(f"Warning: Could not load mock data from {mock_file_path}: {e}")
            self.mock_data_cache[resource_name] = {}
            return {}
    
    def _get_provider_from_resource_name(self, resource_name: str) -> str:
        """Determine provider name from resource name"""
        # Use naming conventions to determine provider
        resource_lower = resource_name.lower()
        
        if "github" in resource_lower:
            return "github"
        elif any(term in resource_lower for term in ["ec2", "iam", "s3", "cloudwatch", "cloudtrail"]):
            return "provider_1"  # Avoid hardcoded names
        elif "user" in resource_lower or "group" in resource_lower:
            return "provider_2"  # Avoid hardcoded names
        else:
            # Default to first available provider
            return "github"
    
    def _extract_field_value(self, resource_data: Dict[str, Any], field_path: str) -> Any:
        """Extract value from resource data using field path"""
        try:
            # Handle simple field access
            if '.' not in field_path and '[' not in field_path:
                return resource_data.get(field_path)
            
            # Handle nested field access
            current_value = resource_data
            path_parts = self._parse_field_path(field_path)
            
            for part in path_parts:
                if part == '*' or part == '[]':
                    # Handle wildcard/array access
                    if isinstance(current_value, list):
                        current_value = [item for item in current_value if item is not None]
                    else:
                        current_value = []
                elif part.isdigit():
                    # Handle specific array index
                    if isinstance(current_value, list):
                        index = int(part)
                        current_value = current_value[index] if index < len(current_value) else None
                    else:
                        current_value = None
                else:
                    # Handle object field access
                    if isinstance(current_value, dict):
                        current_value = current_value.get(part)
                    elif hasattr(current_value, part):
                        current_value = getattr(current_value, part)
                    else:
                        current_value = None
                
                if current_value is None:
                    break
            
            return current_value
            
        except Exception as e:
            print(f"Error extracting field path '{field_path}': {e}")
            return None
    
    def _parse_field_path(self, field_path: str) -> List[str]:
        """Parse field path into components"""
        # Simple parsing - can be enhanced
        parts = []
        current_part = ""
        
        i = 0
        while i < len(field_path):
            char = field_path[i]
            
            if char == '.':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
            elif char == '[':
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                # Find closing bracket
                j = i + 1
                while j < len(field_path) and field_path[j] != ']':
                    j += 1
                
                if j < len(field_path):
                    bracket_content = field_path[i+1:j]
                    if bracket_content == '*' or bracket_content == '':
                        parts.append('[]')
                    else:
                        parts.append(bracket_content)
                    i = j
            else:
                current_part += char
            
            i += 1
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    def _execute_logic(self, logic: str, fetched_value: Any) -> bool:
        """Execute Python logic with fetched_value"""
        # Create execution context
        exec_context = {
            'fetched_value': fetched_value,
            'result': False,
            # Add safe helper functions
            'hasattr': hasattr,
            'isinstance': isinstance,
            'getattr': getattr,
            'len': len,
            'str': str,
            'bool': bool,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'set': set,
            'any': any,
            'all': all,
        }
        
        try:
            # Execute the logic
            exec(logic, exec_context)
            return exec_context.get('result', False)
            
        except Exception as e:
            print(f"Error executing logic: {e}")
            print(f"Logic:\n{logic}")
            print(f"Traceback: {traceback.format_exc()}")
            return False


# Create service instance
service = ValidateWithMockDataService()
