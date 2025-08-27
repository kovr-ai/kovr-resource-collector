"""
Generate Python Logic Service Implementation
"""

import json
import re
from typing import Any, Dict
from pydantic import BaseModel
from llm_generator_v2.services import Service
from .templates import PROMPT


class CannotParseLLMResponse(Exception):
    """Exception raised when LLM response cannot be parsed"""
    pass


class GeneratePythonLogicService(Service):
    """Service for generating Python validation logic from enriched checks"""
    
    def __init__(self):
        super().__init__("generate_python_logic")

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}.yaml"

    def _get_output_filename(self, output_: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id and field path."""
        check_id = output_.resource.check.unique_id
        field_path = output_.resource.field_path
        # Clean the field path to be filename-safe
        safe_field_path = field_path.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '').replace('.', '').replace('/', '_')
        return f"{check_id}_{safe_field_path[:30]}.yaml"

    def _match_input_output(self, input_, output_):
        return input_.check.unique_id == output_.resource.check.unique_id

    def _process_input(self, input_data: Any) -> Any:
        """Process a single input and generate Python logic"""
        # Convert Pydantic model to dict if needed
        if hasattr(input_data, 'model_dump'):
            input_dict = input_data.model_dump()
        else:
            input_dict = input_data
        
        # Format the prompt
        prompt = PROMPT
        for key, value in input_dict.items():
            if key == "check":
                # Handle nested check object
                check_data = value
                for check_key, check_value in check_data.items():
                    if check_key == "resource":
                        # Handle nested resource object
                        resource_data = check_value
                        for resource_key, resource_value in resource_data.items():
                            if isinstance(resource_value, list):
                                resource_value = ", ".join(str(v) for v in resource_value)
                            prompt = prompt.replace(f"{{{{check.resource.{resource_key}}}}}", str(resource_value))
                    else:
                        if isinstance(check_value, list):
                            check_value = ", ".join(str(v) for v in check_value)
                        prompt = prompt.replace(f"{{{{check.{check_key}}}}}", str(check_value))
            else:
                prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
        
        # Call LLM
        llm_response = self.llm_client.call_llm(prompt)
        
        # Parse JSON response
        try:
            parsed_response = self._parse_llm_json(llm_response)
            
            # Validate required fields
            if "field_path" not in parsed_response:
                raise CannotParseLLMResponse("Missing field_path in response")
            if "logic" not in parsed_response:
                raise CannotParseLLMResponse("Missing logic in response")
            
            # Create output using output model
            from . import OutputResource
            
            output = OutputResource(
                field_path=parsed_response["field_path"],
                logic=parsed_response["logic"]
            )
            
            return output
            
        except Exception as e:
            # Create fallback output
            fallback_field_path = input_dict["check"]["resource"]["field_paths"][0] if input_dict["check"]["resource"]["field_paths"] else "id"
            fallback_logic = f"""result = False

# Fallback logic for {input_dict["check"]["unique_id"]}
if fetched_value is None:
    result = False
elif not fetched_value:
    result = False
else:
    # Basic existence check
    result = True
"""
            
            output = OutputResource(
                field_path=fallback_field_path,
                logic=fallback_logic
            )
            
            return output
    
    @staticmethod
    def _parse_llm_json(response_text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response with multiple fallback strategies"""
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            pass
        
        # Strategy 2: Extract JSON block
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 3: Find JSON object in text
        json_match = re.search(r'(\{[^{}]*"field_path"[^{}]*"logic"[^{}]*\})', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Strategy 4: Manual extraction
        field_path_match = re.search(r'"field_path":\s*"([^"]*)"', response_text)
        logic_match = re.search(r'"logic":\s*"([^"]*)"', response_text, re.DOTALL)
        
        if field_path_match and logic_match:
            return {
                "field_path": field_path_match.group(1),
                "logic": logic_match.group(1).replace('\\n', '\n')
            }
        
        raise CannotParseLLMResponse(f"Could not parse JSON from response: {response_text[:200]}...")


# Create service instance
service = GeneratePythonLogicService()
