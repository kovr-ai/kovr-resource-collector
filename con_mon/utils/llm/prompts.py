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


class ChecksYamlPrompt(BasePrompt):
    """
    Prompt for generating complete checks.yaml entries.
    
    Generates a complete YAML check entry with all required fields including
    ID, connection details, operations, tags, severity, and control mappings.
    """
    
    TEMPLATE = """You are a cybersecurity compliance expert. Generate a complete checks.yaml entry for automated compliance validation.

**Control Information:**
- Control ID: {control_name}
- Control Title: {control_title}
- Resource Type: {resource_type}

**Control Requirement:**
{control_text}

**Instructions:**
1. Generate a complete YAML check entry following the exact format shown in the example
2. Include a unique check ID (use {suggested_check_id} as the base)
3. Create a descriptive name using snake_case format
4. Write a clear description explaining what the check validates
5. Set appropriate resource_type (GithubResource, AwsResource, etc.)
6. Determine the correct field_path for the resource data
7. Generate Python code for the custom_logic that validates compliance
8. Set expected_value to null for custom logic checks
9. Add relevant tags for categorization
10. Set appropriate severity level (low, medium, high, critical)
11. Choose the correct category
12. Map to relevant control IDs - USE NUMERIC DATABASE ID {control_id}, NOT control name

**IMPORTANT:** The control_ids field must contain the numeric database ID ({control_id}), NOT the control name ({control_name}).

**Example Format:**
```yaml
checks:
- id: {suggested_check_id}
  connection_id: {connection_id}
  name: {resource_type_lower}_{control_name_lower}_compliance
  description: Verify compliance with NIST 800-53 {control_name}: {control_title}
  resource_type: {resource_type}Resource
  field_path: {suggested_field_path}
  output_statements:
    success: Compliance with NIST 800-53 {control_name}: {control_title} verified
    failure: Compliance with NIST 800-53 {control_name}: {control_title} failed
    partial: Compliance with NIST 800-53 {control_name}: {control_title} partially verified
  fix_details:
    description: str
    instructions: List[str]
    estimated_date: str
    automation_available: bool = False
  operation:
    name: custom
    custom_logic: |
      # Your Python validation code here
      # Set result = True if compliant, False if not
      result = False
      try:
          # Your logic here
          if condition:
              result = True
      except Exception as e:
          result = False
  expected_value: null
  tags:
  - compliance
  - nist
  - {control_family_tag}
  - {resource_type_lower}
  severity: {suggested_severity}
  category: {suggested_category}
  control_ids:
  - {control_id}
```

**Resource Type Guidelines:**
- GitHub: field_path examples: repository_data.branches, repository_data.settings, repository_data.collaborators
- AWS: field_path examples: iam_data.policies, iam_data.users, ec2_data.instances
- Azure: field_path examples: resource_data.policies, resource_data.rbac
- GCP: field_path examples: project_data.iam, project_data.resources

**Severity Guidelines:**
- Critical: System-wide security failures, data exposure risks
- High: Access control violations, authentication issues
- Medium: Configuration issues, monitoring gaps
- Low: Documentation, procedural compliance

**Category Guidelines:**
- access_control: User permissions, authentication, authorization
- configuration: System settings, security configurations
- monitoring: Logging, auditing, alerting
- data_protection: Encryption, data handling
- network_security: Firewall, network controls

Generate ONLY the YAML check entry, no explanations or additional text:"""
    
    def format_prompt(
        self,
        control_name: str,
        control_text: str,
        control_title: Optional[str] = None,
        resource_type: str = "github",
        connection_id: int = 1,
        control_id: Optional[int] = None,
        suggested_check_id: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Format checks YAML generation prompt.
        
        Args:
            control_name: Control identifier (e.g., "AC-2")
            control_text: Full control description/requirement
            control_title: Control title/name
            resource_type: Target resource type (github, aws, etc.)
            connection_id: Connection ID for the check
            control_id: Database ID of the control
            suggested_check_id: Suggested ID for the check
            **kwargs: Additional parameters
            
        Returns:
            Formatted prompt string
        """
        # Generate suggestions based on control and resource type
        resource_type_lower = resource_type.lower()
        control_name_lower = control_name.lower().replace('-', '_')
        
        # Suggest field path based on resource type and control
        field_path_suggestions = {
            "github": self._suggest_github_field_path(control_name, control_text),
            "aws": self._suggest_aws_field_path(control_name, control_text),
            "azure": "resource_data.policies",
            "gcp": "project_data.iam"
        }
        
        # Suggest severity based on control family
        severity_suggestions = {
            "AC": "high",  # Access Control
            "AU": "medium",  # Audit and Accountability
            "CM": "medium",  # Configuration Management
            "IA": "high",  # Identification and Authentication
            "SC": "high",  # System and Communications Protection
            "SI": "medium",  # System and Information Integrity
        }
        
        # Suggest category based on control family
        category_suggestions = {
            "AC": "access_control",
            "AU": "monitoring",
            "CM": "configuration",
            "IA": "access_control",
            "SC": "network_security",
            "SI": "monitoring",
        }
        
        control_family = control_name.split('-')[0] if '-' in control_name else control_name[:2]
        
        return self.TEMPLATE.format(
            control_name=control_name,
            control_title=control_title or "Compliance Check",
            control_text=control_text,
            resource_type=resource_type,
            suggested_check_id=suggested_check_id or 1000,
            connection_id=connection_id,
            resource_type_lower=resource_type_lower,
            control_name_lower=control_name_lower,
            suggested_field_path=field_path_suggestions.get(resource_type_lower, "resource_data"),
            control_family_tag=control_family.lower(),
            suggested_severity=severity_suggestions.get(control_family, "medium"),
            suggested_category=category_suggestions.get(control_family, "configuration"),
            control_id=control_id or 1000
        )
    
    def _suggest_github_field_path(self, control_name: str, control_text: str) -> str:
        """Suggest GitHub field path based on control content."""
        text_lower = control_text.lower()
        
        if any(term in text_lower for term in ['branch', 'protection', 'merge']):
            return "repository_data.branches"
        elif any(term in text_lower for term in ['collaborator', 'user', 'access', 'permission']):
            return "repository_data.collaborators"
        elif any(term in text_lower for term in ['webhook', 'integration']):
            return "repository_data.webhooks"
        elif any(term in text_lower for term in ['secret', 'token', 'key']):
            return "repository_data.secrets"
        elif any(term in text_lower for term in ['issue', 'pull request']):
            return "repository_data.settings"
        else:
            return "repository_data.settings"
    
    def _suggest_aws_field_path(self, control_name: str, control_text: str) -> str:
        """Suggest AWS field path based on control content."""
        text_lower = control_text.lower()
        
        if any(term in text_lower for term in ['iam', 'user', 'role', 'policy', 'access']):
            return "iam_data.policies"
        elif any(term in text_lower for term in ['ec2', 'instance', 'security group']):
            return "ec2_data.instances"
        elif any(term in text_lower for term in ['s3', 'bucket', 'storage']):
            return "s3_data.buckets"
        elif any(term in text_lower for term in ['cloudtrail', 'log', 'audit']):
            return "cloudtrail_data.trails"
        else:
            return "iam_data.policies"
    
    def process_response(self, response: LLMResponse) -> str:
        """
        Process checks YAML response and clean up formatting.
        
        Args:
            response: LLM response object
            
        Returns:
            Cleaned YAML content ready for use
        """
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        content = re.sub(r'```yaml\s*\n?', '', content)
        content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        # Ensure proper YAML structure
        if not content.startswith('checks:'):
            # If the response doesn't start with 'checks:', add it
            if content.startswith('- id:'):
                content = 'checks:\n' + content
        
        return content


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


def generate_checks_yaml(
    control_name: str,
    control_text: str,
    control_title: Optional[str] = None,
    resource_type: str = "github",
    connection_id: int = 1,
    control_id: Optional[int] = None,
    suggested_check_id: Optional[int] = None,
    **kwargs
) -> str:
    """
    Quick function to generate complete checks.yaml entry.
    
    Args:
        control_name: Control identifier
        control_text: Control requirement text
        control_title: Control title/name
        resource_type: Target resource type
        connection_id: Connection ID for the check
        control_id: Database ID of the control
        suggested_check_id: Suggested ID for the check
        **kwargs: Additional LLM parameters
        
    Returns:
        Generated YAML content
    """
    prompt = ChecksYamlPrompt()
    return prompt.generate(
        control_name=control_name,
        control_text=control_text,
        control_title=control_title,
        resource_type=resource_type,
        connection_id=connection_id,
        control_id=control_id,
        suggested_check_id=suggested_check_id,
        **kwargs
    )
