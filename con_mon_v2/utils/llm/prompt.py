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
from typing import Dict, Any, List, Type, Optional
from datetime import datetime
from abc import ABC, abstractmethod

from con_mon_v2.compliance.models import (
    Check, 
    CheckMetadata, 
    CheckOperation, 
    OutputStatements, 
    FixDetails, 
    ComparisonOperationEnum,
    CheckResult
)
from con_mon_v2.connectors.models import ConnectorType
from con_mon_v2.resources import Resource
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
        
        # Core prompt template with extensive guidance
        prompt_template = """You are a cybersecurity compliance expert creating automated compliance checks for NIST 800-53 controls.

**CRITICAL UNDERSTANDING: CHECKS ARE PER INDIVIDUAL RESOURCE**
- Each check validates ONE resource instance at a time
- The fetched_value contains data from a SINGLE resource
- Logic should determine if THIS ONE resource is compliant
- Do NOT try to aggregate or compare across multiple resources

**Control Information:**
- Control ID: {control_name}
- Control Title: {control_title}
- Provider: {provider_name} ({connector_type})
- Resource Type: {resource_model_name}

**Control Requirement:**
{control_text}

**CONTROL TYPE GUIDANCE:**

**POLICY CONTROLS (AC-1, AT-1, AU-1, etc. - ending in "-1"):**
For technical resources, look for configuration that enforces policy requirements.

**ACCESS CONTROL CONTROLS (AC-2, AC-3, AC-4, etc.):**
Focus on authentication, authorization, and access management settings.

**AUDIT CONTROLS (AU-2, AU-3, AU-4, etc.):**
Focus on logging, monitoring, and audit capabilities.

**FIELD PATH SELECTION:**
1. For GitHub Resources: Look for security settings, branch protection, access controls
2. For AWS Resources: Look for security configurations, IAM settings, logging, monitoring
3. Choose paths that contain security-relevant data for the specific control

{resource_schema}

**Available Operations:** {available_operations}

**Field Path Examples for {resource_model_name}:**
{field_path_examples_formatted}

**VALIDATION LOGIC REQUIREMENTS:**
1. Validate THIS ONE resource instance (not multiple resources)
2. Handle edge cases: None, empty lists, missing fields
3. Set result = True for compliance, result = False for non-compliance
4. Use fetched_value variable to access field data
5. Implement meaningful compliance checks (not just existence checks)

**YAML SCHEMA TO FOLLOW:**
```yaml
checks:
- id: "{check_id}"
  name: "{check_name}"
  description: "{check_description}"
  category: "{suggested_category}"
  output_statements:
    success: "Resource is compliant with {control_name}"
    failure: "Resource is not compliant with {control_name}"
    partial: "Resource partially complies with {control_name}"
  fix_details:
    description: "Configure the resource to meet {control_name} requirements"
    instructions:
    - "Review the {control_name} control requirements"
    - "Update resource configuration to implement required security controls"
    estimated_time: "{estimated_time}"
    automation_available: false
  created_by: "system"
  updated_by: "system"
  is_deleted: false
  metadata:
    resource_type: "{resource_type_full_path}"
    field_path: "[CHOOSE APPROPRIATE PATH FROM EXAMPLES ABOVE]"
    operation:
      name: "custom"
      logic: |
        result = False
        
        # Validate THIS ONE resource for compliance
        if fetched_value is None:
            result = False
        elif not fetched_value:
            result = False
        else:
            # Implement specific compliance logic here
            # Example - customize for actual control requirements:
            if isinstance(fetched_value, dict):
                # Check multiple compliance criteria
                condition1 = fetched_value.get('security_setting1', False)
                condition2 = fetched_value.get('security_setting2') is not None
                if condition1 and condition2:
                    result = True
            elif isinstance(fetched_value, list):
                # Check if any items meet criteria
                for item in fetched_value:
                    if isinstance(item, dict) and item.get('enabled', False):
                        result = True
                        break
    expected_value: null
    tags: {tags}
    severity: "{suggested_severity}"
    category: "{suggested_category}"
```

**REQUIREMENTS:**
- Generate ONLY the YAML check entry
- No explanations, no markdown code blocks, no additional text
- Implement complete custom logic (no TODO comments)
- Choose field paths that contain relevant data for this control

Generate the complete YAML check entry now:"""

        # Format field path examples
        field_paths_formatted = '\n'.join([f"- {path}" for path in self.template_vars['field_path_examples']])
        
        # Format the complete prompt
        resource_schema = self.get_resource_schema_section()
        
        return prompt_template.format(
            resource_schema=resource_schema,
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
        
        # Debug: Save the prompt to a file
        import os
        debug_dir = "debug_prompts"
        os.makedirs(debug_dir, exist_ok=True)
        
        with open(f"{debug_dir}/standard_prompt.txt", "w") as f:
            f.write("="*80 + "\n")
            f.write("🤖 SENDING PROMPT TO LLM (CheckPrompt)\n")
            f.write("="*80 + "\n")
            f.write(prompt)
            f.write("\n" + "="*80 + "\n")
            f.write("END PROMPT\n")
            f.write("="*80 + "\n")
        
        print(f"📝 Standard prompt saved to {debug_dir}/standard_prompt.txt")
        
        # Generate response using LLM
        client = get_llm_client()
        request = LLMRequest(prompt=prompt)
        response = client.generate_response(request)
        
        # Debug: Save the LLM response to a file
        with open(f"{debug_dir}/standard_response.txt", "w") as f:
            f.write("="*80 + "\n")
            f.write("🤖 LLM RESPONSE (CheckPrompt)\n")
            f.write("="*80 + "\n")
            f.write(response.content)
            f.write("\n" + "="*80 + "\n")
            f.write("END RESPONSE\n")
            f.write("="*80 + "\n")
        
        print(f"📝 Standard response saved to {debug_dir}/standard_response.txt")
        
        # Process and return the LLM response
        return self.process_response(response)


class CheckPromptWithResults(CheckPrompt):
    """
    Enhanced prompt that includes previous check results and errors to help LLM generate better checks.
    This version learns from failed attempts to create more appropriate field paths and logic.
    """
    
    def __init__(
        self,
        control_name: str,
        control_text: str,
        control_title: str,
        control_id: int,
        connector_type: ConnectorType,
        resource_model_name: str,
        check_results: List[CheckResult],
        suggested_severity: Optional[str] = None,
        suggested_category: Optional[str] = None,
    ):
        # Initialize parent class
        super().__init__(
            control_name=control_name,
            control_text=control_text,
            control_title=control_title,
            control_id=control_id,
            connector_type=connector_type,
            resource_model_name=resource_model_name,
            suggested_severity=suggested_severity,
            suggested_category=suggested_category,
        )
        
        self.check_results = check_results
        
        # Override template variables to include results analysis
        self.template_vars = self._generate_template_variables_with_results()
    
    def _generate_template_variables_with_results(self) -> Dict[str, Any]:
        """Generate template variables including analysis of previous check results"""
        # Start with base template variables
        template_vars = super()._generate_template_variables()
        
        # Add results analysis
        template_vars.update({
            'previous_results_analysis': self._analyze_previous_results(),
            'failed_field_paths': self._get_failed_field_paths(),
            'actual_data_examples': self._get_actual_data_examples(),
            'improvement_suggestions': self._get_improvement_suggestions()
        })
        
        return template_vars
    
    def _analyze_previous_results(self) -> str:
        """Analyze previous check results to understand what went wrong"""
        if not self.check_results:
            return "No previous results available."
        
        analysis = []
        analysis.append("**Previous Check Results Analysis:**")
        
        total_results = len(self.check_results)
        failed_results = [r for r in self.check_results if not r.passed]
        passed_results = [r for r in self.check_results if r.passed]
        
        analysis.append(f"- Total resources tested: {total_results}")
        analysis.append(f"- Failed: {len(failed_results)}")
        analysis.append(f"- Passed: {len(passed_results)}")
        
        if failed_results:
            analysis.append("\n**Common Failure Patterns:**")
            
            # Analyze field paths that failed
            field_paths = set()
            for result in failed_results:
                if hasattr(result.check, 'field_path'):
                    field_paths.add(result.check.field_path)
            
            if field_paths:
                analysis.append(f"- Field paths that failed: {', '.join(field_paths)}")
            
            # Analyze errors
            errors = [r.error for r in failed_results if r.error]
            if errors:
                analysis.append("- Common errors:")
                for error in errors[:3]:  # Show first 3 errors
                    analysis.append(f"  * {error}")
        
        return "\n".join(analysis)
    
    def _get_failed_field_paths(self) -> List[str]:
        """Get list of field paths that failed in previous attempts"""
        failed_paths = set()
        for result in self.check_results:
            if not result.passed and hasattr(result.check, 'field_path'):
                failed_paths.add(result.check.field_path)
        return list(failed_paths)
    
    def _get_actual_data_examples(self) -> str:
        """Get examples of actual data found in resources to guide field selection"""
        if not self.check_results:
            return "No data examples available."
        
        examples = []
        examples.append("**Actual Data Found in Resources:**")
        
        # Group by resource type and show actual values
        resource_data = {}
        for result in self.check_results:
            resource_type = result.resource.__class__.__name__
            if resource_type not in resource_data:
                resource_data[resource_type] = []
            
            # Extract actual value from message if available
            if "Actual:" in result.message:
                actual_value = result.message.split("Actual: ")[-1]
                field_path = getattr(result.check, 'field_path', 'unknown')
                resource_data[resource_type].append(f"{field_path} = {actual_value}")
        
        for resource_type, data_points in resource_data.items():
            examples.append(f"\n{resource_type}:")
            for data_point in data_points[:5]:  # Show first 5 examples
                examples.append(f"  - {data_point}")
        
        return "\n".join(examples)
    
    def _get_improvement_suggestions(self) -> str:
        """Generate suggestions for improving the check based on failures"""
        suggestions = []
        suggestions.append("**Improvement Suggestions:**")
        
        failed_paths = self._get_failed_field_paths()
        if failed_paths:
            suggestions.append("- AVOID these field paths that failed previously:")
            for path in failed_paths:
                suggestions.append(f"  * {path}")

        suggestions.append("- Choose field paths that contain RELEVANT data for the control requirement")
        suggestions.append("- Ensure custom logic checks for meaningful compliance indicators")
        
        return "\n".join(suggestions)
    
    def format_prompt(self, **kwargs) -> str:
        """Format the enhanced prompt with previous results analysis"""
        
        # Enhanced prompt template that includes results analysis
        enhanced_prompt_template = """You are a cybersecurity compliance expert creating automated compliance checks for NIST 800-53 controls.

**CRITICAL UNDERSTANDING: CHECKS ARE PER INDIVIDUAL RESOURCE**
- Each check validates ONE resource instance at a time
- The fetched_value contains data from a SINGLE resource
- Logic should determine if THIS ONE resource is compliant
- Do NOT try to aggregate or compare across multiple resources

IMPORTANT: Learn from the previous failed attempts shown below to create a BETTER check.

{previous_results_analysis}

{actual_data_examples}

{improvement_suggestions}

**Control Information:**
- Control ID: {control_name}
- Control Title: {control_title}
- Provider: {provider_name} ({connector_type})
- Resource Type: {resource_model_name}

**Control Requirement:**
{control_text}

**FIELD PATH SELECTION STRATEGY:**
1. For GitHub Resources: Look for security settings, branch protection, access controls
2. For AWS Resources: Look for security configurations, IAM settings, logging, monitoring
3. AVOID generic metadata unless it directly relates to the control
4. CHOOSE paths that contain security-relevant data for the specific control family
5. LEARN FROM FAILURES: Avoid field paths that failed in previous attempts (shown above)

{resource_schema}

**Available Operations:** {available_operations}

**Field Path Examples for {resource_model_name}:**
{field_path_examples_formatted}

**VALIDATION LOGIC REQUIREMENTS:**
1. Validate THIS ONE resource instance (not multiple resources)
2. Handle edge cases: None, empty lists, missing fields
3. Set result = True for compliance, result = False for non-compliance
4. Use fetched_value variable to access field data
5. LEARN from the failed attempts shown above to choose better validation criteria

**YAML SCHEMA TO FOLLOW:**
```yaml
checks:
- id: "{check_id}"
  name: "{check_name}"
  description: "{check_description}"
  category: "{suggested_category}"
  output_statements:
    success: "Resource is compliant with {control_name}"
    failure: "Resource is not compliant with {control_name}"
    partial: "Resource partially complies with {control_name}"
  fix_details:
    description: "Configure the resource to meet {control_name} requirements based on analysis of failures"
    instructions:
    - "Review the {control_name} control requirements and previous failure patterns"
    - "Update resource configuration to implement required security controls"
    - "Focus on areas identified as problematic in previous attempts"
    estimated_time: "{estimated_time}"
    automation_available: false
  created_by: "system"
  updated_by: "system"
  is_deleted: false
  metadata:
    resource_type: "{resource_type_full_path}"
    field_path: "[CHOOSE BETTER PATH BASED ON ANALYSIS ABOVE - AVOID FAILED PATHS]"
    operation:
      name: "custom"
      logic: |
        result = False
        
        # Validate THIS ONE resource for compliance
        # LEARN FROM PREVIOUS FAILURES - create logic that works with actual data
        
        if fetched_value is None:
            result = False
        elif not fetched_value:
            result = False
        else:
            # Implement specific compliance logic based on control requirements
            # Use insights from previous failures to create better validation
            
            if isinstance(fetched_value, dict):
                # For dict data, check multiple compliance criteria
                # Customize these based on actual control requirements and failed attempts
                condition1 = fetched_value.get('security_setting1', False)
                condition2 = fetched_value.get('security_setting2') is not None
                
                if condition1 and condition2:
                    result = True
                    
            elif isinstance(fetched_value, list):
                # For list data, check if any/all items meet criteria
                for item in fetched_value:
                    if isinstance(item, dict) and item.get('enabled', False):
                        result = True
                        break
    expected_value: null
    tags: {tags}
    severity: "{suggested_severity}"
    category: "{suggested_category}"
```

**REQUIREMENTS:**
- Generate ONLY the YAML check entry
- No explanations, no markdown code blocks, no additional text
- LEARN from the previous failures shown above to choose better field paths and logic
- Choose field paths that contain data relevant to the specific control
- Implement complete custom logic (no TODO comments)

Generate the complete YAML check entry now:"""

        # Format field path examples
        field_paths_formatted = '\n'.join([f"- {path}" for path in self.template_vars['field_path_examples']])
        
        # Format the complete enhanced prompt
        return enhanced_prompt_template.format(
            resource_schema=self.get_resource_schema_section(),
            field_path_examples_formatted=field_paths_formatted,
            **self.template_vars
        )
    
    def generate(self, **kwargs) -> Check:
        """Generate a complete Check object using LLM with enhanced prompt"""
        # Format prompt
        prompt = self.format_prompt(**kwargs)
        
        # Debug: Save the enhanced prompt to a file
        import os
        debug_dir = "debug_prompts"
        os.makedirs(debug_dir, exist_ok=True)
        
        with open(f"{debug_dir}/enhanced_prompt.txt", "w") as f:
            f.write("="*80 + "\n")
            f.write(f"🧠 SENDING ENHANCED PROMPT TO LLM (CheckPromptWithResults)\n")
            f.write(f"📊 Learning from {len(self.check_results)} previous results\n")
            f.write("="*80 + "\n")
            f.write(prompt)
            f.write("\n" + "="*80 + "\n")
            f.write("END ENHANCED PROMPT\n")
            f.write("="*80 + "\n")
        
        print(f"📝 Enhanced prompt saved to {debug_dir}/enhanced_prompt.txt (learning from {len(self.check_results)} results)")
        
        # Generate response using LLM
        client = get_llm_client()
        request = LLMRequest(prompt=prompt)
        response = client.generate_response(request)
        
        # Debug: Save the LLM response to a file
        with open(f"{debug_dir}/enhanced_response.txt", "w") as f:
            f.write("="*80 + "\n")
            f.write("🧠 LLM RESPONSE (CheckPromptWithResults)\n")
            f.write("="*80 + "\n")
            f.write(response.content)
            f.write("\n" + "="*80 + "\n")
            f.write("END ENHANCED RESPONSE\n")
            f.write("="*80 + "\n")
        
        print(f"📝 Enhanced response saved to {debug_dir}/enhanced_response.txt")
        
        # Process and return the LLM response
        return self.process_response(response)
