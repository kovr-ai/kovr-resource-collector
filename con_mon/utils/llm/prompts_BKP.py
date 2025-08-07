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
5.1 field_path can only be one of fields in the selected resource_type
6. Generate Python code for the custom_logic that validates compliance
6.1 the value at resource_type.field_path would be stored in fetched_value
6.2 infer the type of fetched_value using the resources structure below5. Determine the correct field_path for the resource data using the resources structure below
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
- connection_id: {connection_id}
  name: {resource_type_lower}_{control_name_lower}_compliance
  description: Verify compliance with NIST 800-53 {control_name}: {control_title}
  resource_type: # Choose specific resource type (GithubResource, AWSIAMResource, AWSEC2Resource, etc.)
  field_path: # Choose appropriate path from the guidelines above
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

    RESOURCE_SCHEMA = {
        'github': """
**Resource Schema:**
github:
  resources_field_schemas:
    # Nested data type schemas
    RepositoryData:
      name: "repository_data"
      description: "Repository basic information and metadata"
      fields:
        basic_info:
          id: "integer"
          name: "string"
          full_name: "string"
          description: "string"
          private: "boolean"
          owner: "string"
          html_url: "string"
          clone_url: "string"
          ssh_url: "string"
          size: "integer"
          language: "string"
          created_at: "string"
          updated_at: "string"
          pushed_at: "string"
          stargazers_count: "integer"
          watchers_count: "integer"
          forks_count: "integer"
          open_issues_count: "integer"
          archived: "boolean"
          disabled: "boolean"
        metadata:
          default_branch: "string"
          topics: "array"
          has_issues: "boolean"
          has_projects: "boolean"
          has_wiki: "boolean"
          has_pages: "boolean"
          has_downloads: "boolean"
          has_discussions: "boolean"
          is_template: "boolean"
          license: "string"
          visibility: "string"
          allow_forking: "boolean"
          web_commit_signoff_required: "boolean"
        branches:
          type: "array"  # List of branch objects
          structure:
            name: "string"
            sha: "string"
            protected: "boolean"
            protection_details: "object"
        statistics:
          total_commits: "integer"
          contributors_count: "integer"
          languages:
            type: "object"  # Dictionary of language -> bytes
            structure:
              Python: "integer"
              JavaScript: "integer"
              # ... other languages
          code_frequency: "array"

    ActionsData:
      name: "actions_data"
      description: "GitHub Actions workflows and runs"
      fields:
        workflows:
          type: "object"  # Dictionary/map of workflow_id -> workflow_data
          structure:
            id: "integer"
            name: "string"
            path: "string"
            state: "string"
            created_at: "string"
            updated_at: "string"
            url: "string"
            html_url: "string"
            badge_url: "string"
        total_workflows: "integer"
        active_workflows: "integer"
        recent_runs_count: "integer"

    CollaborationData:
      name: "collaboration_data"
      description: "Collaboration information - issues, PRs, collaborators"
      fields:
        issues:
          type: "array"  # List of issue objects
          structure:
            number: "integer"
            title: "string"
            state: "string"
            user: "string"
            created_at: "string"
            updated_at: "string"
            closed_at: "string"
            labels: "array"
            assignees: "array"
            comments_count: "integer"
            is_pull_request: "boolean"
        pull_requests:
          type: "array"  # List of pull request objects
          structure:
            number: "integer"
            title: "string"
            state: "string"
            user: "string"
            created_at: "string"
            updated_at: "string"
            closed_at: "string"
            merged_at: "string"
            base_branch: "string"
        collaborators:
          type: "array"  # List of collaborator objects
          structure:
            login: "string"
            permissions:
              admin: "boolean"
              maintain: "boolean"
              push: "boolean"
              pull: "boolean"
              triage: "boolean"
            role_name: "string"
        total_issues: "integer"
        open_issues: "integer"
        closed_issues: "integer"
        total_pull_requests: "integer"
        open_pull_requests: "integer"
        merged_pull_requests: "integer"
        draft_pull_requests: "integer"
        total_collaborators: "integer"

    SecurityData:
      name: "security_data"
      description: "Security advisories, alerts and analysis"
      fields:
        security_advisories:
          type: "object"
          structure:
            error: "string"  # May contain error message
            advisories: "array"
        vulnerability_alerts:
          type: "object"
          structure:
            enabled: "boolean"
            dependabot_alerts: "array"
            error: "string"
        dependency_graph:
          type: "object"
          structure:
            has_vulnerability_alerts_enabled: "boolean"
            security_and_analysis:
              advanced_security:
                status: "string"
              secret_scanning:
                status: "string"
              secret_scanning_push_protection:
                status: "string"
        security_analysis:
          advanced_security_enabled: "boolean"
          secret_scanning_enabled: "boolean"
          push_protection_enabled: "boolean"
          dependency_review_enabled: "boolean"
        code_scanning_alerts:
          type: "object"
          structure:
            error: "string"
            alerts: "array"
        total_advisories: "integer"
        total_dependabot_alerts: "integer"
        total_code_scanning_alerts: "integer"
        security_features_enabled: "integer"

    OrganizationData:
      name: "organization_data"
      description: "Organization members, teams and collaborators"
      fields:
        members: "array"  # List of member objects (often empty)
        teams: "array"   # List of team objects (often empty)
        outside_collaborators: "array"  # List of collaborator objects (often empty)
        total_members: "integer"
        total_teams: "integer"
        total_outside_collaborators: "integer"
        admin_members: "integer"
        members_error: "string"
        teams_error: "string"
        collaborators_error: "string"

    AdvancedFeaturesData:
      name: "advanced_features_data"
      description: "Advanced GitHub features - tags, webhooks"
      fields:
        tags:
          type: "array"  # List of tag objects
          structure:
            name: "string"
            commit_sha: "string"
            commit_date: "string"
        webhooks: "array"  # List of webhook objects (often empty)
        total_tags: "integer"
        total_webhooks: "integer"
        active_webhooks: "integer"
        tags_error: "string"
        webhooks_error: "string"

  resources:
    # Main resource schemas
    Resource:
      name: "github"
      description: "GitHub repository resource"
      provider: "github"

      # Define the structure that matches GitHub API response with all data types
      fields:
        name: "string"  # Repository name for easy identification
        repository_data: "RepositoryData"  # Nested Pydantic model
        actions_data: "ActionsData"        # Nested Pydantic model
        collaboration_data: "CollaborationData"  # Nested Pydantic model
        security_data: "SecurityData"      # Nested Pydantic model
        organization_data: "OrganizationData"    # Nested Pydantic model
        advanced_features_data: "AdvancedFeaturesData"  # Nested Pydantic model

  ResourceCollection:
    name: "github_collection"
    description: "Collection of GitHub repository resources from a single connector call"
    provider: "github"
    collection_type: "GithubResource"

    # Define the structure for GitHub resource collections
    fields:
      resources:
        - "github.resources.Resource"
      source_connector: "string"
      total_count: "integer"
      fetched_at: "string"
      collection_metadata:
        authenticated_user: "string"
        total_repositories: "integer"
        total_workflows: "integer"
        total_issues: "integer"
        total_pull_requests: "integer"
        total_security_alerts: "integer"
        total_collaborators: "integer"
        total_tags: "integer"
        total_active_webhooks: "integer"
        rate_limit_info: "object"
      github_api_metadata:
        collection_time: "string"
        api_version: "string"
        scope: "array"
        """,
        'aws': """
**Resource Schema:**
aws:
  resources:
    # AWS EC2 Resource Schema
    EC2Resource:
      name: "aws_ec2"
      description: "AWS EC2 service resource"
      provider: "aws"
      service: "ec2"

      fields:
        # Account-level information
        account:
          limits: "object"
          reserved_instances: "array"
          spot_instances: "array"
        # EC2 resources
        instances:
          type: "object"  # Dictionary/map of instance_id -> instance_data
          structure:
            instance_type: "string"
            state: "string"
            launch_time: "string"
            image_id: "string"
            vpc_id: "string"
            subnet_id: "string"
            availability_zone: "string"
            key_name: "string"
            platform: "string"
            monitoring: "string"
            iam_instance_profile: "object"
            ebs_optimized: "boolean"
            instance_lifecycle: "string"
            security_groups: "array"
            network_interfaces: "array"
            block_device_mappings: "array"
        security_groups:
          type: "object"  # Dictionary/map of group_id -> security_group_data
          structure:
            group_name: "string"
            description: "string"
            vpc_id: "string"
            inbound_rules: "array"
            outbound_rules: "array"
            tags: "object"
        vpcs:
          type: "object"  # Dictionary/map of vpc_id -> vpc_data
          structure:
            cidr_block: "string"
            state: "string"
            dhcp_options_id: "string"
            instance_tenancy: "string"
            is_default: "boolean"
            cidr_block_association_set: "array"
            tags: "object"
        subnets: "object"
        route_tables: "object"
        internet_gateways: "object"
        nat_gateways: "object"
        elastic_ips: "object"
        key_pairs: "object"
        volumes: "object"
        snapshots: "object"
        network_interfaces: "object"
        relationships: "object"

    # AWS IAM Resource Schema
    IAMResource:
      name: "aws_iam"
      description: "AWS IAM service resource"
      provider: "aws"
      service: "iam"

      fields:
        # Account-level information
        account: "object"
        # IAM resources
        users:
          type: "object"  # Dictionary/map of user_arn -> user_data
          structure:
            arn: "string"
            user_id: "string"
            create_date: "string"
            path: "string"
            access_keys: "array"
            mfa_devices: "array"
            login_profile: "object"
        groups: "object"  # Dictionary/map structure (if present)
        roles: "object"   # Dictionary/map structure (if present)
        policies:
          type: "object"  # Dictionary/map of policy_arn -> policy_data
          structure:
            policy_name: "string"
            policy_id: "string"
            create_date: "string"
            update_date: "string"
            path: "string"
            default_version_id: "string"
            attachment_count: "integer"
            default_version:
              Document:
                Version: "string"
                Statement: "array"
              VersionId: "string"
              IsDefaultVersion: "boolean"
              CreateDate: "string"
        relationships: "object"

    # AWS S3 Resource Schema
    S3Resource:
      name: "aws_s3"
      description: "AWS S3 service resource"
      provider: "aws"
      service: "s3"

      fields:
        # S3 resources
        buckets:
          type: "object"  # Dictionary/map of bucket_name -> bucket_data
          structure:
            name: "string"
            creation_date: "string"
            region: "string"
            versioning: "object"
            encryption: "object"
            public_access_block: "object"
            logging: "object"
            lifecycle: "object"
            notification: "object"
            tags: "object"
        bucket_policies: "object"
        bucket_encryption: "object"
        bucket_versioning: "object"
        bucket_logging: "object"
        bucket_public_access: "object"
        bucket_lifecycle: "object"
        bucket_notifications: "object"

    # AWS CloudTrail Resource Schema
    CloudTrailResource:
      name: "aws_cloudtrail"
      description: "AWS CloudTrail service resource"
      provider: "aws"
      service: "cloudtrail"

      fields:
        # CloudTrail resources
        trails:
          type: "object"  # Dictionary/map of trail_name -> trail_data
          structure:
            name: "string"
            s3_bucket_name: "string"
            s3_key_prefix: "string"
            include_global_service_events: "boolean"
            is_multi_region_trail: "boolean"
            enable_log_file_validation: "boolean"
            event_selectors: "array"
            insight_selectors: "array"
            is_logging: "boolean"
            kms_key_id: "string"
            tags: "object"
        event_selectors: "object"
        insight_selectors: "object"
        tags: "object"

    # AWS CloudWatch Resource Schema
    CloudWatchResource:
      name: "aws_cloudwatch"
      description: "AWS CloudWatch service resource"
      provider: "aws"
      service: "cloudwatch"

      fields:
        # CloudWatch resources
        log_groups:
          type: "object"  # Dictionary/map of log_group_name -> log_group_data
          structure:
            log_group_name: "string"
            creation_time: "integer"
            retention_in_days: "integer"
            metric_filter_count: "integer"
            arn: "string"
            stored_bytes: "integer"
            kms_key_id: "string"
            tags: "object"
        log_streams: "object"  # Dictionary/map structure
        metrics: 
          type: "array"  # List of metric objects
          structure:
            namespace: "string"
            metric_name: "string"  
            dimensions: "array"
        alarms:
          type: "object"  # Dictionary/map of alarm_name -> alarm_data
          structure:
            alarm_name: "string"
            alarm_description: "string"
            actions_enabled: "boolean"
            ok_actions: "array"
            alarm_actions: "array"
            insufficient_data_actions: "array"
            state_value: "string"
            state_reason: "string"
            state_updated_timestamp: "string"
            metric_name: "string"
            namespace: "string"
            statistic: "string"
            dimensions: "array"
            period: "integer"
            evaluation_periods: "integer"
            threshold: "number"
            comparison_operator: "string"
            tags: "object"
        dashboards:
          type: "object"  # Dictionary/map of dashboard_name -> dashboard_data
          structure:
            dashboard_name: "string"
            dashboard_arn: "string"
            dashboard_body: "string"
            size: "integer"
            last_modified: "string"

  ResourceCollection:
    name: "aws_collection"
    description: "Collection of AWS resources from a single connector call"
    provider: "aws"
    collection_type: "AWSResource"

    # Define the structure for AWS resource collections
    fields:
      resources:
        - "aws.resources.EC2Resource"
        - "aws.resources.IAMResource"
        - "aws.resources.S3Resource"
        - "aws.resources.CloudTrailResource"
        - "aws.resources.CloudWatchResource"
      source_connector: "string"
      total_count: "integer"
      fetched_at: "string"
      collection_metadata:
        account_id: "string"
        regions: "array"
        services_collected: "array"
        collection_errors: "array"
      aws_api_metadata:
        collection_time: "string"
        api_version: "string"
        services: "array"
        regions_scanned: "array"
        """
    }
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

Generate ONLY the YAML check entry, no explanations or additional text:
    """

    TEMPLATE = """You are a cybersecurity compliance expert. Generate a complete checks.yaml entry for automated compliance validation.
"""

    def format_prompt(
        self,
        control_name: str,
        control_text: str,
        control_title: str,
        resource_type: str,
        connection_id: int,
        control_id: int,
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
            **kwargs: Additional parameters

        Returns:
            Formatted prompt string
        """
        # Generate suggestions based on control and resource type
        resource_type_lower = resource_type.lower()
        control_name_lower = control_name.lower().replace('-', '_')

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
            connector_type=resource_type,
            connection_id=connection_id,
            resource_type_lower=resource_type_lower,
            control_name_lower=control_name_lower,
            control_family_tag=control_family.lower(),
            suggested_severity=severity_suggestions.get(control_family, "medium"),
            suggested_category=category_suggestions.get(control_family, "configuration"),
            control_id=control_id
        )
    
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

        # print(f'Content: {content}')
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
    control_id: int,
    control_title: Optional[str] = None,
    resource_type: str = "github",
    connection_id: int = 1,
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
        **kwargs
    )
