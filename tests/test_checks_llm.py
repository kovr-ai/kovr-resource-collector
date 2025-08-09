"""
Tests for LLM-based check generation functionality.

This module tests the ChecksYamlPrompt class and related functionality
for generating compliance checks using LLM responses.
"""
import os
import yaml
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from con_mon_v2.utils.llm.prompts import ChecksYamlPrompt
from con_mon_v2.utils.llm.client import LLMResponse
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.checks.models import Check, CheckMetadata, CheckResultStatement, CheckFailureFix, CheckOperation


class TestChecksYamlPrompt:
    """Test cases for ChecksYamlPrompt class."""
    
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
    def mock_yaml_content(self) -> str:
        """Load mock YAML content from file."""
        mock_file_path = os.path.join(os.path.dirname(__file__), 'mocks', 'check_prompt.yaml')
        with open(mock_file_path, 'r') as f:
            return f.read()
    
    @pytest.fixture
    def prompt_instance(self, sample_control_data) -> ChecksYamlPrompt:
        """Create a ChecksYamlPrompt instance for testing."""
        return ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            resource_type=GithubResource,
            control_id=sample_control_data['control_id']
        )
    
    @pytest.fixture
    def mock_llm_response(self, mock_yaml_content) -> LLMResponse:
        """Create a mock LLM response."""
        return LLMResponse(
            content=mock_yaml_content,
            model_id="mock-model",
            usage={"input_tokens": 1000, "output_tokens": 500},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
    
    def test_prompt_initialization(self, sample_control_data):
        """Test that ChecksYamlPrompt initializes correctly."""
        prompt = ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            resource_type=GithubResource,
            control_id=sample_control_data['control_id']
        )
        
        assert prompt.control_name == 'AC-2'
        assert prompt.control_title == 'Account Management'
        assert prompt.control_id == 1
        assert prompt.resource_type == GithubResource
        assert prompt.resource_type_lower == 'github_resource'
        assert prompt.control_name_lower == 'ac_2'
        assert prompt.connector_type_lower == 'github'
        assert prompt.control_family == 'AC'
    
    def test_format_prompt(self, prompt_instance):
        """Test that format_prompt generates a complete prompt."""
        prompt = prompt_instance.format_prompt()
        
        # Check that the prompt contains expected sections
        assert "Control Information:" in prompt
        assert "AC-2" in prompt
        assert "Account Management" in prompt
        assert "Instructions:" in prompt
        assert "Example Format:" in prompt
        assert "Resource Schema:" in prompt
        assert "Guidelines:" in prompt
        
        # Check that control-specific information is included
        assert "The organization:" in prompt
        assert "Identifies and selects" in prompt
        
        # Check that resource type information is included
        assert "GithubResource" in prompt
    
    def test_process_response_valid_yaml(self, prompt_instance, mock_llm_response):
        """Test processing a valid LLM response with mock YAML."""
        with patch.object(prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = prompt_instance.process_response(mock_llm_response)
        
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
    
    def test_process_response_invalid_yaml(self, prompt_instance):
        """Test processing an invalid LLM response."""
        invalid_response = LLMResponse(
            content="invalid yaml content: [unclosed bracket",
            model_id="mock-model",
            usage={"input_tokens": 100, "output_tokens": 50},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
        
        with pytest.raises(yaml.YAMLError):
            prompt_instance.process_response(invalid_response)
    
    def test_process_response_missing_checks_key(self, prompt_instance):
        """Test processing response without 'checks' key gets auto-corrected."""
        invalid_yaml = """
        invalid_structure:
        - name: test
        """
        invalid_response = LLMResponse(
            content=invalid_yaml,
            model_id="mock-model",
            usage={"input_tokens": 100, "output_tokens": 50},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
        
        # The process_response method should auto-correct this by prepending 'checks:'
        # but it will still fail due to missing required fields
        with pytest.raises(Exception):  # Could be ValidationError or other errors
            prompt_instance.process_response(invalid_response)
    
    def test_process_response_multiple_checks(self, prompt_instance):
        """Test processing response with multiple checks (should fail)."""
        multiple_checks_yaml = """
        checks:
        - id: check1
          name: check1
        - id: check2
          name: check2
        """
        invalid_response = LLMResponse(
            content=multiple_checks_yaml,
            model_id="mock-model",
            usage={"input_tokens": 100, "output_tokens": 50},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
        
        with pytest.raises(ValueError, match="Expected 1 check, got 2"):
            prompt_instance.process_response(invalid_response)
    
    def test_process_response_markdown_removal(self, prompt_instance):
        """Test that markdown code blocks are properly removed."""
        yaml_with_markdown = """```yaml
checks:
- id: test_check
  name: test_check
  description: Test check
  category: test
  metadata:
    field_path: test.path
    operation:
      name: custom
      logic: "result = True"
    expected_value: null
    tags: []
    severity: medium
    category: configuration
    control_ids: [1]
  output_statements:
    success: "Success"
    failure: "Failure"
    partial: "Partial"
  fix_details:
    description: "Fix it"
    instructions: ["Step 1"]
    estimated_date: "2024-12-31"
    automation_available: false
  created_by: "system"
  updated_by: "system"
  is_deleted: false
```"""
        
        response = LLMResponse(
            content=yaml_with_markdown,
            model_id="mock-model",
            usage={"input_tokens": 100, "output_tokens": 50},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
        
        with patch.object(prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = prompt_instance.process_response(response)
        
        assert check.id == "test_check"
        assert check.name == "test_check"
    
    def test_severity_suggestions(self, sample_control_data):
        """Test that severity suggestions work correctly for different control families."""
        test_cases = [
            ('AC-1', 'high'),      # Access Control
            ('AU-1', 'medium'),    # Audit and Accountability
            ('CM-1', 'medium'),    # Configuration Management
            ('IA-1', 'high'),      # Identification and Authentication
            ('SC-1', 'high'),      # System and Communications Protection
            ('SI-1', 'medium'),    # System and Information Integrity
            ('XX-1', 'medium'),    # Unknown family should default to medium
        ]
        
        for control_name, expected_severity in test_cases:
            prompt = ChecksYamlPrompt(
                control_name=control_name,
                control_text=sample_control_data['control_text'],
                control_title=sample_control_data['control_title'],
                resource_type=GithubResource,
                control_id=sample_control_data['control_id']
            )
            
            formatted_prompt = prompt.format_prompt()
            assert f"severity: {expected_severity}" in formatted_prompt
    
    def test_category_suggestions(self, sample_control_data):
        """Test that category suggestions work correctly for different control families."""
        test_cases = [
            ('AC-1', 'access_control'),
            ('AU-1', 'monitoring'),
            ('CM-1', 'configuration'),
            ('IA-1', 'access_control'),
            ('SC-1', 'network_security'),
            ('SI-1', 'monitoring'),
            ('XX-1', 'configuration'),  # Unknown family should default to configuration
        ]
        
        for control_name, expected_category in test_cases:
            prompt = ChecksYamlPrompt(
                control_name=control_name,
                control_text=sample_control_data['control_text'],
                control_title=sample_control_data['control_title'],
                resource_type=GithubResource,
                control_id=sample_control_data['control_id']
            )
            
            formatted_prompt = prompt.format_prompt()
            assert f"category: {expected_category}" in formatted_prompt
    
    @patch('con_mon_v2.utils.llm.prompts.ResourceCollectionService')
    def test_test_check_success(self, mock_service_class, prompt_instance):
        """Test successful check testing against resource collection."""
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
        
        success, message = prompt_instance.test_check(mock_check)
        
        assert success == True
        assert "Field path 'organization_data.members' validated successfully" in message
    
    @patch('con_mon_v2.utils.llm.prompts.ResourceCollectionService')
    def test_test_check_field_not_found(self, mock_service_class, prompt_instance):
        """Test check testing when field path is not found."""
        # Mock the service class and its instance
        mock_service_instance = Mock()
        mock_service_class.return_value = mock_service_instance
        
        mock_service_instance.get_resource_collection.return_value = Mock()
        mock_service_instance.validate_resource_field_paths.return_value = {
            'GithubResource': {
                'other.field': 'success'
            }
        }
        
        # Create a mock check
        mock_check = Mock()
        mock_check.metadata.field_path = 'missing.field'
        
        success, message = prompt_instance.test_check(mock_check)
        
        assert success == False
        assert "Field path 'missing.field' not found in any resource" in message
    
    def test_raw_yaml_storage(self, prompt_instance, mock_llm_response):
        """Test that raw YAML is stored in the check object for debugging."""
        with patch.object(prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = prompt_instance.process_response(mock_llm_response)
        
        assert hasattr(check, '_raw_yaml')
        assert check._raw_yaml is not None
        assert 'checks:' in check._raw_yaml
        assert 'github_resource_ac_2_compliance' in check._raw_yaml
    
    def test_system_fields_set(self, prompt_instance, mock_llm_response):
        """Test that system fields are properly set."""
        with patch.object(prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = prompt_instance.process_response(mock_llm_response)
        
        assert check.created_by == "system"
        assert check.updated_by == "system"
        assert check.is_deleted == False


class TestMockYamlStructure:
    """Test the structure of the generated mock YAML."""
    
    @pytest.fixture
    def mock_yaml_data(self) -> Dict[str, Any]:
        """Load and parse mock YAML data."""
        mock_file_path = os.path.join(os.path.dirname(__file__), 'mocks', 'check_prompt.yaml')
        with open(mock_file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_mock_yaml_structure(self, mock_yaml_data):
        """Test that the mock YAML has the expected structure."""
        assert 'checks' in mock_yaml_data
        assert len(mock_yaml_data['checks']) == 1
        
        check = mock_yaml_data['checks'][0]
        
        # Test main check fields
        required_fields = ['id', 'name', 'description', 'category', 'output_statements', 
                          'fix_details', 'created_by', 'updated_by', 'is_deleted', 'metadata']
        for field in required_fields:
            assert field in check, f"Required field '{field}' missing from check"
    
    def test_mock_metadata_structure(self, mock_yaml_data):
        """Test that the mock metadata has the expected structure."""
        check = mock_yaml_data['checks'][0]
        metadata = check['metadata']
        
        required_metadata_fields = ['field_path', 'operation', 'expected_value', 
                                   'tags', 'severity', 'category']
        for field in required_metadata_fields:
            assert field in metadata, f"Required metadata field '{field}' missing"
        
        # Test operation structure
        operation = metadata['operation']
        assert 'name' in operation
        assert 'logic' in operation
        assert operation['name'] == 'custom'
        assert 'result = False' in operation['logic']
    
    def test_mock_output_statements_structure(self, mock_yaml_data):
        """Test that the mock output statements have the expected structure."""
        check = mock_yaml_data['checks'][0]
        output_statements = check['output_statements']
        
        required_fields = ['success', 'failure', 'partial']
        for field in required_fields:
            assert field in output_statements, f"Required output statement field '{field}' missing"
            assert isinstance(output_statements[field], str)
            assert len(output_statements[field]) > 0
    
    def test_mock_fix_details_structure(self, mock_yaml_data):
        """Test that the mock fix details have the expected structure."""
        check = mock_yaml_data['checks'][0]
        fix_details = check['fix_details']
        
        required_fields = ['description', 'instructions', 'estimated_date', 'automation_available']
        for field in required_fields:
            assert field in fix_details, f"Required fix details field '{field}' missing"
        
        assert isinstance(fix_details['instructions'], list)
        assert len(fix_details['instructions']) > 0
        assert isinstance(fix_details['automation_available'], bool) 