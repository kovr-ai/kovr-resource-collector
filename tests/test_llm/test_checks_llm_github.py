"""
GitHub LLM Checks Test Module

This module tests the ChecksPrompt class with GitHub resources.
It verifies that the prompt generation and processing works correctly
for GitHub-specific compliance checks.
"""

import pytest
from datetime import datetime
from con_mon_v2.utils.llm.prompts import ChecksPrompt
from con_mon_v2.compliance.models import Check, CheckMetadata, OutputStatements, FixDetails, CheckOperation
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.connectors.models import ConnectorType


class TestGitHubChecksPrompt:
    """Test cases for ChecksPrompt class with GitHub resources."""
    
    @pytest.fixture
    def sample_control_data(self):
        """Sample control data for testing."""
        return {
            'control_name': 'AC-2',
            'control_text': '''
            Account Management: The organization:
            a. Identifies and selects the following types of information system accounts to support organizational missions/business functions;
            b. Assigns account managers for information system accounts;
            c. Establishes conditions for group and role membership;
            d. Specifies authorized users of the information system, group and role membership, and access authorizations.
            ''',
            'control_title': 'Account Management',
            'control_id': 1,
            'resource_type': GithubResource,
            'connector_type': ConnectorType.GITHUB
        }
    
    @pytest.fixture
    def github_prompt_instance(self, sample_control_data) -> ChecksPrompt:
        """Create a ChecksPrompt instance for GitHub testing."""
        return ChecksPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_model=sample_control_data['resource_type'],
            connector_type=sample_control_data['connector_type']
        )
    
    def test_github_prompt_initialization(self, sample_control_data):
        """Test that ChecksPrompt initializes correctly for GitHub."""
        prompt = ChecksPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_model=sample_control_data['resource_type'],
            connector_type=sample_control_data['connector_type']
        )
        
        assert prompt.control_name == 'AC-2'
        assert prompt.control_title == 'Account Management'
        assert prompt.resource_model == GithubResource
        assert prompt.connector_type == ConnectorType.GITHUB
        # Test resource_model_lower property derived from resource_model
        assert prompt.resource_model_lower == 'github_resource'
        assert prompt.control_name_lower == 'ac_2'
        assert prompt.control_family == 'AC'
        assert prompt.connector_type_lower == 'github'
    
    def test_github_prompt_formatting(self, github_prompt_instance):
        """Test GitHub prompt formatting."""
        formatted_prompt = github_prompt_instance.format_prompt()
        
        # Check that key GitHub-specific elements are in the prompt
        assert 'AC-2' in formatted_prompt
        assert 'Account Management' in formatted_prompt
        assert 'resource_model' in formatted_prompt
        assert 'field_path' in formatted_prompt
        assert 'custom' in formatted_prompt
        assert 'compliance' in formatted_prompt
        
        # Check for compliance model specific instructions
        assert 'ComparisonOperation' in formatted_prompt
        assert 'metadata' in formatted_prompt
        assert 'connection_id' in formatted_prompt
    
    def test_github_mock_yaml_processing(self, github_prompt_instance):
        """Test processing mock YAML response for GitHub."""
        # Mock YAML content that would come from LLM
        mock_yaml_content = """
checks:
- id: github_resource_ac_2_compliance
  name: github_resource_ac_2_compliance
  description: Verify compliance with NIST 800-53 AC-2 Account Management for GitHub
  category: access_control
  output_statements:
    success: "Check passed: GitHub organization has proper account management"
    failure: "Check failed: GitHub organization lacks proper account management"
    partial: "Check partially passed: Some account management controls in place"
  fix_details:
    description: "Implement proper GitHub account management controls"
    instructions:
    - "Review organization member roles"
    - "Implement proper access controls"
    - "Set up account monitoring"
    estimated_date: "2024-12-31"
    automation_available: false
  created_by: "system"
  updated_by: "system"
  is_deleted: false
  metadata:
    resource_type: con_mon_v2.mappings.github.GithubResource
    field_path: organization_data.members
    connection_id: 1
    operation:
      name: custom
      logic: |
        result = False
        if fetched_value and isinstance(fetched_value, list):
            admin_count = sum(1 for member in fetched_value if hasattr(member, 'role') and member.role == 'admin')
            if admin_count > 0:
                result = True
    expected_value: null
    tags:
    - compliance
    - nist
    - ac
    - github_resource
    severity: high
    category: access_control
    control_ids:
    - 1
        """
        
        # Create a mock LLM response
        class MockLLMResponse:
            def __init__(self, content):
                self.content = content
        
        mock_response = MockLLMResponse(mock_yaml_content)
        
        # Process the response
        try:
            check = github_prompt_instance.process_response(mock_response)
            
            # Verify the check was created correctly
            assert isinstance(check, Check)
            assert check.name == 'github_resource_ac_2_compliance'
            assert check.description.startswith('Verify compliance with NIST 800-53 AC-2')
            assert check.category == 'access_control'
            
            # Verify compliance model structure
            assert isinstance(check.metadata, CheckMetadata)
            assert isinstance(check.output_statements, OutputStatements)
            assert isinstance(check.fix_details, FixDetails)
            assert isinstance(check.metadata.operation, CheckOperation)
            
            # Verify GitHub-specific details
            assert 'github' in check.metadata.resource_type.lower()
            assert check.metadata.field_path == 'organization_data.members'
            assert check.metadata.operation.name.value == 'custom'
            assert 'admin_count' in check.metadata.operation.logic
            
            # Verify tags and metadata
            assert 'compliance' in check.metadata.tags
            assert 'github_resource' in check.metadata.tags
            assert check.metadata.severity == 'high'
            assert check.metadata.category == 'access_control'
            
            print("✅ GitHub YAML processing test passed")
            
        except Exception as e:
            pytest.fail(f"GitHub YAML processing failed: {str(e)}")
    
    def test_github_resource_schema_loading(self, github_prompt_instance):
        """Test that GitHub resource schema is loaded correctly."""
        from con_mon_v2.utils.llm.prompts import load_resource_schema
        
        schema = load_resource_schema('github')
        
        # Check that schema contains expected GitHub fields
        assert 'github' in schema.lower()
        assert 'Resource Schema' in schema
        
        # Should contain some expected GitHub resource fields
        github_fields = ['organization_data', 'repository_data', 'security_data']
        schema_contains_github_fields = any(field in schema for field in github_fields)
        assert schema_contains_github_fields, "Schema should contain GitHub-specific fields"
    
    def test_github_severity_and_category_suggestions(self, github_prompt_instance):
        """Test GitHub-specific severity and category suggestions."""
        formatted_prompt = github_prompt_instance.format_prompt()
        
        # AC family should suggest high severity and access_control category
        assert 'high' in formatted_prompt  # Severity suggestion
        assert 'access_control' in formatted_prompt  # Category suggestion 