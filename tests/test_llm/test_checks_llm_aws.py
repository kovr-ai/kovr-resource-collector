"""
AWS LLM Checks Test Module

This module tests the ChecksPrompt class with AWS resources.
"""

import pytest
from con_mon_v2.utils.llm.prompts import ChecksPrompt
from con_mon_v2.compliance.models import Check, CheckMetadata, OutputStatements, FixDetails, CheckOperation
from con_mon_v2.mappings.aws import EC2Resource
from con_mon_v2.connectors.models import ConnectorType


class TestAWSChecksPrompt:
    """Test cases for ChecksPrompt class with AWS resources."""
    
    @pytest.fixture
    def sample_control_data(self):
        """Sample control data for testing."""
        return {
            'control_name': 'SC-7',
            'control_text': 'Boundary Protection: The information system monitors and controls communications at the external boundary.',
            'control_title': 'Boundary Protection',
            'control_id': 2,
            'resource_type': EC2Resource,
            'connector_type': ConnectorType.AWS
        }
    
    @pytest.fixture
    def aws_prompt_instance(self, sample_control_data) -> ChecksPrompt:
        """Create a ChecksPrompt instance for AWS testing."""
        return ChecksPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_model=sample_control_data['resource_type'],
            connector_type=sample_control_data['connector_type']
        )
    
    def test_aws_prompt_initialization(self, sample_control_data):
        """Test that ChecksPrompt initializes correctly for AWS."""
        prompt = ChecksPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_model=sample_control_data['resource_type'],
            connector_type=sample_control_data['connector_type']
        )
        
        assert prompt.control_name == 'SC-7'
        assert prompt.control_title == 'Boundary Protection'
        assert prompt.resource_model == EC2Resource
        assert prompt.connector_type == ConnectorType.AWS
        assert prompt.connector_type_lower == 'aws'
    
    def test_aws_prompt_formatting(self, aws_prompt_instance):
        """Test AWS prompt formatting."""
        formatted_prompt = aws_prompt_instance.format_prompt()
        
        # Check that key AWS-specific elements are in the prompt
        assert 'SC-7' in formatted_prompt
        assert 'Boundary Protection' in formatted_prompt
        assert 'resource_model' in formatted_prompt
        assert 'field_path' in formatted_prompt
        assert 'compliance' in formatted_prompt
        
        # Check for compliance model specific instructions
        assert 'ComparisonOperation' in formatted_prompt
        assert 'metadata' in formatted_prompt
        assert 'connection_id' in formatted_prompt 