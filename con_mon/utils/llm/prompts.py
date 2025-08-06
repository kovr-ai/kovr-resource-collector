"""
LLM Prompt Templates and Post-Processing

This module contains specialized prompt classes for different use cases.
Each class handles prompt template formatting and response post-processing.

Classes:
- BasePrompt: Abstract base class for all prompts
- GeneralPrompt: General purpose text generation
- ComplianceCheckPrompt: Generate compliance check code
- ControlAnalysisPrompt: Analyze control requirements
"""

import re
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

from .client import get_llm_client, LLMRequest, LLMResponse


class BasePrompt(ABC):
    """
    Abstract base class for all prompt templates.
    
    Provides a common interface for prompt formatting and response processing.
    """
    
    @abstractmethod
    def format_prompt(self, **kwargs) -> str:
        """Format the prompt template with provided parameters."""
        pass
    
    @abstractmethod
    def process_response(self, response: LLMResponse) -> Any:
        """Process the LLM response and return structured data."""
        pass
    
    def generate(self, **kwargs) -> Any:
        """
        Generate response using the prompt template.
        
        Args:
            **kwargs: Parameters for prompt formatting and LLM generation
            
        Returns:
            Processed response data
        """
        # Format prompt
        prompt = self.format_prompt(**kwargs)
        
        # Extract LLM parameters
        llm_params = {
            'model_id': kwargs.get('model_id'),
            'max_tokens': kwargs.get('max_tokens'),
            'temperature': kwargs.get('temperature'),
            'top_p': kwargs.get('top_p'),
            'stop_sequences': kwargs.get('stop_sequences')
        }
        # Remove None values
        llm_params = {k: v for k, v in llm_params.items() if v is not None}
        
        # Get LLM client and generate response
        client = get_llm_client()
        request = LLMRequest(prompt=prompt, **llm_params)
        response = client.generate_response(request)
        
        # Process and return response
        return self.process_response(response)


class GeneralPrompt(BasePrompt):
    """
    General purpose prompt for text generation.
    
    Simple prompt that returns the raw text response without special processing.
    """
    
    def format_prompt(self, text: str, context: Optional[str] = None, **kwargs) -> str:
        """
        Format a general text prompt.
        
        Args:
            text: Main prompt text
            context: Optional context information
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Formatted prompt string
        """
        if context:
            return f"Context: {context}\n\nPrompt: {text}"
        return text
    
    def process_response(self, response: LLMResponse) -> str:
        """
        Process general response by returning raw content.
        
        Args:
            response: LLM response object
            
        Returns:
            Raw text content
        """
        return response.content.strip()


class ComplianceCheckPrompt(BasePrompt):
    """
    Prompt for generating compliance check code.
    
    Generates Python code that can be used in the checks.yaml files
    for automated compliance validation.
    """
    
    TEMPLATE = """You are a cybersecurity compliance expert. Generate Python code for an automated compliance check.

**Control Information:**
- Control ID: {control_name}
- Control Title: {control_title}
- Resource Type: {resource_type}

**Control Requirement:**
{control_text}

**Instructions:**
1. Generate Python code that validates compliance with this control
2. The code should work with {resource_type} data structures
3. Set a boolean variable 'result' to True if compliant, False if not
4. Add comments explaining the logic
5. Handle edge cases and missing data gracefully
6. Use only standard Python libraries and basic data operations

**Data Context:**
The variable 'resource_data' contains the {resource_type} resource information to validate.

**Example Structure:**
```python
# Check for [specific requirement]
try:
    # Your validation logic here
    if [condition]:
        result = True
    else:
        result = False
except Exception as e:
    # Handle errors gracefully
    result = False
```

Generate ONLY the Python code, no explanations or markdown formatting:"""
    
    def format_prompt(
        self, 
        control_name: str,
        control_text: str,
        resource_type: str = "github",
        control_title: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Format compliance check prompt.
        
        Args:
            control_name: Control identifier (e.g., "AC-2")
            control_text: Full control description/requirement
            resource_type: Target resource type (github, aws, etc.)
            control_title: Optional control title
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Formatted prompt string
        """
        return self.TEMPLATE.format(
            control_name=control_name,
            control_title=control_title or "Control Compliance Check",
            control_text=control_text,
            resource_type=resource_type.title()
        )
    
    def process_response(self, response: LLMResponse) -> str:
        """
        Process compliance check response and extract Python code.
        
        Args:
            response: LLM response object
            
        Returns:
            Cleaned Python code ready for execution
        """
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        content = re.sub(r'```python\s*\n?', '', content)
        content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        # Ensure the code sets a result variable
        if 'result =' not in content and 'result=' not in content:
            # Look for return statements and convert them
            if 'return True' in content:
                content = content.replace('return True', 'result = True')
            elif 'return False' in content:
                content = content.replace('return False', 'result = False')
            else:
                # Add a default result assignment if none found
                content += '\n\n# Default result if not set above\nif "result" not in locals():\n    result = False'
        
        return content


class ControlAnalysisPrompt(BasePrompt):
    """
    Prompt for analyzing control requirements.
    
    Analyzes a control's text to extract key information like
    automation feasibility, required checks, and implementation guidance.
    """
    
    TEMPLATE = """You are a cybersecurity compliance expert. Analyze this control requirement and provide structured insights.

**Control Information:**
- Control ID: {control_name}
- Control Title: {control_title}

**Control Requirement:**
{control_text}

**Analysis Instructions:**
Provide a JSON response with the following structure:
{{
    "automation_feasibility": "high|medium|low",
    "automation_reason": "Brief explanation of why this control can/cannot be automated",
    "key_requirements": ["List of key requirements that need to be checked"],
    "resource_types": ["List of resource types this control applies to (github, aws, azure, etc.)"],
    "check_categories": ["List of categories like access_control, configuration, monitoring, etc."],
    "implementation_complexity": "low|medium|high",
    "technical_requirements": ["List of technical things to validate"],
    "manual_requirements": ["List of things that require manual review"],
    "suggested_checks": ["List of specific automated checks that could be implemented"]
}}

Respond with ONLY the JSON object, no explanations or additional text:"""
    
    def format_prompt(
        self,
        control_name: str,
        control_text: str,
        control_title: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Format control analysis prompt.
        
        Args:
            control_name: Control identifier (e.g., "AC-2")
            control_text: Full control description/requirement
            control_title: Optional control title
            **kwargs: Additional parameters (ignored)
            
        Returns:
            Formatted prompt string
        """
        return self.TEMPLATE.format(
            control_name=control_name,
            control_title=control_title or "Control Analysis",
            control_text=control_text
        )
    
    def process_response(self, response: LLMResponse) -> Dict[str, Any]:
        """
        Process control analysis response and parse JSON.
        
        Args:
            response: LLM response object
            
        Returns:
            Dictionary containing structured analysis data
        """
        content = response.content.strip()
        
        # Try to extract JSON from the response
        try:
            # Look for JSON object in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # If no JSON found, try parsing the entire content
                return json.loads(content)
                
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return a default structure with error
            return {
                "automation_feasibility": "unknown",
                "automation_reason": f"Failed to parse analysis response: {str(e)}",
                "key_requirements": [],
                "resource_types": [],
                "check_categories": [],
                "implementation_complexity": "unknown",
                "technical_requirements": [],
                "manual_requirements": [],
                "suggested_checks": [],
                "error": f"JSON parsing failed: {str(e)}",
                "raw_response": content
            }


class PromptResult(BaseModel):
    """
    Result object for prompt operations.
    
    Contains both the processed result and metadata about the operation.
    """
    result: Any
    prompt_class: str
    model_id: str
    usage: Dict[str, int]
    duration: Optional[float] = None
    error: Optional[str] = None


# Convenience functions for quick access to common prompts

def generate_compliance_check(
    control_name: str,
    control_text: str,
    resource_type: str = "github",
    **kwargs
) -> str:
    """
    Quick function to generate compliance check code.
    
    Args:
        control_name: Control identifier
        control_text: Control requirement text
        resource_type: Target resource type
        **kwargs: Additional LLM parameters
        
    Returns:
        Generated Python code
    """
    prompt = ComplianceCheckPrompt()
    return prompt.generate(
        control_name=control_name,
        control_text=control_text,
        resource_type=resource_type,
        **kwargs
    )


def analyze_control(
    control_name: str,
    control_text: str,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick function to analyze control requirements.
    
    Args:
        control_name: Control identifier
        control_text: Control requirement text
        **kwargs: Additional LLM parameters
        
    Returns:
        Dictionary containing analysis results
    """
    prompt = ControlAnalysisPrompt()
    return prompt.generate(
        control_name=control_name,
        control_text=control_text,
        **kwargs
    )


def generate_text(text: str, context: Optional[str] = None, **kwargs) -> str:
    """
    Quick function for general text generation.
    
    Args:
        text: Prompt text
        context: Optional context
        **kwargs: Additional LLM parameters
        
    Returns:
        Generated text
    """
    prompt = GeneralPrompt()
    return prompt.generate(text=text, context=context, **kwargs)
