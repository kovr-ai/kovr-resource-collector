"""
Service implementation for add_targeted_literature.
Analyzes security checks and determines resource compatibility with detailed implementation guidance.
"""

import json
import logging
from typing import Dict, Any
from pydantic import BaseModel
from llm_generator_v2.services import Service as BaseService
from llm_generator_v2.system_compatible_checks_literature.add_targeted_literature.templates import PROMPT

logger = logging.getLogger(__name__)


class CannotParseLLMResponse(Exception):
    """Raised when LLM response cannot be parsed as JSON"""
    pass


class AddTargetedLiteratureService(BaseService):
    """
    Service that uses LLM to analyze security checks and generate resource-specific
    implementation guidance with field path validation.
    """

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}.yaml"

    def _get_output_filename(self, output_: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id and resource name."""
        try:
            check_id = output_.resource.check.unique_id
            resource_name = output_.resource.name
            # Clean the resource name to be filename-safe
            safe_resource_name = resource_name.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '').replace('.', '')
            return f"{check_id}_{safe_resource_name[:30]}.yaml"
        except Exception as e:
            logger.error(f"Error in _get_output_filename: {e}")
            logger.error(f"Output structure: {output_.model_dump() if hasattr(output_, 'model_dump') else output_}")
            # Return a generic filename as fallback
            return f"fallback_{hash(str(output_)) % 10000:04d}.yaml"

    def _match_input_output(self, input_, output_):
        return input_.check.unique_id == output_.resource.check.unique_id

    def _process_input(self, input_data) -> Dict[str, Any]:
        """
        Process input through LLM to generate targeted literature for resource implementation.
        
        Args:
            input_data: Pydantic model containing check and resource information
            
        Returns:
            Dictionary with resource analysis and implementation guidance
        """
        # Convert to dict if it's a Pydantic model
        if hasattr(input_data, 'model_dump'):
            input_dict = input_data.model_dump()
        else:
            input_dict = input_data
            
        check = input_dict['check']
        
        # Format the prompt with input data
        prompt = PROMPT.format(
            check_name=check['name'],
            check_unique_id=check['unique_id'],
            check_category=check['category'],
            check_literature=check['literature'],
            control_names=', '.join(check.get('control_names', [])),
            provider=check['provider'],
            resource_name=check['resource']['name'],
            field_paths=', '.join(check['resource']['field_paths'])
        )
        
        # Get LLM response
        llm_response = self.llm_client.generate_text(prompt)
        
        # Parse LLM response with robust error handling
        try:
            analysis = self._parse_llm_response(llm_response)
            return {"resource": analysis}
        except CannotParseLLMResponse as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            fallback_analysis = self._create_fallback_analysis(check)
            logger.info(f"Created fallback analysis: {fallback_analysis}")
            return {"resource": fallback_analysis}
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response with multiple fallback strategies.
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed analysis dictionary
            
        Raises:
            CannotParseLLMResponse: If all parsing attempts fail
        """
        parsing_methods = [
            self._parse_json_direct,
            self._parse_json_with_markdown_removal,
            self._parse_json_with_extraction
        ]
        
        for method in parsing_methods:
            try:
                return method(response)
            except Exception:
                continue
        
        raise CannotParseLLMResponse(f"All parsing methods failed for response: {response[:200]}...")
    
    @staticmethod
    def _parse_json_direct(response: str) -> Dict[str, Any]:
        """Direct JSON parsing attempt."""
        parsed = json.loads(response.strip())
        
        # Ensure is_valid is boolean
        if 'is_valid' in parsed and not isinstance(parsed['is_valid'], bool):
            if isinstance(parsed['is_valid'], str):
                parsed['is_valid'] = parsed['is_valid'].lower() in ['true', '1', 'yes']
            else:
                parsed['is_valid'] = bool(parsed['is_valid'])
        
        return parsed
    
    @staticmethod
    def _parse_json_with_markdown_removal(response: str) -> Dict[str, Any]:
        """Parse after removing common markdown wrappers."""
        cleaned = response.strip()
        
        # Remove common markdown code block wrappers
        if cleaned.startswith('```json') and cleaned.endswith('```'):
            cleaned = cleaned[7:-3].strip()
        elif cleaned.startswith('```') and cleaned.endswith('```'):
            cleaned = cleaned[3:-3].strip()
        
        parsed = json.loads(cleaned)
        
        # Ensure is_valid is boolean
        if 'is_valid' in parsed and not isinstance(parsed['is_valid'], bool):
            if isinstance(parsed['is_valid'], str):
                parsed['is_valid'] = parsed['is_valid'].lower() in ['true', '1', 'yes']
            else:
                parsed['is_valid'] = bool(parsed['is_valid'])
        
        return parsed
    
    @staticmethod
    def _parse_json_with_extraction(response: str) -> Dict[str, Any]:
        """Extract JSON from response with more aggressive cleaning."""
        # Find JSON object bounds
        start_idx = response.find('{')
        end_idx = response.rfind('}')
        
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx + 1]
            parsed = json.loads(json_str)
            
            # Ensure is_valid is boolean
            if 'is_valid' in parsed and not isinstance(parsed['is_valid'], bool):
                if isinstance(parsed['is_valid'], str):
                    parsed['is_valid'] = parsed['is_valid'].lower() in ['true', '1', 'yes']
                else:
                    parsed['is_valid'] = bool(parsed['is_valid'])
            
            return parsed
        
        raise ValueError("No JSON object found in response")
    
    def _create_fallback_analysis(self, check: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a fallback analysis when LLM parsing fails.
        
        Args:
            check: Input check data
            
        Returns:
            Basic analysis structure with fallback values
        """
        resource_name = check['resource']['name']
        check_name = check['name']
        
        return {
            'name': resource_name,
            'check': {
                'unique_id': check['unique_id']
            },
            'is_valid': False,  # Always boolean - partial cases should be classified as False for safety
            'literature': f'Analysis needed for {resource_name} implementation of {check_name}. '
                         f'This resource may be applicable but requires manual review to determine '
                         f'specific implementation details and field path relevance.',
            'field_paths': check['resource']['field_paths'][:3] if check['resource']['field_paths'] else [],  # Limit to first 3 paths
            'reason': 'Automated analysis was unable to complete. Manual review required to '
                     'determine resource applicability and implementation approach.',
            'output_statements': {
                'success': f'{check_name} check passed for {resource_name}',
                'failure': f'{check_name} check failed for {resource_name}',
                'partial': f'{check_name} check partially implemented for {resource_name}'
            },
            'fix_details': {
                'description': f'Manual review required for {resource_name} implementation',
                'instructions': [
                    'Review resource documentation for applicable fields',
                    'Verify field path relevance to security check',
                    'Implement appropriate validation logic'
                ],
                'estimated_time': '30 minutes',
                'automation_available': False
            }
        }
