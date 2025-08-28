"""
Generate Python Logic Service Implementation
"""

import json
import re
from typing import Any, Dict
from pydantic import BaseModel
from llm_generator_v2.services import Service as BaseService
from .templates import PROMPT


class GeneratePythonLogicService(BaseService):
    """Service for generating Python validation logic from enriched checks"""

    class CannotParseLLMResponse(Exception):
        """Exception raised when LLM response cannot be parsed"""
        pass

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}-{input_.check.resource.name}.yaml"

    def _get_output_filename(self, output_: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id and resource name."""
        # This is with Input
        if hasattr(output_, "check") and output_.check.resource.name:
            return f"{output_.check.unique_id}-{output_.check.resource.name}.yaml"
        # This is with Output
        elif hasattr(output_, "resource") and output_.resource.name:
            return f"{output_.resource.check.unique_id}-{output_.resource.name}.yaml"
        raise self.GenerateUniqueFilepath()

    @staticmethod
    def mark_primitives(field_paths):
        result = {}
        field_set = set(field_paths)

        for path in field_paths:
            has_children = any(other.startswith(path + ".") for other in field_set)

            if path.endswith("[]"):
                result[path] = "not primitive" if has_children else "primitive list"
            else:
                if path + "[]" in field_set or has_children:
                    result[path] = "not primitive"
                else:
                    result[path] = "primitive"

        return result

    def _process_input(self, input_):
        """Process a single input and generate Python logic"""
        # Format the prompt
        primitive_aware_field_paths = self.mark_primitives(input_.check.resource.field_paths)
        primitive_aware_field_paths_str = "\n- ".join([
            f"{field}: {type_}"
            for field, type_ in primitive_aware_field_paths.items()
        ])
        prompt = PROMPT.format(
            check_unique_id=input_.check.unique_id,
            check_name=input_.check.name,
            check_category=input_.check.category,
            check_literature=input_.check.literature,
            check_control_names="\n- ".join(input_.check.control_names),
            resource_name=input_.check.resource.name,
            resource_field_paths=primitive_aware_field_paths_str,
            resource_reason=input_.check.resource.reason,
            resource_literature=input_.check.resource.literature,
        )

        # Call LLM
        llm_response = self.llm_client.generate_text(prompt)

        # Parse JSON response
        parsed_response = self._parse_llm_json(llm_response)

        # Validate required fields
        if "field_path" not in parsed_response:
            raise self.CannotParseLLMResponse("Missing field_path in response")
        if "logic" not in parsed_response:
            raise self.CannotParseLLMResponse("Missing logic in response")

        return self.Output(resource=dict(
            name=input_.check.resource.name,
            field_path=parsed_response["field_path"],
            logic=parsed_response["logic"],
            check=dict(
                unique_id=input_.check.unique_id,
            ),
            prompt=prompt,
        ))

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

        raise GeneratePythonLogicService.CannotParseLLMResponse(f"Could not parse JSON from response: {response_text[:200]}...")
