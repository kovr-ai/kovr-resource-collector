"""
Tests for LLM-based check generation functionality - GitHub specific.

This module tests the ChecksYamlPrompt class with GitHub resources.
"""
import os
import yaml
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from con_mon_v2.utils.llm.prompts import ChecksYamlPrompt
from con_mon_v2.utils.llm.client import LLMResponse
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.connectors.models import ConnectorType
from con_mon_v2.checks.models import Check, CheckMetadata, CheckResultStatement, CheckFailureFix, CheckOperation


class TestGitHubChecksYamlPrompt:
    """Test cases for ChecksYamlPrompt class with GitHub resources."""
    
    @pytest.fixture
    def sample_control_data(self) -> Dict[str, Any]:
        """Sample control data for testing."""
        return {
            'control_name': 'AC-2',
            'control_text': """The organization:
a. Identifies and selects the following types of information system accounts to support organizational missions/business functions: [Assignment: organization-defined information system account types];
b. Assigns account managers for information system accounts;
c. Establishes conditions for group and role membership;
d. Specifies authorized users of the information system, group and role membership, and access authorizations (i.e., privileges) and other attributes (as required) for each account;
e. Requires approvals by [Assignment: organization-defined personnel or roles] for requests to create information system accounts;
f. Creates, enables, modifies, disables, and removes information system accounts in accordance with [Assignment: organization-defined procedures or conditions];
g. Monitors the use of information system accounts;
h. Notifies account managers: 1. When accounts are no longer required; 2. When users are terminated or transferred; and 3. When individual information system usage or need-to-know changes;
i. Authorizes access to the information system based on: 1. A valid access authorization; 2. Intended system usage; and 3. Other attributes as required by the organization or associated missions/business functions;
j. Reviews accounts for compliance with account management requirements [Assignment: organization-defined frequency]; and
k. Establishes a process for reissuing shared/group account credentials (if deployed) when individuals are removed from the group.""",
            'control_title': 'Account Management',
            'control_id': 1
        }
    
    @pytest.fixture
    def github_mock_yaml_content(self) -> str:
        """Load GitHub mock YAML content from file."""
        mock_file_path = os.path.join(os.path.dirname(__file__), '..', 'mocks', 'github', 'check_prompt.yaml')
        with open(mock_file_path, 'r') as f:
            return f.read()
    
    @pytest.fixture
    def github_prompt_instance(self, sample_control_data) -> ChecksYamlPrompt:
        """Create a ChecksYamlPrompt instance for GitHub testing."""
        return ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=GithubResource,
            connector_type=ConnectorType.GITHUB,
        )
    
    @pytest.fixture
    def github_mock_llm_response(self, github_mock_yaml_content) -> LLMResponse:
        """Create a mock LLM response for GitHub."""
        return LLMResponse(
            content=github_mock_yaml_content,
            model_id="mock-model",
            usage={"input_tokens": 1000, "output_tokens": 500},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
    
    def test_github_prompt_initialization(self, sample_control_data):
        """Test that ChecksYamlPrompt initializes correctly for GitHub."""
        prompt = ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=GithubResource,
            connector_type=ConnectorType.GITHUB
        )
        
        assert prompt.control_name == 'AC-2'
        assert prompt.control_title == 'Account Management'
        assert prompt.resource_type == GithubResource
        assert prompt.connector_type == ConnectorType.GITHUB
        assert prompt.control_id == 1
        assert prompt.connector_type_lower == 'github'
    
    def test_github_format_prompt(self, github_prompt_instance):
        """Test that format_prompt generates a complete prompt for GitHub."""
        prompt = github_prompt_instance.format_prompt()
        
        # Check that the prompt contains expected sections
        assert "Control Information:" in prompt
        assert "AC-2" in prompt
        assert "Account Management" in prompt
        assert "Instructions:" in prompt
        assert "Example Format:" in prompt
        assert "Resource Schema:" in prompt
        assert "Guidelines:" in prompt
        
        # Check that GitHub schema is included
        assert "github:" in prompt
        assert "GithubResource" in prompt
        assert "organization_data" in prompt
        assert "repository_data" in prompt
    
    def test_github_process_response_valid_yaml(self, github_prompt_instance, github_mock_llm_response):
        """Test processing a valid LLM response with GitHub mock YAML."""
        with patch.object(github_prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = github_prompt_instance.process_response(github_mock_llm_response)

        # Verify the check object is created correctly
        assert isinstance(check, Check)
        assert check.id == "github_resource_ac_2_compliance"
        assert check.name == "github_resource_ac_2_compliance"
        assert check.description == "Verify compliance with NIST 800-53 AC-2 Account Management"
        assert check.category == "access_control"
        
        # Verify metadata is properly structured
        assert isinstance(check.metadata, CheckMetadata)
        assert check.metadata.field_path == "organization_data.members"
        assert check.metadata.severity == "high"
        assert check.metadata.category == "access_control"
        assert "compliance" in check.metadata.tags
        assert "nist" in check.metadata.tags
        assert "github_resource" in check.metadata.tags
        
        # Verify operation is properly structured
        assert isinstance(check.metadata.operation, CheckOperation)
        assert check.metadata.operation.name == "custom"
        assert "result = False" in check.metadata.operation.logic
        assert "admin_count" in check.metadata.operation.logic
        
        # Verify output statements
        assert isinstance(check.output_statements, CheckResultStatement)
        assert "GitHub organization has proper account management" in check.output_statements.success
        assert "missing admin accounts" in check.output_statements.failure
        assert "some account management controls" in check.output_statements.partial
        
        # Verify fix details
        assert isinstance(check.fix_details, CheckFailureFix)
        assert "Implement proper GitHub organization account management" in check.fix_details.description
        assert len(check.fix_details.instructions) == 4
        assert "Ensure at least one administrator account exists" in check.fix_details.instructions[0]
        assert check.fix_details.automation_available == False
    
    @patch('con_mon_v2.utils.llm.prompts.ResourceCollectionService')
    def test_github_test_check_success(self, mock_service_class, github_prompt_instance):
        """Test successful check testing against GitHub resource collection."""
        # Mock the service class and its instance
        mock_service_instance = Mock()
        mock_service_class.return_value = mock_service_instance
        
        mock_service_instance.get_resource_collection.return_value = Mock()
        mock_service_instance.validate_resource_field_paths.return_value = {
            'GithubResource': {
                'organization_data.members': 'success'
            }
        }
        
        # Create a mock check
        mock_check = Mock()
        mock_check.metadata.field_path = 'organization_data.members'
        
        success, message = github_prompt_instance.test_check(mock_check)
        
        assert success == True
        assert "Field path 'organization_data.members' validated successfully" in message
    
    def test_github_raw_yaml_storage(self, github_prompt_instance, github_mock_llm_response):
        """Test that raw YAML is stored in the GitHub check object for debugging."""
        with patch.object(github_prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = github_prompt_instance.process_response(github_mock_llm_response)
        
        assert hasattr(check, '_raw_yaml')
        assert check._raw_yaml is not None
        assert 'checks:' in check._raw_yaml
        assert 'github_resource_ac_2_compliance' in check._raw_yaml
    
    def test_github_system_fields_set(self, github_prompt_instance, github_mock_llm_response):
        """Test that system fields are properly set for GitHub checks."""
        with patch.object(github_prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = github_prompt_instance.process_response(github_mock_llm_response)
        
        assert check.created_by == "system"
        assert check.updated_by == "system"
        assert check.is_deleted == False


class TestGitHubMockYamlStructure:
    """Test the structure of the GitHub mock YAML."""
    
    @pytest.fixture
    def github_mock_yaml_data(self) -> Dict[str, Any]:
        """Load and parse GitHub mock YAML data."""
        mock_file_path = os.path.join(os.path.dirname(__file__), '..', 'mocks', 'github', 'check_prompt.yaml')
        with open(mock_file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_github_mock_yaml_structure(self, github_mock_yaml_data):
        """Test that the GitHub mock YAML has the expected structure."""
        assert 'checks' in github_mock_yaml_data
        assert len(github_mock_yaml_data['checks']) == 1
        
        check = github_mock_yaml_data['checks'][0]
        
        # Test main check fields
        required_fields = ['id', 'name', 'description', 'category', 'output_statements', 
                          'fix_details', 'created_by', 'updated_by', 'is_deleted', 'metadata']
        for field in required_fields:
            assert field in check, f"Required field '{field}' missing from GitHub check"
            
        # Test GitHub-specific values
        assert check['id'] == 'github_resource_ac_2_compliance'
        assert 'GitHub organization' in check['output_statements']['success']
    
    def test_github_mock_metadata_structure(self, github_mock_yaml_data):
        """Test that the GitHub mock metadata has the expected structure."""
        check = github_mock_yaml_data['checks'][0]
        metadata = check['metadata']
        
        required_metadata_fields = ['resource_type', 'field_path', 'operation', 'expected_value', 
                                   'tags', 'severity', 'category']
        for field in required_metadata_fields:
            assert field in metadata, f"Required metadata field '{field}' missing from GitHub check"
        
        # Test GitHub-specific values
        assert metadata['resource_type'] == 'GithubResource'
        assert metadata['field_path'] == 'organization_data.members'
        assert 'github_resource' in metadata['tags']
        
        # Test operation structure
        operation = metadata['operation']
        assert 'name' in operation
        assert 'logic' in operation
        assert operation['name'] == 'custom'
        assert 'result = False' in operation['logic']
        assert 'admin_count' in operation['logic']
    
    def test_github_mock_output_statements_structure(self, github_mock_yaml_data):
        """Test that the GitHub mock output statements have the expected structure."""
        check = github_mock_yaml_data['checks'][0]
        output_statements = check['output_statements']
        
        required_fields = ['success', 'failure', 'partial']
        for field in required_fields:
            assert field in output_statements, f"Required output statement field '{field}' missing from GitHub check"
            assert isinstance(output_statements[field], str)
            assert len(output_statements[field]) > 0
            assert 'GitHub' in output_statements[field]  # GitHub-specific content
    
    def test_github_mock_fix_details_structure(self, github_mock_yaml_data):
        """Test that the GitHub mock fix details have the expected structure."""
        check = github_mock_yaml_data['checks'][0]
        fix_details = check['fix_details']
        
        required_fields = ['description', 'instructions', 'estimated_date', 'automation_available']
        for field in required_fields:
            assert field in fix_details, f"Required fix details field '{field}' missing from GitHub check"
        
        assert isinstance(fix_details['instructions'], list)
        assert len(fix_details['instructions']) > 0
        assert isinstance(fix_details['automation_available'], bool)
        assert 'GitHub' in fix_details['description']  # GitHub-specific content 