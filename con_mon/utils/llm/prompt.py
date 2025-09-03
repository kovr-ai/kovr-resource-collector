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
import json
from typing import Dict, Any, List, Type, Optional
from datetime import datetime
from abc import ABC, abstractmethod
from functools import lru_cache

from con_mon.compliance.models import (
    Check, 
    CheckMetadata, 
    CheckOperation, 
    OutputStatements, 
    FixDetails, 
    ComparisonOperationEnum,
    CheckResult
)
from con_mon.connectors.models import ConnectorType
from con_mon.resources import Resource, ResourceCollection
from .client import get_llm_client, LLMRequest, LLMResponse


# Pydantic models for preprocessing guidance
from pydantic import BaseModel, Field
from enum import Enum

class ControlCategory(str, Enum):
    """Categories of NIST 800-53 controls"""
    POLICY = "policy"
    TECHNICAL = "technical" 
    OPERATIONAL = "operational"
    HYBRID = "hybrid"

class RiskLevel(str, Enum):
    """Risk levels for compliance validation"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ControlGuidance(BaseModel):
    """Preprocessed guidance for a specific NIST control"""
    control_name: str
    control_category: ControlCategory
    key_compliance_indicators: List[str] = Field(description="What to look for to determine compliance")
    implementation_patterns: List[str] = Field(description="Common ways this control is implemented")
    risk_areas: List[str] = Field(description="High-risk areas to focus validation on")
    validation_approach: str = Field(description="How to approach validating this control")
    
class ResourceGuidance(BaseModel):
    """Resource-specific guidance for implementing a control"""
    resource_model_name: str
    provider: str
    relevant_field_paths: List[str] = Field(description="Most relevant field paths for this control")
    expected_data_patterns: Dict[str, Any] = Field(description="Expected data patterns for compliance")
    compliance_indicators: List[str] = Field(description="Specific indicators of compliance in this resource")
    non_compliance_indicators: List[str] = Field(description="Specific indicators of non-compliance")
    edge_cases: List[str] = Field(description="Edge cases to handle in validation logic")
    suggested_field_path: str = Field(description="Best field path to use for this control-resource combination")

class EnhancedGuidance(BaseModel):
    """Combined control and resource guidance"""
    control_guidance: ControlGuidance
    resource_guidance: ResourceGuidance
    specific_instructions: str = Field(description="Specific instructions for this control-resource combination")
    validation_logic_hints: List[str] = Field(description="Hints for implementing the validation logic")


# Preprocessing functions for dynamic guidance generation
@lru_cache(maxsize=500)
def generate_control_guidance(control_name: str, control_text: str, control_title: str) -> ControlGuidance:
    """
    Generate control-specific guidance using LLM preprocessing.
    Cached to avoid repeated calls for the same control.
    """
    prompt = f"""You are a NIST 800-53 cybersecurity expert. Analyze this control and provide structured guidance.

Control: {control_name} - {control_title}
Control Text: {control_text}

Provide a JSON response with this exact structure:
{{
    "control_name": "{control_name}",
    "control_category": "policy|technical|operational|hybrid",
    "key_compliance_indicators": ["indicator1", "indicator2", "..."],
    "implementation_patterns": ["pattern1", "pattern2", "..."],
    "risk_areas": ["risk1", "risk2", "..."],
    "validation_approach": "detailed approach description"
}}

Guidelines:
- control_category: "policy" for procedures/documentation, "technical" for system configurations, "operational" for processes, "hybrid" for mixed
- key_compliance_indicators: What evidence shows this control is implemented
- implementation_patterns: Common ways organizations implement this control
- risk_areas: What could go wrong or be misconfigured
- validation_approach: How to verify compliance programmatically

Generate ONLY valid JSON, no explanations."""

    try:
        client = get_llm_client()
        request = LLMRequest(prompt=prompt)
        response = client.generate_response(request)
        
        # Parse JSON response
        guidance_data = json.loads(response.content.strip())
        return ControlGuidance(**guidance_data)
        
    except Exception as e:
        print(f"⚠️  Failed to generate control guidance for {control_name}: {e}")
        # Fallback to basic guidance
        return ControlGuidance(
            control_name=control_name,
            control_category=ControlCategory.TECHNICAL,
            key_compliance_indicators=["Configuration exists", "Settings are secure"],
            implementation_patterns=["Standard configuration", "Security hardening"],
            risk_areas=["Misconfiguration", "Default settings"],
            validation_approach="Check for secure configuration settings"
        )

@lru_cache(maxsize=1000)
def generate_resource_guidance(
    control_guidance_json: str,  # JSON string for caching
    resource_model_name: str,
    provider: str,
    resource_schema_json: str,  # JSON string for caching
    field_paths: tuple  # Tuple for caching
) -> ResourceGuidance:
    """
    Generate resource-specific guidance for implementing a control.
    Uses JSON strings and tuples for caching compatibility.
    """
    control_guidance = ControlGuidance.parse_raw(control_guidance_json)
    resource_schema = json.loads(resource_schema_json)
    
    prompt = f"""You are a cloud security expert. Map this NIST control to specific resource capabilities.

Control Guidance:
- Control: {control_guidance.control_name}
- Category: {control_guidance.control_category}
- Key Indicators: {', '.join(control_guidance.key_compliance_indicators)}
- Validation Approach: {control_guidance.validation_approach}

Resource Information:
- Provider: {provider}
- Resource Type: {resource_model_name}
- Available Field Paths: {', '.join(field_paths)}

Resource Schema (first 1000 chars): {str(resource_schema)[:1000]}...

Provide a JSON response with this exact structure:
{{
    "resource_model_name": "{resource_model_name}",
    "provider": "{provider}",
    "relevant_field_paths": ["path1", "path2", "..."],
    "expected_data_patterns": {{"field": "expected_pattern"}},
    "compliance_indicators": ["indicator1", "indicator2", "..."],
    "non_compliance_indicators": ["problem1", "problem2", "..."],
    "edge_cases": ["edge_case1", "edge_case2", "..."],
    "suggested_field_path": "best_field_path_for_this_control"
}}

Guidelines:
- relevant_field_paths: Choose 3-5 most relevant paths from available field paths
- expected_data_patterns: What values/structures indicate compliance
- compliance_indicators: Specific data patterns that show compliance
- non_compliance_indicators: Specific data patterns that show problems
- edge_cases: Null values, empty lists, missing fields to handle
- suggested_field_path: Single best field path for this control validation

Generate ONLY valid JSON, no explanations."""

    try:
        client = get_llm_client()
        request = LLMRequest(prompt=prompt)
        response = client.generate_response(request)
        
        # Parse JSON response
        guidance_data = json.loads(response.content.strip())
        return ResourceGuidance(**guidance_data)
        
    except Exception as e:
        print(f"⚠️  Failed to generate resource guidance for {resource_model_name}: {e}")
        # Fallback to basic guidance
        return ResourceGuidance(
            resource_model_name=resource_model_name,
            provider=provider,
            relevant_field_paths=list(field_paths)[:3],
            expected_data_patterns={"enabled": True, "configured": True},
            compliance_indicators=["Feature is enabled", "Security settings configured"],
            non_compliance_indicators=["Feature disabled", "Default configuration"],
            edge_cases=["Null values", "Empty configurations"],
            suggested_field_path=field_paths[0] if field_paths else "id"
        )

def generate_enhanced_guidance(
    control_name: str,
    control_text: str, 
    control_title: str,
    resource_model_name: str,
    provider: str,
    resource_schema: Dict[str, Any],
    field_paths: List[str]
) -> EnhancedGuidance:
    """
    Generate complete enhanced guidance combining control and resource analysis.
    """
    # Step 1: Get control-specific guidance
    control_guidance = generate_control_guidance(control_name, control_text, control_title)
    
    # Step 2: Get resource-specific guidance (using JSON/tuple for caching)
    resource_guidance = generate_resource_guidance(
        control_guidance.json(),
        resource_model_name,
        provider,
        json.dumps(resource_schema),
        tuple(field_paths)
    )
    
    # Step 3: Combine into specific instructions
    specific_instructions = f"""
For {control_name} on {provider} {resource_model_name}:
- Focus on: {', '.join(control_guidance.key_compliance_indicators)}
- Check field: {resource_guidance.suggested_field_path}
- Look for: {', '.join(resource_guidance.compliance_indicators)}
- Avoid: {', '.join(resource_guidance.non_compliance_indicators)}
"""
    
    validation_hints = [
        f"Use field path: {resource_guidance.suggested_field_path}",
        f"Control category: {control_guidance.control_category}",
        f"Expected patterns: {resource_guidance.expected_data_patterns}",
        f"Handle edge cases: {', '.join(resource_guidance.edge_cases)}"
    ]
    
    return EnhancedGuidance(
        control_guidance=control_guidance,
        resource_guidance=resource_guidance,
        specific_instructions=specific_instructions.strip(),
        validation_logic_hints=validation_hints
    )


class ProviderConfig:
    """Configuration for provider-specific data"""
    
    def __init__(self, connector_type: ConnectorType):
        self.connector_type = connector_type
        self.provider_name = connector_type.value
        self.resources: List[Type[Resource]] = list()
        self.resource_collection: ResourceCollection = None
        self.resource_wise_field_paths: Dict[Resource, List[str]] = dict()
        self.load_provider_data()
    
    def load_provider_data(self):
        """Load provider-specific resource schemas and configurations"""
        # Load resource schemas
        current_dir = os.path.dirname(os.path.abspath(__file__))
        resources_yaml_path = os.path.join(current_dir, '..', '..', 'resources', 'resources.yaml')

        with open(resources_yaml_path, 'r') as f:
            resources_data = yaml.safe_load(f)

        provider_data = resources_data[self.provider_name]

        # Generate field path examples for each resource
        for resource_name, schema in provider_data['resources'].items():
            # Dynamically import and get the resource class
            resource_model = self._get_resource_class(resource_name)
            self.resources.append(resource_model)
            self.resource_wise_field_paths[resource_name] = resource_model.field_paths(
                max_depth=10,
                short_list=True,
            )

    def _get_resource_class(self, resource_name: str) -> Optional[Type[Resource]]:
        """Dynamically import and return the Resource class for a given resource name."""
        try:
            # Construct the full module path
            module_path = f"con_mon.mappings.{self.provider_name}"
            # Import the module and get the class
            module = __import__(module_path, fromlist=[resource_name])
            resource_class = getattr(module, resource_name)
            
            # Verify it's a Resource subclass
            if issubclass(resource_class, Resource):
                return resource_class
            else:
                print(f"⚠️ {resource_name} is not a Resource subclass")
                return None
                
        except ImportError:
            print(f"⚠️ Resource class not found for {resource_name} in {self.provider_name}")
            return None
        except AttributeError:
            print(f"⚠️ Class {resource_name} not found in module {module_path}")
            return None
        except Exception as e:
            print(f"⚠️ Error loading resource class for {resource_name}: {e}")
            return None

    def _extract_basic_field_paths(self, schema: Dict[str, Any], prefix: str = "") -> List[str]:
        """Extract basic field paths from a resource schema for fallback."""
        field_paths = []
        
        for key, value in schema.items():
            current_path = f"{prefix}.{key}" if prefix else key
            field_paths.append(current_path)
            
            if isinstance(value, dict):
                # Recursively extract nested field paths
                nested_paths = self._extract_basic_field_paths(value, current_path)
                field_paths.extend(nested_paths)
                
            elif isinstance(value, list) and value:
                # For arrays, add wildcard patterns
                field_paths.extend([
                    f"{current_path}[*]",
                    f"{current_path}[]",
                    f"{current_path}.*"
                ])
                
                # If the first item is a dict, extract its paths with wildcards
                if isinstance(value[0], dict):
                    nested_paths = self._extract_basic_field_paths(value[0], current_path)
                    for nested_path in nested_paths:
                        if nested_path.startswith(current_path):
                            # Add wildcard versions
                            field_paths.extend([
                                nested_path.replace(current_path, f"{current_path}[*]", 1),
                                nested_path.replace(current_path, f"{current_path}[]", 1),
                                nested_path.replace(current_path, f"{current_path}.*", 1)
                            ])
        
        return field_paths


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
        
        # Generate enhanced guidance using preprocessing LLM
        print(f"🧠 Generating enhanced guidance for {control_name} + {resource_model_name}...")
        self.enhanced_guidance = generate_enhanced_guidance(
            control_name=control_name,
            control_text=control_text,
            control_title=control_title,
            resource_model_name=resource_model_name,
            provider=connector_type.value,
            resource_schema=self.provider_config.resources.get(resource_model_name, {}),
            field_paths=self.provider_config.field_path_examples.get(resource_model_name, [])
        )
        
        # Generate template variables
        self.template_vars = self._generate_template_variables()
    
    def _generate_template_variables(self) -> Dict[str, Any]:
        """Generate all template variables needed for the prompt"""
        
        # Control-based variables
        control_name_clean = self.control_name.lower().replace('-', '_').replace('.', '_')
        resource_name_clean = self.resource_model_name.lower().replace('resource', '')
        
        # Extract control family for tags
        control_family = self.control_name.split('-')[0] if '-' in self.control_name else self.control_name[:2]
        
        # Base template variables
        base_vars = {
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
            'resource_type_full_path': f"con_mon.mappings.{self.provider_config.provider_name}.{self.resource_model_name}",
            
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
        
        # Add enhanced guidance variables
        enhanced_vars = {
            # Control guidance
            'control_category': self.enhanced_guidance.control_guidance.control_category.value,
            'key_compliance_indicators': self.enhanced_guidance.control_guidance.key_compliance_indicators,
            'implementation_patterns': self.enhanced_guidance.control_guidance.implementation_patterns,
            'risk_areas': self.enhanced_guidance.control_guidance.risk_areas,
            'validation_approach': self.enhanced_guidance.control_guidance.validation_approach,
            
            # Resource guidance  
            'relevant_field_paths': self.enhanced_guidance.resource_guidance.relevant_field_paths,
            'expected_data_patterns': self.enhanced_guidance.resource_guidance.expected_data_patterns,
            'compliance_indicators': self.enhanced_guidance.resource_guidance.compliance_indicators,
            'non_compliance_indicators': self.enhanced_guidance.resource_guidance.non_compliance_indicators,
            'edge_cases': self.enhanced_guidance.resource_guidance.edge_cases,
            'suggested_field_path': self.enhanced_guidance.resource_guidance.suggested_field_path,
            
            # Combined guidance
            'specific_instructions': self.enhanced_guidance.specific_instructions,
            'validation_logic_hints': self.enhanced_guidance.validation_logic_hints,
        }
        
        # Merge base and enhanced variables
        return {**base_vars, **enhanced_vars}
    
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

**ENHANCED CONTROL ANALYSIS:**
- Control Category: {control_category}
- Key Compliance Indicators: {key_compliance_indicators}
- Implementation Patterns: {implementation_patterns}
- Risk Areas: {risk_areas}
- Validation Approach: {validation_approach}

**RESOURCE-SPECIFIC GUIDANCE:**
- Suggested Field Path: {suggested_field_path}
- Relevant Field Paths: {relevant_field_paths}
- Compliance Indicators: {compliance_indicators}
- Non-Compliance Indicators: {non_compliance_indicators}
- Edge Cases to Handle: {edge_cases}
- Expected Data Patterns: {expected_data_patterns}

**SPECIFIC INSTRUCTIONS FOR THIS CONTROL-RESOURCE COMBINATION:**
{specific_instructions}

**VALIDATION LOGIC HINTS:**
{validation_logic_hints}

{resource_schema}

**🚨 CRITICAL: FIELD PATH EXTRACTION BEHAVIOR 🚨**

**IMPORTANT:** The field_path extracts ONLY specific data from the resource, NOT the full resource object!

**Example for CloudWatchResource:**

Full Resource Object:
```json
{{
  "id": "cloudwatch-us-west-2",
  "alarms": [
    {{"alarm_name": "HighCPU", "alarm_actions": ["arn:aws:sns:us-west-2:123:alert"]}},
    {{"alarm_name": "LowMemory", "alarm_actions": ["arn:aws:autoscaling:us-west-2:123:policy"]}}
  ],
  "log_groups": [
    {{"log_group_name": "/aws/lambda/func", "metric_filter_count": 2}}
  ]
}}
```

**Field Path Examples and What fetched_value Contains:**

1. `field_path: "alarms[*].alarm_actions"` 
   → `fetched_value = [["arn:aws:sns:us-west-2:123:alert"], ["arn:aws:autoscaling:us-west-2:123:policy"]]`
   → Logic should iterate through this list of alarm_actions arrays

2. `field_path: "alarms[*].alarm_name"`
   → `fetched_value = ["HighCPU", "LowMemory"]`
   → Logic should check this list of alarm names

3. `field_path: "log_groups[*].metric_filter_count"`
   → `fetched_value = [2]`
   → Logic should check this list of counts

4. `field_path: "alarms"`
   → `fetched_value = [{{"alarm_name": "HighCPU", "alarm_actions": [...]}}, {{"alarm_name": "LowMemory", "alarm_actions": [...]}}]`
   → Logic should iterate through this list of alarm objects

**🚨 CRITICAL: PYDANTIC MODEL ACCESS 🚨**

**IMPORTANT:** When field_path extracts nested data, the results may be **Pydantic model objects**, NOT Python dictionaries!

**❌ WRONG - Using dict methods on Pydantic objects:**
```python
# This will FAIL with AttributeError
for statement in fetched_value:
    if statement.get('Effect') == 'Allow':  # ERROR: Pydantic models don't have .get()
        condition = statement.get('Condition')  # ERROR: Use attribute access instead
```

**✅ CORRECT - Using attribute access on Pydantic objects:**
```python
# This works with both dicts AND Pydantic models
for statement in fetched_value:
    if hasattr(statement, 'Effect'):
        effect = statement.Effect
    elif isinstance(statement, dict):
        effect = statement.get('Effect')
    else:
        effect = getattr(statement, 'Effect', None)
    
    if effect == 'Allow':
        # Access nested attributes safely
        condition = getattr(statement, 'Condition', None)
        if condition:
            # Handle condition logic...
```

**✅ BEST PRACTICE - Safe attribute/key access:**
```python
def safe_get(obj, key, default=None):
    \"\"\"Safely get value from dict or Pydantic object\"\"\"
    if hasattr(obj, key):
        return getattr(obj, key, default)
    elif isinstance(obj, dict):
        return obj.get(key, default)
    return default

# Usage:
for statement in fetched_value:
    effect = safe_get(statement, 'Effect')
    if effect == 'Allow':
        condition = safe_get(statement, 'Condition')
        if condition:
            bool_condition = safe_get(condition, 'Bool')
            # etc...
```

**❌ WRONG LOGIC (assumes full resource):**
```python
# This will FAIL because fetched_value is NOT the full resource
for alarm in fetched_value.get('alarms', []):  # ERROR: fetched_value has no 'alarms' key
    if alarm.get('alarm_actions'):
        # ...
```

**✅ CORRECT LOGIC (works with extracted data):**
```python
# For field_path "alarms[*].alarm_actions"
# fetched_value = [["arn:aws:sns:..."], ["arn:aws:autoscaling:..."]]
if isinstance(fetched_value, list):
    for alarm_actions_list in fetched_value:
        if alarm_actions_list:
            for action in alarm_actions_list:
                if action.startswith('arn:aws:sns:'):
                    result = True
                    break
```

**For YOUR field_path "{suggested_field_path}":**
- fetched_value will contain ONLY the data extracted by this path
- Do NOT assume fetched_value has the full resource structure
- Write logic that works with the specific data format returned by this field path

**🚨 CRITICAL: VARIABLE SCOPE IN CUSTOM LOGIC 🚨**

**IMPORTANT:** In your custom logic, you can ONLY use these variables:
- `fetched_value` - the data extracted by the field_path
- `result` - the variable to set (True/False for compliance)

**❌ DO NOT use these variables (they don't exist):**
- `resource` - This variable is NOT available in custom logic scope
- Any other variable names not listed above

**❌ WRONG - Using undefined variables:**
```python
# This will cause NameError - 'resource' is not defined
policy_statements = safe_get(resource, 'policies.*.default_version.Document.Statement')
log_groups = safe_get(resource, 'log_groups', [])
```

**✅ CORRECT - Only use fetched_value:**
```python
# Only use the data extracted by your field_path
if isinstance(fetched_value, list):
    for item in fetched_value:
        # Process the extracted data
        if item and hasattr(item, 'some_attribute'):
            result = True
            break
```

**Available Operations:** {available_operations}

**Field Path Examples for {resource_model_name}:**
{field_path_examples_formatted}

**🚨 CRITICAL: FIELD PATH RESTRICTION 🚨**

**MANDATORY:** You MUST choose your field_path from the list above. DO NOT create custom field paths!

**✅ VALID - Choose from the provided list:**
- Pick ONE field path from the {resource_model_name} list above
- Use the EXACT spelling and format shown
- The path must exist in the list above

**❌ INVALID - Do NOT create custom paths:**
- Do NOT invent new field paths
- Do NOT modify the provided paths
- Do NOT combine multiple paths
- Do NOT use paths not in the list

**Example:**
If the list contains `alarms[*].alarm_actions`, use exactly:
```yaml
field_path: "alarms[*].alarm_actions"
```

**VALIDATION LOGIC REQUIREMENTS:**
1. Validate THIS ONE resource instance (not multiple resources)
2. Handle edge cases: None, empty lists, missing fields
3. Set result = True for compliance, result = False for non-compliance
4. Use fetched_value variable to access field data
5. Implement meaningful compliance checks (not just existence checks)
6. Use the suggested field path: {suggested_field_path}
7. **CRITICAL:** Write logic that works with the extracted data format, NOT the full resource

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
    field_path: "{suggested_field_path}"
    operation:
      name: "custom"
      logic: |
        result = False
        
        # Validate THIS ONE resource for compliance
        # REMEMBER: fetched_value contains ONLY data from field_path "{suggested_field_path}"
        # NOT the full resource object!
        
        if fetched_value is None:
            result = False
        elif not fetched_value:
            result = False
        else:
            # Implement specific compliance logic here based on enhanced guidance
            # Control Category: {control_category}
            # Expected Data Patterns: {expected_data_patterns}
            # Compliance Indicators: {compliance_indicators}
            # Non-Compliance Indicators: {non_compliance_indicators}
            
            # Write logic that works with the extracted data format
            if isinstance(fetched_value, dict):
                # Check multiple compliance criteria based on guidance
                # TODO: Implement based on expected_data_patterns and compliance_indicators
                pass
            elif isinstance(fetched_value, list):
                # Check if any items meet criteria based on guidance
                # TODO: Implement based on expected_data_patterns and compliance_indicators  
                pass
            elif isinstance(fetched_value, (str, bool, int)):
                # Check simple values based on guidance
                # TODO: Implement based on expected_data_patterns and compliance_indicators
                pass
    expected_value: null
    tags: {tags}
    severity: "{suggested_severity}"
    category: "{suggested_category}"
```

**REQUIREMENTS:**
- Generate ONLY the YAML check entry
- No explanations, no markdown code blocks, no additional text
- Implement complete custom logic (no TODO comments)
- Use the suggested field path: {suggested_field_path}
- **CRITICAL:** Write logic that works with extracted data, NOT full resource
- Follow the enhanced guidance provided above

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
        # Clean and extract YAML content
        content = response.content.strip()
        
        # Remove markdown code blocks if present
        if content.startswith('```yaml'):
            content = content[7:]
        elif content.startswith('```'):
            content = content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Clean special characters that break YAML parsing
        char_replacements = {
            # Fix UTF-8 encoding issues
            'â€"': '—',  # Fix mangled em dash
            'â€™': "'",  # Fix mangled right single quotation mark
            'â€œ': '"',  # Fix mangled left double quotation mark
            'â€': '"',  # Fix mangled right double quotation mark
            'â€¢': '•',  # Fix mangled bullet point
            'â€¦': '...',  # Fix mangled ellipsis
            
            # Replace problematic characters with safe alternatives
            '—': '-',    # Em dash to hyphen
            '–': '-',    # En dash to hyphen
            ''': "'",    # Left single quotation mark to straight quote
            ''': "'",    # Right single quotation mark to straight quote
            '"': '"',    # Left double quotation mark to straight quote
            '"': '"',    # Right double quotation mark to straight quote
            '…': '...',  # Horizontal ellipsis to three dots
            '•': '-',    # Bullet point to hyphen
            '™': 'TM',   # Trademark symbol
            '®': '(R)',  # Registered trademark
            '©': '(C)',  # Copyright symbol
            '°': ' degrees',  # Degree symbol
            '±': '+/-',  # Plus-minus sign
            '×': 'x',    # Multiplication sign
            '÷': '/',    # Division sign
        }
        
        # Apply character replacements
        for old_char, new_char in char_replacements.items():
            content = content.replace(old_char, new_char)
        
        # Remove any remaining non-ASCII characters that might cause issues
        # Keep only printable ASCII characters, newlines, and tabs
        import string
        allowed_chars = string.printable
        content = ''.join(char for char in content if char in allowed_chars)
        
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
        row_data['output_statements'] = json.dumps(check_dict['output_statements'])
        row_data['fix_details'] = json.dumps(check_dict['fix_details'])
        row_data['metadata'] = json.dumps(check_dict['metadata'])

        # Create the Check object using from_row (standard pattern)
        check = Check.from_row(row_data)

        # Store raw YAML for debugging
        check._raw_yaml = content
        
        # Store input prompt for debugging (if available)
        if hasattr(self, 'last_generated_prompt'):
            check._input_prompt = self.last_generated_prompt

        return check

    def generate(self, **kwargs) -> Check:
        """Generate a complete Check object using LLM"""
        # Format prompt
        prompt = self.format_prompt(**kwargs)
        
        # Store prompt for later attachment to Check object
        self.last_generated_prompt = prompt

        # Generate response using LLM
        client = get_llm_client()
        request = LLMRequest(prompt=prompt)
        response = client.generate_response(request)

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

**ENHANCED CONTROL ANALYSIS:**
- Control Category: {control_category}
- Key Compliance Indicators: {key_compliance_indicators}
- Implementation Patterns: {implementation_patterns}
- Risk Areas: {risk_areas}
- Validation Approach: {validation_approach}

**RESOURCE-SPECIFIC GUIDANCE:**
- Suggested Field Path: {suggested_field_path}
- Relevant Field Paths: {relevant_field_paths}
- Compliance Indicators: {compliance_indicators}
- Non-Compliance Indicators: {non_compliance_indicators}
- Edge Cases to Handle: {edge_cases}
- Expected Data Patterns: {expected_data_patterns}

**SPECIFIC INSTRUCTIONS FOR THIS CONTROL-RESOURCE COMBINATION:**
{specific_instructions}

**VALIDATION LOGIC HINTS:**
{validation_logic_hints}

**LEARN FROM FAILURES:** Avoid field paths and logic that failed in previous attempts (shown above)

{resource_schema}

**🚨 CRITICAL: FIELD PATH EXTRACTION BEHAVIOR 🚨**

**IMPORTANT:** The field_path extracts ONLY specific data from the resource, NOT the full resource object!

**Example for CloudWatchResource:**

Full Resource Object:
```json
{{
  "id": "cloudwatch-us-west-2",
  "alarms": [
    {{"alarm_name": "HighCPU", "alarm_actions": ["arn:aws:sns:us-west-2:123:alert"]}},
    {{"alarm_name": "LowMemory", "alarm_actions": ["arn:aws:autoscaling:us-west-2:123:policy"]}}
  ],
  "log_groups": [
    {{"log_group_name": "/aws/lambda/func", "metric_filter_count": 2}}
  ]
}}
```

**Field Path Examples and What fetched_value Contains:**

1. `field_path: "alarms[*].alarm_actions"` 
   → `fetched_value = [["arn:aws:sns:us-west-2:123:alert"], ["arn:aws:autoscaling:us-west-2:123:policy"]]`
   → Logic should iterate through this list of alarm_actions arrays

2. `field_path: "alarms[*].alarm_name"`
   → `fetched_value = ["HighCPU", "LowMemory"]`
   → Logic should check this list of alarm names

3. `field_path: "log_groups[*].metric_filter_count"`
   → `fetched_value = [2]`
   → Logic should check this list of counts

4. `field_path: "alarms"`
   → `fetched_value = [{{"alarm_name": "HighCPU", "alarm_actions": [...]}}, {{"alarm_name": "LowMemory", "alarm_actions": [...]}}]`
   → Logic should iterate through this list of alarm objects

**🚨 CRITICAL: PYDANTIC MODEL ACCESS 🚨**

**IMPORTANT:** When field_path extracts nested data, the results may be **Pydantic model objects**, NOT Python dictionaries!

**❌ WRONG - Using dict methods on Pydantic objects:**
```python
# This will FAIL with AttributeError
for statement in fetched_value:
    if statement.get('Effect') == 'Allow':  # ERROR: Pydantic models don't have .get()
        condition = statement.get('Condition')  # ERROR: Use attribute access instead
```

**✅ CORRECT - Using attribute access on Pydantic objects:**
```python
# This works with both dicts AND Pydantic models
for statement in fetched_value:
    if hasattr(statement, 'Effect'):
        effect = statement.Effect
    elif isinstance(statement, dict):
        effect = statement.get('Effect')
    else:
        effect = getattr(statement, 'Effect', None)
    
    if effect == 'Allow':
        # Access nested attributes safely
        condition = getattr(statement, 'Condition', None)
        if condition:
            # Handle condition logic...
```

**✅ BEST PRACTICE - Safe attribute/key access:**
```python
def safe_get(obj, key, default=None):
    \"\"\"Safely get value from dict or Pydantic object\"\"\"
    if hasattr(obj, key):
        return getattr(obj, key, default)
    elif isinstance(obj, dict):
        return obj.get(key, default)
    return default

# Usage:
for statement in fetched_value:
    effect = safe_get(statement, 'Effect')
    if effect == 'Allow':
        condition = safe_get(statement, 'Condition')
        if condition:
            bool_condition = safe_get(condition, 'Bool')
            # etc...
```

**❌ WRONG LOGIC (assumes full resource):**
```python
# This will FAIL because fetched_value is NOT the full resource
for alarm in fetched_value.get('alarms', []):  # ERROR: fetched_value has no 'alarms' key
    if alarm.get('alarm_actions'):
        # ...
```

**✅ CORRECT LOGIC (works with extracted data):**
```python
# For field_path "alarms[*].alarm_actions"
# fetched_value = [["arn:aws:sns:..."], ["arn:aws:autoscaling:..."]]
if isinstance(fetched_value, list):
    for alarm_actions_list in fetched_value:
        if alarm_actions_list:
            for action in alarm_actions_list:
                if action.startswith('arn:aws:sns:'):
                    result = True
                    break
```

**For YOUR field_path "{suggested_field_path}":**
- fetched_value will contain ONLY the data extracted by this path
- Do NOT assume fetched_value has the full resource structure
- Write logic that works with the specific data format returned by this field path

**🚨 CRITICAL: VARIABLE SCOPE IN CUSTOM LOGIC 🚨**

**IMPORTANT:** In your custom logic, you can ONLY use these variables:
- `fetched_value` - the data extracted by the field_path
- `result` - the variable to set (True/False for compliance)

**❌ DO NOT use these variables (they don't exist):**
- `resource` - This variable is NOT available in custom logic scope
- Any other variable names not listed above

**❌ WRONG - Using undefined variables:**
```python
# This will cause NameError - 'resource' is not defined
policy_statements = safe_get(resource, 'policies.*.default_version.Document.Statement')
log_groups = safe_get(resource, 'log_groups', [])
```

**✅ CORRECT - Only use fetched_value:**
```python
# Only use the data extracted by your field_path
if isinstance(fetched_value, list):
    for item in fetched_value:
        # Process the extracted data
        if item and hasattr(item, 'some_attribute'):
            result = True
            break
```

**Available Operations:** {available_operations}

**Field Path Examples for {resource_model_name}:**
{field_path_examples_formatted}

**🚨 CRITICAL: FIELD PATH RESTRICTION 🚨**

**MANDATORY:** You MUST choose your field_path from the list above. DO NOT create custom field paths!

**✅ VALID - Choose from the provided list:**
- Pick ONE field path from the {resource_model_name} list above
- Use the EXACT spelling and format shown
- The path must exist in the list above

**❌ INVALID - Do NOT create custom paths:**
- Do NOT invent new field paths
- Do NOT modify the provided paths
- Do NOT combine multiple paths
- Do NOT use paths not in the list

**Example:**
If the list contains `alarms[*].alarm_actions`, use exactly:
```yaml
field_path: "alarms[*].alarm_actions"
```

**VALIDATION LOGIC REQUIREMENTS:**
1. Validate THIS ONE resource instance (not multiple resources)
2. Handle edge cases: None, empty lists, missing fields
3. Set result = True for compliance, result = False for non-compliance
4. Use fetched_value variable to access field data
5. LEARN from the failed attempts shown above to choose better validation criteria
6. Use the suggested field path: {suggested_field_path} (unless previous failures suggest otherwise)
7. **CRITICAL:** Write logic that works with the extracted data format, NOT the full resource

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
    field_path: "[CHOOSE BETTER PATH BASED ON ANALYSIS ABOVE - PREFER {suggested_field_path}]"
    operation:
      name: "custom"
      logic: |
        result = False
        
        # Validate THIS ONE resource for compliance
        # LEARN FROM PREVIOUS FAILURES - create logic that works with actual data
        # REMEMBER: fetched_value contains ONLY data from field_path, NOT the full resource!
        
        if fetched_value is None:
            result = False
        elif not fetched_value:
            result = False
        else:
            # Implement specific compliance logic based on enhanced guidance and failure analysis
            # Control Category: {control_category}
            # Expected Data Patterns: {expected_data_patterns}
            # Compliance Indicators: {compliance_indicators}
            # Non-Compliance Indicators: {non_compliance_indicators}
            # Use insights from previous failures to create better validation
            
            # Write logic that works with the extracted data format
            if isinstance(fetched_value, dict):
                # For dict data, check multiple compliance criteria
                # Customize these based on actual control requirements and failed attempts
                # TODO: Implement based on enhanced guidance and failure analysis
                pass
                    
            elif isinstance(fetched_value, list):
                # For list data, check if any/all items meet criteria
                # TODO: Implement based on enhanced guidance and failure analysis
                pass
                        
            elif isinstance(fetched_value, (str, bool, int)):
                # For simple values, check if they meet compliance criteria
                # TODO: Implement based on enhanced guidance and failure analysis
                pass
    expected_value: null
    tags: {tags}
    severity: "{suggested_severity}"
    category: "{suggested_category}"
```

**REQUIREMENTS:**
- Generate ONLY the YAML check entry
- No explanations, no markdown code blocks, no additional text
- LEARN from the previous failures shown above to choose better field paths and logic
- Use the enhanced guidance provided above
- Implement complete custom logic (no TODO comments)
- **CRITICAL:** Write logic that works with extracted data, NOT full resource

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
        
        # Store prompt for later attachment to Check object
        self.last_generated_prompt = prompt
        
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
