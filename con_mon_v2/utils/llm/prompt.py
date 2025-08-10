"""
Prompt V2 - Provider-Agnostic Check Generation

This module provides a new generation of prompts that:
1. Match the Check schema EXACTLY with no deviations
2. Are provider-agnostic (GitHub, AWS, etc.)
3. Include all required enums and model names as template variables
4. Generate perfect YAML that maps 1:1 to the Check model
"""

import os
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime
from abc import ABC

from con_mon_v2.compliance.models import (
    Check,
    ComparisonOperationEnum
)
from con_mon_v2.connectors.models import ConnectorType
from .client import get_llm_client, LLMRequest, LLMResponse


class ProviderConfig:
    """Configuration for provider-specific data"""
    
    def __init__(self, connector_type: ConnectorType):
        self.connector_type = connector_type
        self.provider_name = connector_type.value
        self.load_provider_data()
    
    def load_provider_data(self):
        """Load provider-specific resource schemas and configurations"""
        try:
            # Load resource schemas
            current_dir = os.path.dirname(os.path.abspath(__file__))
            resources_yaml_path = os.path.join(current_dir, '..', '..', 'resources', 'resources.yaml')
            
            with open(resources_yaml_path, 'r') as f:
                resources_data = yaml.safe_load(f)
            
            provider_data = resources_data.get(self.provider_name, {})
            self.resources = provider_data.get('resources', {})
            self.resource_collection = provider_data.get('resource_collection', {})
            
            # Extract resource model names
            self.resource_models = list(self.resources.keys())
            
            # Generate field path examples for each resource
            self.field_path_examples = {}
            for resource_name, schema in self.resources.items():
                self.field_path_examples[resource_name] = self._extract_field_paths(schema, resource_name.lower())
                
        except Exception as e:
            self.resources = {}
            self.resource_collection = {}
            self.resource_models = []
            self.field_path_examples = {}
    
    def _extract_field_paths(self, schema: Dict[str, Any], prefix: str = "") -> List[str]:
        """Extract all possible field paths from a resource schema"""
        paths = []
        
        def extract_paths(obj, current_path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{current_path}.{key}" if current_path else key
                    paths.append(new_path)
                    
                    # Handle arrays
                    if key.endswith('[]'):
                        base_key = key[:-2]
                        new_path = f"{current_path}.{base_key}" if current_path else base_key
                        paths.append(new_path)
                        if isinstance(value, dict):
                            extract_paths(value, new_path)
                    elif isinstance(value, dict):
                        extract_paths(value, new_path)
            elif isinstance(obj, list) and obj:
                if isinstance(obj[0], dict):
                    extract_paths(obj[0], current_path)
        
        extract_paths(schema)
        return paths[:10]  # Return top 10 most relevant paths


class CheckPrompt(ABC):
    """
    This prompt generates YAML that matches the Check model schema exactly,
    with no instructions or comments that don't belong in the final YAML.
    """
    
    def __init__(
        self,
        control_name: str,
        control_text: str,
        control_title: str,
        control_id: int,
        connector_type: ConnectorType,
        resource_model_name: str,
        suggested_severity: Optional[str] = None,
        suggested_category: Optional[str] = None,
    ):
        self.control_name = control_name
        self.control_text = control_text
        self.control_title = control_title
        self.control_id = control_id
        self.connector_type = connector_type
        self.resource_model_name = resource_model_name
        self.suggested_severity = suggested_severity or 'medium'
        self.suggested_category = suggested_category or 'configuration'
        
        # Load provider configuration
        self.provider_config = ProviderConfig(connector_type)
        
        # Generate template variables
        self.template_vars = self._generate_template_variables()
    
    def _generate_template_variables(self) -> Dict[str, Any]:
        """Generate all template variables needed for the prompt"""
        
        # Control-based variables
        control_name_clean = self.control_name.lower().replace('-', '_').replace('.', '_')
        resource_name_clean = self.resource_model_name.lower().replace('resource', '')
        
        # Extract control family for tags
        control_family = self.control_name.split('-')[0] if '-' in self.control_name else self.control_name[:2]
        
        return {
            # Core identifiers
            'check_id': f"{resource_name_clean}_{control_name_clean}_compliance",
            'check_name': f"{resource_name_clean}_{control_name_clean}_compliance",
            'check_description': f"Verify compliance with NIST 800-53 {self.control_name}: {self.control_title}",
            
            # Control information
            'control_name': self.control_name,
            'control_title': self.control_title,
            'control_text': self.control_text,
            'control_id': self.control_id,
            'control_family': control_family.lower(),
            
            # Provider information
            'provider_name': self.provider_config.provider_name,
            'connector_type': self.connector_type.value,
            'resource_model_name': self.resource_model_name,
            'resource_type_full_path': f"con_mon_v2.mappings.{self.provider_config.provider_name}.{self.resource_model_name}",
            
            # Classification (use defaults, can be overridden via parameters)
            'suggested_severity': self.suggested_severity,
            'suggested_category': self.suggested_category,
            'tags': ['compliance', 'nist', control_family.lower(), resource_name_clean],
            
            # Schema information
            'operation_enums': [op.value for op in ComparisonOperationEnum],
            'available_operations': ', '.join([f"'{op.value}'" for op in ComparisonOperationEnum]),
            'resource_models': self.provider_config.resource_models,
            'field_path_examples': self.provider_config.field_path_examples.get(self.resource_model_name, []),
            
            # Timestamps
            'current_timestamp': datetime.now().isoformat(),
            'estimated_time': '2 weeks',
        }
    
    def get_resource_schema_section(self) -> str:
        """Get the resource schema section for the specific provider and resource"""
        if self.resource_model_name in self.provider_config.resources:
            schema = {self.resource_model_name: self.provider_config.resources[self.resource_model_name]}
            schema_yaml = yaml.dump(schema, default_flow_style=False, sort_keys=False)
            return f"**{self.provider_config.provider_name.upper()} {self.resource_model_name} Schema:**\n```yaml\n{schema_yaml}\n```"
        return f"**No schema available for {self.resource_model_name}**"
    
    def format_prompt(self, **kwargs) -> str:
        """Format the complete prompt with all template variables"""
        
        # Core prompt template
        prompt_template = """You are a cybersecurity compliance expert. Generate a YAML check entry that matches the Check model schema EXACTLY.

**Control Information:**
- Control ID: {control_name}
- Control Title: {control_title}
- Provider: {provider_name} ({connector_type})
- Resource Type: {resource_model_name}

**Control Requirement:**
{control_text}

{resource_schema}

**Available Operations:** {available_operations}

**Field Path Examples for {resource_model_name}:**
{field_path_examples_formatted}

**CRITICAL REQUIREMENTS:**
1. Generate YAML that matches the Check model schema EXACTLY
2. Use operation name from: {available_operations}
3. Use full resource type path: {resource_type_full_path}
4. Implement complete custom logic (no TODO comments)
5. Handle all edge cases: None, empty lists, missing fields
6. Set result = True for compliance, result = False for non-compliance
7. Use fetched_value variable to access field data

**EXACT YAML SCHEMA TO FOLLOW:**
```yaml
checks:
- id: "{check_id}"
  name: "{check_name}"
  description: "{check_description}"
  category: "{suggested_category}"
  output_statements:
    success: "Check passed: [specific success message]"
    failure: "Check failed: [specific failure message]"
    partial: "Check partially passed: [specific partial message]"
  fix_details:
    description: "[Specific remediation steps]"
    instructions:
    - "[Step 1 with specific action]"
    - "[Step 2 with specific action]"
    estimated_time: "{estimated_time}"
    automation_available: false
  created_by: "system"
  updated_by: "system"
  is_deleted: false
  metadata:
    resource_type: "{resource_type_full_path}"
    field_path: "[CHOOSE FROM EXAMPLES ABOVE]"
    operation:
      name: "CUSTOM"
      logic: |
        result = False
        
        # Implement complete validation logic here
        # Example structure:
        if fetched_value and isinstance(fetched_value, [EXPECTED_TYPE]):
            # Multiple validation criteria
            condition1 = [validation logic]
            condition2 = [validation logic]
            condition3 = [validation logic]
            
            if condition1 and condition2 and condition3:
                result = True
        elif fetched_value is None:
            result = False
    expected_value: null
    tags: {tags}
    severity: "{suggested_severity}"
    category: "{suggested_category}"
```

Generate ONLY the YAML check entry with complete implementation. No explanations, no additional text, no markdown code blocks."""

        # Format field path examples
        field_paths_formatted = '\n'.join([f"- {path}" for path in self.template_vars['field_path_examples']])
        
        # Format the complete prompt
        return prompt_template.format(
            resource_schema=self.get_resource_schema_section(),
            field_path_examples_formatted=field_paths_formatted,
            **self.template_vars
        )
    
    def process_response(self, response: LLMResponse) -> Check:
        """Process the LLM response and create a validated Check object using from_row"""
        content = response.content.strip()
        
        # Clean up the response
        if content.startswith('```yaml'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Ensure proper YAML structure
        if not content.startswith('checks:'):
            if content.startswith('- '):
                content = 'checks:\n' + content
            else:
                content = 'checks:\n- ' + content

        yaml_data = yaml.safe_load(content)
        checks = yaml_data['checks']
        if len(checks) != 1:
            raise ValueError(f"Expected exactly 1 check, got {len(checks)}")

        check_dict = checks[0]

        # Validate required fields exist
        required_fields = ['id', 'name', 'description', 'category', 'output_statements',
                         'fix_details', 'created_by', 'updated_by', 'is_deleted', 'metadata']

        for field in required_fields:
            if field not in check_dict:
                raise ValueError(f"Missing required field: {field}")

        # Convert nested objects to JSON strings (as they would come from database)
        row_data = {}

        # Copy simple fields directly
        for field in ['id', 'name', 'description', 'category', 'created_by', 'updated_by', 'is_deleted']:
            row_data[field] = check_dict[field]

        # Add timestamps (Check.from_row expects these)
        row_data['created_at'] = datetime.now()
        row_data['updated_at'] = datetime.now()

        # Convert complex fields to JSON strings (simulating database JSONB fields)
        import json
        row_data['output_statements'] = json.dumps(check_dict['output_statements'])
        row_data['fix_details'] = json.dumps(check_dict['fix_details'])
        row_data['metadata'] = json.dumps(check_dict['metadata'])

        # Create the Check object using from_row (standard pattern)
        check = Check.from_row(row_data)

        # Store raw YAML for debugging
        check._raw_yaml = content

        return check

    def generate(self, **kwargs) -> Check:
        """Generate a complete Check object using LLM"""
        # Format prompt
        prompt = self.format_prompt(**kwargs)
        
        # Generate response using LLM
        client = get_llm_client()
        request = LLMRequest(prompt=prompt)
        response = client.generate_response(request)
        
        # Process and return the LLM response
        return self.process_response(response)
