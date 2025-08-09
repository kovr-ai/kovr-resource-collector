"""
Tests for LLM-based check generation functionality - AWS specific.

This module tests the ChecksYamlPrompt class with AWS resources.
"""
import os
import yaml
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from con_mon_v2.utils.llm.prompts import ChecksYamlPrompt
from con_mon_v2.utils.llm.client import LLMResponse
from con_mon_v2.mappings.aws import EC2Resource
from con_mon_v2.connectors.models import ConnectorType
from con_mon_v2.checks.models import Check, CheckMetadata, CheckResultStatement, CheckFailureFix, CheckOperation


class TestAWSChecksYamlPrompt:
    """Test cases for ChecksYamlPrompt class with AWS resources."""
    
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
    def aws_mock_yaml_content(self) -> str:
        """Load AWS mock YAML content from file."""
        mock_file_path = os.path.join(os.path.dirname(__file__), '..', 'mocks', 'aws', 'check_prompt.yaml')
        with open(mock_file_path, 'r') as f:
            return f.read()
    
    @pytest.fixture
    def aws_prompt_instance(self, sample_control_data) -> ChecksYamlPrompt:
        """Create a ChecksYamlPrompt instance for AWS testing."""
        return ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=EC2Resource,
            connector_type=ConnectorType.AWS,
        )
    
    @pytest.fixture
    def aws_mock_llm_response(self, aws_mock_yaml_content) -> LLMResponse:
        """Create a mock LLM response for AWS."""
        return LLMResponse(
            content=aws_mock_yaml_content,
            model_id="mock-model",
            usage={"input_tokens": 1000, "output_tokens": 500},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
    
    def test_aws_prompt_initialization(self, sample_control_data):
        """Test that ChecksYamlPrompt initializes correctly for AWS."""
        prompt = ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=EC2Resource,
            connector_type=ConnectorType.AWS
        )
        
        assert prompt.control_name == 'AC-2'
        assert prompt.control_title == 'Account Management'
        assert prompt.resource_type == EC2Resource
        assert prompt.connector_type == ConnectorType.AWS
        assert prompt.control_id == 1
        assert prompt.connector_type_lower == 'aws'
    
    def test_aws_format_prompt(self, aws_prompt_instance):
        """Test that format_prompt generates a complete prompt for AWS."""
        prompt = aws_prompt_instance.format_prompt()
        
        # Check that the prompt contains expected sections
        assert "Control Information:" in prompt
        assert "AC-2" in prompt
        assert "Account Management" in prompt
        assert "Instructions:" in prompt
        assert "Example Format:" in prompt
        assert "Resource Schema:" in prompt
        assert "Guidelines:" in prompt
        
        # Check that AWS schema is included
        assert "aws:" in prompt
        assert "EC2Resource" in prompt
        assert "instances" in prompt
        assert "iam_instance_profile" in prompt
    
    def test_aws_process_response_valid_yaml(self, aws_prompt_instance, aws_mock_llm_response):
        """Test processing a valid LLM response with AWS mock YAML."""
        with patch.object(aws_prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = aws_prompt_instance.process_response(aws_mock_llm_response)

        # Verify the check object is created correctly
        assert isinstance(check, Check)
        assert check.id == "ec2_resource_ac_2_compliance"
        assert check.name == "ec2_resource_ac_2_compliance"
        assert check.description == "Verify compliance with NIST 800-53 AC-2 Account Management for EC2 instances"
        assert check.category == "access_control"
        
        # Verify metadata is properly structured
        assert isinstance(check.metadata, CheckMetadata)
        assert check.metadata.field_path == "instances"
        assert check.metadata.severity == "high"
        assert check.metadata.category == "access_control"
        assert "compliance" in check.metadata.tags
        assert "nist" in check.metadata.tags
        assert "ec2_resource" in check.metadata.tags
        
        # Verify operation is properly structured
        assert isinstance(check.metadata.operation, CheckOperation)
        assert check.metadata.operation.name == "custom"
        assert "result = False" in check.metadata.operation.logic
        assert "instances_with_profiles" in check.metadata.operation.logic
        
        # Verify output statements
        assert isinstance(check.output_statements, CheckResultStatement)
        assert "EC2 instances have proper IAM instance profiles" in check.output_statements.success
        assert "EC2 instances lack proper IAM instance profiles" in check.output_statements.failure
        assert "Some EC2 instances have proper access controls" in check.output_statements.partial
        
        # Verify fix details
        assert isinstance(check.fix_details, CheckFailureFix)
        assert "Implement proper IAM instance profiles" in check.fix_details.description
        assert len(check.fix_details.instructions) == 4
        assert "Ensure all EC2 instances have IAM instance profiles attached" in check.fix_details.instructions[0]
        assert check.fix_details.automation_available == False
    
    @patch('con_mon_v2.utils.llm.prompts.ResourceCollectionService')
    def test_aws_test_check_success(self, mock_service_class, aws_prompt_instance):
        """Test successful check testing against AWS resource collection."""
        # Mock the service class and its instance
        mock_service_instance = Mock()
        mock_service_class.return_value = mock_service_instance
        
        mock_service_instance.get_resource_collection.return_value = Mock()
        mock_service_instance.validate_resource_field_paths.return_value = {
            'EC2Resource': {
                'instances': 'success'
            }
        }
        
        # Create a mock check
        mock_check = Mock()
        mock_check.metadata.field_path = 'instances'
        
        success, message = aws_prompt_instance.test_check(mock_check)
        
        assert success == True
        assert "Field path 'instances' validated successfully" in message
    
    def test_aws_raw_yaml_storage(self, aws_prompt_instance, aws_mock_llm_response):
        """Test that raw YAML is stored in the AWS check object for debugging."""
        with patch.object(aws_prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = aws_prompt_instance.process_response(aws_mock_llm_response)
        
        assert hasattr(check, '_raw_yaml')
        assert check._raw_yaml is not None
        assert 'checks:' in check._raw_yaml
        assert 'ec2_resource_ac_2_compliance' in check._raw_yaml
    
    def test_aws_system_fields_set(self, aws_prompt_instance, aws_mock_llm_response):
        """Test that system fields are properly set for AWS checks."""
        with patch.object(aws_prompt_instance, 'test_check', return_value=(True, "Test passed")):
            check = aws_prompt_instance.process_response(aws_mock_llm_response)
        
        assert check.created_by == "system"
        assert check.updated_by == "system"
        assert check.is_deleted == False


class TestAWSMockYamlStructure:
    """Test the structure of the AWS mock YAML."""
    
    @pytest.fixture
    def aws_mock_yaml_data(self) -> Dict[str, Any]:
        """Load and parse AWS mock YAML data."""
        mock_file_path = os.path.join(os.path.dirname(__file__), '..', 'mocks', 'aws', 'check_prompt.yaml')
        with open(mock_file_path, 'r') as f:
            return yaml.safe_load(f)
    
    def test_aws_mock_yaml_structure(self, aws_mock_yaml_data):
        """Test that the AWS mock YAML has the expected structure."""
        assert 'checks' in aws_mock_yaml_data
        assert len(aws_mock_yaml_data['checks']) == 1
        
        check = aws_mock_yaml_data['checks'][0]
        
        # Test main check fields
        required_fields = ['id', 'name', 'description', 'category', 'output_statements', 
                          'fix_details', 'created_by', 'updated_by', 'is_deleted', 'metadata']
        for field in required_fields:
            assert field in check, f"Required field '{field}' missing from AWS check"
            
        # Test AWS-specific values
        assert check['id'] == 'ec2_resource_ac_2_compliance'
        assert 'EC2 instances' in check['output_statements']['success']
    
    def test_aws_mock_metadata_structure(self, aws_mock_yaml_data):
        """Test that the AWS mock metadata has the expected structure."""
        check = aws_mock_yaml_data['checks'][0]
        metadata = check['metadata']
        
        required_metadata_fields = ['resource_type', 'field_path', 'operation', 'expected_value', 
                                   'tags', 'severity', 'category']
        for field in required_metadata_fields:
            assert field in metadata, f"Required metadata field '{field}' missing from AWS check"
        
        # Test AWS-specific values
        assert metadata['resource_type'] == 'EC2Resource'
        assert metadata['field_path'] == 'instances'
        assert 'ec2_resource' in metadata['tags']
        
        # Test operation structure
        operation = metadata['operation']
        assert 'name' in operation
        assert 'logic' in operation
        assert operation['name'] == 'custom'
        assert 'result = False' in operation['logic']
        assert 'instances_with_profiles' in operation['logic']
    
    def test_aws_mock_output_statements_structure(self, aws_mock_yaml_data):
        """Test that the AWS mock output statements have the expected structure."""
        check = aws_mock_yaml_data['checks'][0]
        output_statements = check['output_statements']
        
        required_fields = ['success', 'failure', 'partial']
        for field in required_fields:
            assert field in output_statements, f"Required output statement field '{field}' missing from AWS check"
            assert isinstance(output_statements[field], str)
            assert len(output_statements[field]) > 0
            assert 'EC2' in output_statements[field]  # AWS-specific content
    
    def test_aws_mock_fix_details_structure(self, aws_mock_yaml_data):
        """Test that the AWS mock fix details have the expected structure."""
        check = aws_mock_yaml_data['checks'][0]
        fix_details = check['fix_details']
        
        required_fields = ['description', 'instructions', 'estimated_date', 'automation_available']
        for field in required_fields:
            assert field in fix_details, f"Required fix details field '{field}' missing from AWS check"
        
        assert isinstance(fix_details['instructions'], list)
        assert len(fix_details['instructions']) > 0
        assert isinstance(fix_details['automation_available'], bool)
        assert 'IAM instance profiles' in fix_details['description']  # AWS-specific content 