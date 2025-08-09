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
import os
import yaml
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel
from con_mon_v2.checks import Check

from .client import get_llm_client, LLMRequest, LLMResponse
from ...resources import Resource


def load_resource_schema(resource_type: str) -> str:
    """
    Dynamically load resource schema from resources.yaml file.
    
    Args:
        resource_type: Resource type to load (github, aws, etc.)
        
    Returns:
        Formatted resource schema string for the specified type
    """
    try:
        # Get the path to resources.yaml
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resources_yaml_path = os.path.join(current_dir, '..', '..', 'resources', 'resources.yaml')
        
        # Read and parse the YAML file
        with open(resources_yaml_path, 'r') as f:
            resources_data = yaml.safe_load(f)
        
        # Extract the specific resource type section
        if resource_type.lower() in resources_data:
            resource_section = resources_data[resource_type.lower()]
            
            # Convert back to YAML format for the prompt
            schema_yaml = yaml.dump({resource_type.lower(): resource_section}, 
                                  default_flow_style=False, 
                                  sort_keys=False,
                                  allow_unicode=True)
            
            return f"**Resource Schema:**\n{schema_yaml}"
        else:
            return f"**Resource Schema:**\n# No schema found for resource type: {resource_type}"
            
    except Exception as e:
        return f"**Resource Schema:**\n# Error loading schema for {resource_type}: {str(e)}"


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


class ChecksYamlPrompt(BasePrompt):
    """
    Prompt for generating complete checks.yaml entries.
    
    Generates a complete YAML check entry with all required fields including
    ID, connection details, operations, tags, severity, and control mappings.
    """

    CONTROL_INFORMATION = """
**Control Information:**
- Control ID: {control_name}
- Control Title: {control_title}
- Connector Type: {connector_type}

**Control Requirement:**
{control_text}
    """

    INSTRUCTIONS = """
**Instructions:**
1. Generate a complete YAML check entry following the exact format shown in the example
2. Create a descriptive name using snake_case format
3. Write a clear description explaining what the check validates
4. Set appropriate resource_type using the resources structure below
4.1 resource_type can only be one of resources_field_schemas
5. Determine the correct field_path for the resource data using the resources structure below
5.1 field_path must be available in the resource_type
5.2 field_path must use dot notation to navigate nested structures
5.3 field_path should start with one of the top level resource fields
5.4 then navigate through nested objects using dots to reach the specific field you want to validate
6. Generate Python code for the custom_logic that validates compliance
6.1 the value at resource_type.field_path would be stored in fetched_value
6.2 fetched_value would be a pydantic class or primitive type
6. Generate Python code for the custom_logic that validates compliance
7. Set expected_value to null for custom logic checks
8. Add relevant tags for categorization
9. Set appropriate severity level (low, medium, high, critical)
10. Choose the correct category
11. Map to relevant control IDs - USE NUMERIC DATABASE ID {control_id}, NOT control name
    """

    SAMPLE_FORMAT = """
**Example Format:**
```yaml
checks:
- id: {resource_type_lower}_{control_name_lower}_compliance
  name: {resource_type_lower}_{control_name_lower}_compliance
  description: Verify compliance with NIST 800-53 {control_name}: {control_title}
  resource_type: # Choose specific resource type (GithubResource, AWSIAMResource, AWSEC2Resource, etc.)
  field_path: # Examples: "repository_data.basic_info.description", "security_data.security_analysis.advanced_security_enabled", "organization_data.members"
  operation:
    name: custom
    custom_logic: |
      # CRITICAL: Custom logic rules:
      # 1. NEVER use 'return' statements - this is not a function!
      # 2. ALWAYS set 'result = True' for compliance, 'result = False' for non-compliance
      # 3. Use 'fetched_value' variable to access the field data
      
      result = False  # Default to non-compliant
      # Your validation logic here using fetched_value
      if fetched_value and some_condition:
          result = True
      else:
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
  output_statements:
    success: "Check passed: [describe what was verified]"
    failure: "Check failed: [describe what was missing or incorrect]" 
    partial: "Check partially passed: [describe partial compliance]"
  fix_details:
    description: "Steps to fix the compliance issue"
    instructions:
    - "Step 1: [specific action]"
    - "Step 2: [specific action]"
    estimated_date: "2024-12-31"
    automation_available: false
```
    """

    GUIDELINES = """
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

**Custom Logic Rules (CRITICAL):**
- NEVER use 'return' statements in custom_logic - this causes execution errors
- ALWAYS use 'result = True' for compliance, 'result = False' for non-compliance
- Use 'fetched_value' variable to access the extracted field data
- Incase the logic fails to execute, don't catch and absorb the error. Let it bubble up

Generate ONLY the YAML check entry, no explanations or additional text:
    """
    
    def __init__(
        self,
        control_name: str,
        control_text: str,
        control_title: str,
        resource_type: Type[Resource],
        control_id: int,
    ):
        """
        Initialize the prompt with required parameters.
        
        Args:
            control_name: Control identifier (e.g., "AC-2")
            control_text: Full control description/requirement
            control_title: Control title/name
            resource_type: Target resource type class
            control_id: Database ID of the control
        """
        self.control_name = control_name
        self.control_text = control_text
        self.control_title = control_title
        self.resource_type = resource_type
        self.control_id = control_id
        
        # Pre-compute derived values
        self.resource_type_lower = re.sub(r'([a-z])([A-Z])', r'\1_\2', resource_type.__name__).lower()
        self.control_name_lower = control_name.lower().replace('-', '_')
        self.connector_type_lower = self.resource_type_lower.split('_')[0]
        self.control_family = control_name.split('-')[0] if '-' in control_name else control_name[:2]

    def format_prompt(self, **kwargs) -> str:
        """Format the prompt template with stored parameters."""
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
        
        resource_schema = load_resource_schema(self.connector_type_lower)
        
        # Format each template part
        control_info = self.CONTROL_INFORMATION.format(
            control_name=self.control_name,
            control_title=self.control_title,
            connector_type=self.resource_type.__name__,
            control_text=self.control_text
        )
        
        instructions = self.INSTRUCTIONS.format(
            control_id=self.control_id
        )
        
        sample_format = self.SAMPLE_FORMAT.format(
            resource_type_lower=self.resource_type_lower,
            control_name_lower=self.control_name_lower,
            control_name=self.control_name,
            control_title=self.control_title,
            control_family_tag=self.control_family.lower(),
            suggested_severity=severity_suggestions.get(self.control_family, "medium"),
            suggested_category=category_suggestions.get(self.control_family, "configuration"),
            control_id=self.control_id
        )
        
        # Assemble the complete prompt
        complete_prompt = f"""
You are a cybersecurity compliance expert. Generate a complete checks.yaml entry for automated compliance validation.
{control_info}
{instructions}
{resource_schema}
{sample_format}
{self.GUIDELINES}"""
        
        return complete_prompt
    
    def process_response(self, response: LLMResponse) -> Check:
        """
        Process checks YAML response and validate it.
        
        Args:
            response: LLM response object
            
        Returns:
            Validated Check object
        """
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        content = re.sub(r'```yaml\s*\n?', '', content)
        content = re.sub(r'```\s*$', '', content, flags=re.MULTILINE)
        
        # Remove any leading/trailing whitespace
        content = content.strip()
        
        # Ensure proper YAML structure
        if not content.startswith('checks:'):
            if content.startswith('- '):
                content = 'checks:\n' + content
            else:
                content = 'checks:\n- ' + content

        # Parse YAML and validate
        yaml_data = yaml.safe_load(content)
        checks = yaml_data['checks']
        # We expect a single check
        if len(checks) != 1:
            raise ValueError(f"Expected 1 check, got {len(checks)}")
        check_dict = checks[0]
        check_dict['resource_type'] = self.resource_type
        check_dict['id'] = check_dict['name']

        return Check(**check_dict)


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


def generate_checks_yaml(
    control_name: str,
    control_text: str,
    control_id: int,
    control_title: str,
    resource_type: Type[Resource],
    **kwargs
) -> Check:
    """
    Quick function to generate complete checks.yaml entry.
    
    Args:
        control_name: Control identifier
        control_text: Control requirement text
        control_title: Control title/name
        resource_type: Target resource type class
        control_id: Database ID of the control
        **kwargs: Additional LLM parameters
        
    Returns:
        Generated and validated Check object
    """
    prompt = ChecksYamlPrompt(
        control_name=control_name,
        control_text=control_text,
        control_title=control_title,
        resource_type=resource_type,
        control_id=control_id,
    )
    return prompt.generate(**kwargs)
