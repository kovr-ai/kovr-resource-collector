"""
Test CheckPrompt with Mock Responses

Tests the complete CheckPrompt system using real mock responses generated
by the LLM, validating:
1. Mock response loading and parsing
2. Check object creation from mock YAML
3. Schema compliance validation
4. Provider-specific logic validation
5. End-to-end prompt → check flow
"""

import os
import yaml
from unittest.mock import patch, Mock
import pytest

from con_mon_v2.utils.llm import CheckPrompt, generate_check
from con_mon_v2.connectors import ConnectorType
from con_mon_v2.compliance.models import ComparisonOperationEnum
from con_mon_v2.utils.llm.client import LLMResponse


class TestCheckPromptWithMocks:
    """Test CheckPrompt using real mock responses"""
    
    @pytest.fixture
    def github_mock_yaml(self):
        """Load GitHub mock response YAML"""
        mock_path = os.path.join(os.path.dirname(__file__), 'mocks', 'github', 'prompt_response.yaml')
        with open(mock_path, 'r') as f:
            return f.read()
    
    @pytest.fixture
    def aws_mock_yaml(self):
        """Load AWS mock response YAML"""
        mock_path = os.path.join(os.path.dirname(__file__), 'mocks', 'aws', 'prompt_response.yaml')
        with open(mock_path, 'r') as f:
            return f.read()
    
    def test_github_mock_response_parsing(self, github_mock_yaml):
        """Test parsing GitHub mock response into Check object"""
        # Create CheckPrompt instance
        prompt = CheckPrompt(
            control_name='AC-2',
            control_text='The organization manages information system accounts.',
            control_title='Account Management',
            control_id=1,
            connector_type=ConnectorType.GITHUB,
            resource_model_name='GithubResource'
        )
        
        # Create mock LLM response
        mock_response = LLMResponse(
            content=github_mock_yaml, 
            model_id="mock", 
            usage={}, 
            stop_reason="end_turn", 
            raw_response={}
        )
        
        # Process the response
        check = prompt.process_response(mock_response)
        
        # Validate basic fields
        assert check.id == "github_ac_2_compliance"
        assert check.name == "github_ac_2_compliance"
        assert check.description == "Verify compliance with NIST 800-53 AC-2: Account Management"
        assert check.category == "configuration"
        assert check.created_by == "system"
        assert check.updated_by == "system"
        assert check.is_deleted == False
        
        # Validate output statements
        assert "Check passed:" in check.output_statements.success
        assert "Check failed:" in check.output_statements.failure
        assert "Check partially passed:" in check.output_statements.partial
        
        # Validate fix details
        assert check.fix_details.description
        assert len(check.fix_details.instructions) >= 2
        assert check.fix_details.estimated_time == "2 weeks"
        assert check.fix_details.automation_available == False
        
        # Validate metadata
        assert check.metadata.resource_type == "con_mon_v2.mappings.github.GithubResource"
        assert check.metadata.field_path == "collaboration_data"
        assert check.metadata.operation.name == ComparisonOperationEnum.CUSTOM
        assert "result = False" in check.metadata.operation.logic
        assert "fetched_value" in check.metadata.operation.logic
        assert check.metadata.expected_value is None
        assert "compliance" in check.metadata.tags
        assert "nist" in check.metadata.tags
        assert "github" in check.metadata.tags
        assert check.metadata.severity == "medium"
        assert check.metadata.category == "configuration"
        
        print("✅ GitHub mock response parsing test passed")
    
    def test_aws_mock_response_parsing(self, aws_mock_yaml):
        """Test parsing AWS mock response into Check object"""
        # Create CheckPrompt instance
        prompt = CheckPrompt(
            control_name='SC-7',
            control_text='The information system monitors and controls communications at boundaries.',
            control_title='Boundary Protection',
            control_id=2,
            connector_type=ConnectorType.AWS,
            resource_model_name='EC2Resource'
        )
        
        # Create mock LLM response
        mock_response = LLMResponse(
            content=aws_mock_yaml, 
            model_id="mock", 
            usage={}, 
            stop_reason="end_turn", 
            raw_response={}
        )
        
        # Process the response
        check = prompt.process_response(mock_response)
        
        # Validate basic fields
        assert check.id == "ec2_sc_7_compliance"
        assert check.name == "ec2_sc_7_compliance"
        assert check.description == "Verify compliance with NIST 800-53 SC-7: Boundary Protection"
        assert check.category == "configuration"
        
        # Validate metadata
        assert check.metadata.resource_type == "con_mon_v2.mappings.aws.EC2Resource"
        assert check.metadata.field_path == "security_groups"
        assert check.metadata.operation.name == ComparisonOperationEnum.CUSTOM
        assert "inbound_rules" in check.metadata.operation.logic
        assert "outbound_rules" in check.metadata.operation.logic
        assert "ec2" in check.metadata.tags
        assert check.metadata.severity == "medium"
        
        print("✅ AWS mock response parsing test passed")
    
    def test_github_check_logic_execution(self, github_mock_yaml):
        """Test GitHub check logic execution with mock data"""
        # Parse the check
        prompt = CheckPrompt(
            control_name='AC-2',
            control_text='Account management test',
            control_title='Account Management',
            control_id=1,
            connector_type=ConnectorType.GITHUB,
            resource_model_name='GithubResource'
        )
        
        mock_response = LLMResponse(
            content=github_mock_yaml, 
            model_id="mock", 
            usage={}, 
            stop_reason="end_turn", 
            raw_response={}
        )
        check = prompt.process_response(mock_response)
        
        # Test with valid collaboration data
        valid_data = {
            "collaborators": [
                {
                    "login": "user1",
                    "role_name": "admin",
                    "permissions": {
                        "admin": True,
                        "push": True,
                        "pull": True
                    }
                },
                {
                    "login": "user2", 
                    "role_name": "member",
                    "permissions": {
                        "admin": False,
                        "push": True,
                        "pull": True
                    }
                }
            ]
        }
        
        # Execute check logic
        comparison_op = check.comparison_operation
        result = comparison_op(valid_data, None)
        
        assert result == True, "Check should pass with valid collaboration data"
        
        # Test with invalid data (missing permissions)
        invalid_data = {
            "collaborators": [
                {
                    "login": "user1",
                    "role_name": "admin"
                    # Missing permissions
                }
            ]
        }
        
        result = comparison_op(invalid_data, None)
        assert result in [False, "partial"], "Check should fail or be partial with incomplete data"
        
        # Test with None data
        result = comparison_op(None, None)
        assert result == False, "Check should fail with None data"
        
        print("✅ GitHub check logic execution test passed")
    
    def test_aws_check_logic_execution(self, aws_mock_yaml):
        """Test AWS check logic execution with mock data"""
        # Parse the check
        prompt = CheckPrompt(
            control_name='SC-7',
            control_text='Boundary protection test',
            control_title='Boundary Protection', 
            control_id=2,
            connector_type=ConnectorType.AWS,
            resource_model_name='EC2Resource'
        )
        
        mock_response = LLMResponse(
            content=aws_mock_yaml, 
            model_id="mock", 
            usage={}, 
            stop_reason="end_turn", 
            raw_response={}
        )
        check = prompt.process_response(mock_response)
        
        # Create mock security group data
        class MockSecurityGroup:
            def __init__(self, inbound_rules=None, outbound_rules=None):
                self.inbound_rules = inbound_rules or []
                self.outbound_rules = outbound_rules or []
        
        # Test with valid security groups
        valid_security_groups = [
            MockSecurityGroup(
                inbound_rules=[{"port": 22, "protocol": "tcp", "source": "10.0.0.0/8"}],
                outbound_rules=[{"port": 443, "protocol": "tcp", "destination": "0.0.0.0/0"}]
            )
        ]
        
        # Execute check logic
        comparison_op = check.comparison_operation
        result = comparison_op(valid_security_groups, None)
        
        assert result == True, "Check should pass with valid security groups"
        
        # Test with incomplete security groups (no inbound rules)
        incomplete_security_groups = [
            MockSecurityGroup(
                inbound_rules=[],
                outbound_rules=[{"port": 443, "protocol": "tcp"}]
            )
        ]
        
        result = comparison_op(incomplete_security_groups, None)
        assert result == False, "Check should fail with incomplete security groups"
        
        # Test with None data
        result = comparison_op(None, None)
        assert result == False, "Check should fail with None data"
        
        print("✅ AWS check logic execution test passed")
    
    def test_mock_yaml_schema_compliance(self, github_mock_yaml, aws_mock_yaml):
        """Test that mock YAML responses comply with Check schema exactly"""
        
        # Test GitHub YAML structure
        github_data = yaml.safe_load(github_mock_yaml)
        assert 'checks' in github_data
        assert len(github_data['checks']) == 1
        
        github_check = github_data['checks'][0]
        
        # Required root fields
        required_root_fields = [
            'id', 'name', 'description', 'category', 'output_statements',
            'fix_details', 'created_by', 'updated_by', 'is_deleted', 'metadata'
        ]
        
        for field in required_root_fields:
            assert field in github_check, f"Missing required root field: {field}"
        
        # Required metadata fields
        required_metadata_fields = [
            'resource_type', 'field_path', 'operation', 'expected_value',
            'tags', 'severity', 'category'
        ]
        
        for field in required_metadata_fields:
            assert field in github_check['metadata'], f"Missing required metadata field: {field}"
        
        # Required operation fields
        assert 'name' in github_check['metadata']['operation']
        assert 'logic' in github_check['metadata']['operation']
        assert github_check['metadata']['operation']['name'] == 'custom'
        
        # Test AWS YAML structure (same validation)
        aws_data = yaml.safe_load(aws_mock_yaml)
        assert 'checks' in aws_data
        assert len(aws_data['checks']) == 1
        
        aws_check = aws_data['checks'][0]
        
        for field in required_root_fields:
            assert field in aws_check, f"Missing required root field in AWS: {field}"
        
        for field in required_metadata_fields:
            assert field in aws_check['metadata'], f"Missing required metadata field in AWS: {field}"
        
        print("✅ Mock YAML schema compliance test passed")
    
    @patch('con_mon_v2.utils.llm.prompt.get_llm_client')
    def test_end_to_end_prompt_to_check_flow(self, mock_get_llm_client):
        """Test complete flow from prompt generation to check validation"""
        
        # Create mock LLM client
        mock_client = Mock()
        mock_get_llm_client.return_value = mock_client
        
        # Load GitHub mock response for AC-3
        github_mock_path = os.path.join(os.path.dirname(__file__), 'mocks', 'github', 'prompt_response.yaml')
        with open(github_mock_path, 'r') as f:
            github_mock_yaml = f.read()
        
        # Create mock response for GitHub
        mock_github_response = LLMResponse(
            content=github_mock_yaml,
            model_id="mock",
            usage={},
            stop_reason="end_turn",
            raw_response={}
        )
        
        # Load AWS mock response for AU-2
        aws_mock_path = os.path.join(os.path.dirname(__file__), 'mocks', 'aws', 'prompt_response.yaml')
        with open(aws_mock_path, 'r') as f:
            aws_mock_yaml = f.read()
        
        # Create mock response for AWS
        mock_aws_response = LLMResponse(
            content=aws_mock_yaml,
            model_id="mock", 
            usage={},
            stop_reason="end_turn",
            raw_response={}
        )
        
        # Configure mock to return different responses based on call order
        mock_client.generate_response.side_effect = [mock_github_response, mock_aws_response]
        
        # Test GitHub flow
        github_check = generate_check(
            control_name='AC-3',
            control_text='The information system enforces approved authorizations for logical access.',
            control_title='Access Enforcement',
            control_id=3,
            connector_type=ConnectorType.GITHUB,
            resource_model_name='GithubResource'
        )
        
        # Validate GitHub check
        assert github_check.id
        assert github_check.name
        assert github_check.metadata.resource_type.endswith('GithubResource')
        assert github_check.metadata.operation.name == ComparisonOperationEnum.CUSTOM
        assert github_check.metadata.operation.logic
        assert 'github' in github_check.metadata.tags
        
        # Test AWS flow
        aws_check = generate_check(
            control_name='AU-2',
            control_text='The organization determines that the information system is capable of auditing events.',
            control_title='Audit Events',
            control_id=4,
            connector_type=ConnectorType.AWS,
            resource_model_name='EC2Resource'  # Changed from CloudTrailResource to EC2Resource to match mock
        )
        
        # Validate AWS check
        assert aws_check.id
        assert aws_check.name
        assert aws_check.metadata.resource_type.endswith('EC2Resource')  # Changed from CloudTrailResource
        assert aws_check.metadata.operation.name == ComparisonOperationEnum.CUSTOM
        assert aws_check.metadata.operation.logic
        assert any('aws' in tag or 'ec2' in tag.lower() for tag in aws_check.metadata.tags)  # Changed from cloudtrail to ec2
        
        # Verify that the mock was called twice (once for each generate_check call)
        assert mock_client.generate_response.call_count == 2
        
        print("✅ End-to-end prompt to check flow test passed")
    
    def test_provider_specific_field_paths(self):
        """Test that provider-specific field paths are used correctly"""
        
        # GitHub should use GitHub-specific field paths
        github_prompt = CheckPrompt(
            control_name='CM-2',
            control_text='Configuration management test',
            control_title='Baseline Configuration',
            control_id=5,
            connector_type=ConnectorType.GITHUB,
            resource_model_name='GithubResource'
        )
        
        github_field_paths = github_prompt.template_vars['field_path_examples']
        assert any('repository_data' in path for path in github_field_paths), "Should have GitHub-specific paths"
        
        # AWS should use AWS-specific field paths
        aws_prompt = CheckPrompt(
            control_name='CM-2',
            control_text='Configuration management test',
            control_title='Baseline Configuration',
            control_id=5,
            connector_type=ConnectorType.AWS,
            resource_model_name='EC2Resource'
        )
        
        aws_field_paths = aws_prompt.template_vars['field_path_examples']
        # AWS field paths should be different from GitHub
        assert github_field_paths != aws_field_paths, "AWS and GitHub should have different field paths"
        
        print("✅ Provider-specific field paths test passed")
    
    def test_template_variable_generation(self):
        """Test that template variables are generated correctly"""
        
        prompt = CheckPrompt(
            control_name='SI-4',
            control_text='The organization monitors the information system.',
            control_title='Information System Monitoring',
            control_id=6,
            connector_type=ConnectorType.GITHUB,
            resource_model_name='GithubResource',
            suggested_severity='high',
            suggested_category='monitoring'
        )
        
        vars = prompt.template_vars
        
        # Test core identifiers
        assert vars['check_id'] == 'github_si_4_compliance'
        assert vars['check_name'] == 'github_si_4_compliance'
        assert 'SI-4' in vars['check_description']
        
        # Test control information
        assert vars['control_name'] == 'SI-4'
        assert vars['control_title'] == 'Information System Monitoring'
        assert vars['control_family'] == 'si'
        
        # Test provider information
        assert vars['provider_name'] == 'github'
        assert vars['connector_type'] == 'github'
        assert vars['resource_model_name'] == 'GithubResource'
        assert vars['resource_type_full_path'] == 'con_mon_v2.mappings.github.GithubResource'
        
        # Test custom severity/category
        assert vars['suggested_severity'] == 'high'
        assert vars['suggested_category'] == 'monitoring'
        
        # Test tags
        expected_tags = ['compliance', 'nist', 'si', 'github']
        assert vars['tags'] == expected_tags
        
        # Test schema information
        assert ComparisonOperationEnum.CUSTOM.value in vars['operation_enums']
        assert ComparisonOperationEnum.EQUAL.value in vars['operation_enums']
        
        print("✅ Template variable generation test passed")


class TestMockDataIntegrity:
    """Test the integrity and consistency of mock data"""
    
    def test_mock_files_exist(self):
        """Test that all required mock files exist"""
        base_path = os.path.join(os.path.dirname(__file__), 'mocks')
        
        # Check directories exist
        assert os.path.exists(os.path.join(base_path, 'github'))
        assert os.path.exists(os.path.join(base_path, 'aws'))
        
        # Check files exist
        assert os.path.exists(os.path.join(base_path, 'github', 'prompt_response.yaml'))
        assert os.path.exists(os.path.join(base_path, 'aws', 'prompt_response.yaml'))
        
        print("✅ Mock files exist test passed")
    
    def test_mock_yaml_validity(self):
        """Test that mock YAML files are valid YAML"""
        mock_files = [
            'tests/mocks/github/prompt_response.yaml',
            'tests/mocks/aws/prompt_response.yaml'
        ]
        
        for mock_file in mock_files:
            with open(mock_file, 'r') as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {mock_file}: {e}")
        
        print("✅ Mock YAML validity test passed")
    
    def test_mock_data_consistency(self):
        """Test consistency between GitHub and AWS mock data structures"""
        
        # Load both mock files
        with open('tests/mocks/github/prompt_response.yaml', 'r') as f:
            github_data = yaml.safe_load(f)
        
        with open('tests/mocks/aws/prompt_response.yaml', 'r') as f:
            aws_data = yaml.safe_load(f)
        
        github_check = github_data['checks'][0]
        aws_check = aws_data['checks'][0]
        
        # Both should have the same structure
        assert set(github_check.keys()) == set(aws_check.keys()), "GitHub and AWS checks should have same root fields"
        assert set(github_check['metadata'].keys()) == set(aws_check['metadata'].keys()), "Metadata should have same structure"
        assert set(github_check['output_statements'].keys()) == set(aws_check['output_statements'].keys()), "Output statements should have same structure"
        assert set(github_check['fix_details'].keys()) == set(aws_check['fix_details'].keys()), "Fix details should have same structure"
        
        # But content should be different (provider-specific)
        assert github_check['id'] != aws_check['id']
        assert github_check['metadata']['resource_type'] != aws_check['metadata']['resource_type']
        assert github_check['metadata']['field_path'] != aws_check['metadata']['field_path']
        
        print("✅ Mock data consistency test passed")


if __name__ == "__main__":
    # Run all tests
    test_classes = [TestCheckPromptWithMocks, TestMockDataIntegrity]
    
    for test_class in test_classes:
        print(f"\n🧪 Running {test_class.__name__}...")
        instance = test_class()
        
        # Get fixtures if needed
        if hasattr(instance, 'github_mock_yaml'):
            github_mock_path = os.path.join(os.path.dirname(__file__), 'mocks', 'github', 'prompt_response.yaml')
            with open(github_mock_path, 'r') as f:
                github_mock = f.read()
        else:
            github_mock = None
            
        if hasattr(instance, 'aws_mock_yaml'):
            aws_mock_path = os.path.join(os.path.dirname(__file__), 'mocks', 'aws', 'prompt_response.yaml')
            with open(aws_mock_path, 'r') as f:
                aws_mock = f.read()
        else:
            aws_mock = None
        
        # Run all test methods
        for method_name in dir(instance):
            if method_name.startswith('test_'):
                try:
                    print(f"  Running {method_name}...")
                    method = getattr(instance, method_name)
                    
                    # Call with fixtures if method needs them
                    if 'github_mock_yaml' in method.__code__.co_varnames and 'aws_mock_yaml' in method.__code__.co_varnames:
                        method(github_mock, aws_mock)
                    elif 'github_mock_yaml' in method.__code__.co_varnames:
                        method(github_mock)
                    elif 'aws_mock_yaml' in method.__code__.co_varnames:
                        method(aws_mock)
                    else:
                        method()
                        
                except Exception as e:
                    print(f"  ❌ {method_name} failed: {e}")
                    import traceback
                    traceback.print_exc()
    
    print("\n🎉 All CheckPrompt mock tests completed!") 