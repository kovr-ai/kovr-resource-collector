#!/usr/bin/env python3
"""
Tests for Check operation functionality through metadata access.

This module tests the operation functionality that works through the
metadata.operation property, which provides access to CheckOperation data.
"""

import os
import yaml
import pytest
from typing import Dict, Any

from con_mon_v2.checks.models import (
    Check, CheckMetadata, CheckOperation, CheckResultStatement, 
    CheckFailureFix
)
from con_mon_v2.utils.llm.prompts import ChecksYamlPrompt
from con_mon_v2.compliance.models import Control
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.connectors.models import ConnectorType


class TestCheckMetadataOperationAccess:
    """Test accessing operation data through metadata (which works without issues)."""
    
    @pytest.fixture
    def sample_check_data(self) -> Dict[str, Any]:
        """Sample check data with custom operation."""
        return {
            'id': 'test_metadata_check',
            'name': 'test_metadata_check',
            'description': 'Test check for metadata operation access',
            'category': 'access_control',
            'created_by': 'system',
            'updated_by': 'system',
            'is_deleted': False,
            'metadata': CheckMetadata(
                resource_type='con_mon_v2.mappings.github.GithubResource',
                field_path='organization_data.members',
                operation=CheckOperation(
                    name='custom',
                    logic='''
result = False
if fetched_value and isinstance(fetched_value, list):
    admin_count = sum(1 for member in fetched_value if member.get('role') == 'admin')
    if admin_count > 0:
        result = True
'''
                ),
                expected_value=None,
                tags=['test', 'operation'],
                severity='medium',
                category='access_control'
            ),
            'output_statements': CheckResultStatement(
                success='Operation test passed',
                failure='Operation test failed',
                partial='Operation test partially passed'
            ),
            'fix_details': CheckFailureFix(
                description='Fix operation test',
                instructions=['Step 1: Fix the issue'],
                estimated_date='2024-12-31',
                automation_available=False
            )
        }
    
    @pytest.fixture
    def sample_check(self, sample_check_data) -> Check:
        """Create a sample Check object."""
        return Check(**sample_check_data)
    
    def test_metadata_operation_name_access(self, sample_check):
        """Test that we can access operation name through metadata."""
        assert sample_check.metadata.operation.name == 'custom'
    
    def test_metadata_operation_logic_access(self, sample_check):
        """Test that we can access operation logic through metadata."""
        logic = sample_check.metadata.operation.logic
        assert 'admin_count' in logic
        assert 'fetched_value' in logic
        assert 'result = False' in logic
    
    def test_metadata_operation_logic_content(self, sample_check):
        """Test that operation logic contains expected content."""
        logic = sample_check.metadata.operation.logic
        assert 'isinstance(fetched_value, list)' in logic
        assert "member.get('role') == 'admin'" in logic
        assert 'result = True' in logic
    
    def test_different_operation_names(self):
        """Test checks with different operation names."""
        operation_names = ['equals', 'contains', 'greater_than', 'custom']
        
        for op_name in operation_names:
            metadata = CheckMetadata(
                resource_type='con_mon_v2.mappings.github.GithubResource',
                field_path='test.field',
                operation=CheckOperation(
                    name=op_name,
                    logic='result = True' if op_name == 'custom' else ''
                ),
                expected_value='test_value' if op_name != 'custom' else None,
                tags=['test'],
                severity='low',
                category='configuration'
            )
            
            check = Check(
                id=f'{op_name}_test',
                name=f'{op_name}_test',
                description=f'Test {op_name} operation',
                category='configuration',
                created_by='system',
                updated_by='system',
                is_deleted=False,
                metadata=metadata,
                output_statements=CheckResultStatement(
                    success=f'{op_name} test passed',
                    failure=f'{op_name} test failed',
                    partial=f'{op_name} test partially passed'
                ),
                fix_details=CheckFailureFix(
                    description=f'Fix {op_name} test',
                    instructions=['Step 1'],
                    estimated_date='2024-12-31',
                    automation_available=False
                )
            )
            
            # Test that we can access the operation name
            assert check.metadata.operation.name == op_name
            
            # Test logic content based on operation type
            if op_name == 'custom':
                assert 'result = True' in check.metadata.operation.logic
            else:
                assert check.metadata.operation.logic == ''
    
    def test_operation_expected_value_access(self):
        """Test that we can access expected_value through metadata."""
        metadata = CheckMetadata(
            resource_type='con_mon_v2.mappings.github.GithubResource',
            field_path='status',
            operation=CheckOperation(name='equals', logic=''),
            expected_value='active',
            tags=['test'],
            severity='low',
            category='configuration'
        )
        
        check = Check(
            id='expected_value_test',
            name='expected_value_test',
            description='Test expected value access',
            category='configuration',
            created_by='system',
            updated_by='system',
            is_deleted=False,
            metadata=metadata,
            output_statements=CheckResultStatement(
                success='Test passed',
                failure='Test failed',
                partial='Test partially passed'
            ),
            fix_details=CheckFailureFix(
                description='Fix test',
                instructions=['Step 1'],
                estimated_date='2024-12-31',
                automation_available=False
            )
        )
        
        # Test that we can access expected_value through metadata
        assert check.metadata.expected_value == 'active'
    
    def test_operation_field_path_access(self, sample_check):
        """Test that we can access field_path through metadata."""
        assert sample_check.metadata.field_path == 'organization_data.members'
    
    def test_operation_resource_type_access(self, sample_check):
        """Test that we can access resource_type through metadata."""
        assert sample_check.metadata.resource_type == 'con_mon_v2.mappings.github.GithubResource'


class TestCheckOperationIntegration:
    """Integration tests for operation functionality with real YAML data."""
    
    @pytest.fixture
    def github_mock_yaml_content(self) -> str:
        """Load GitHub mock YAML content from file."""
        mock_file_path = os.path.join(os.path.dirname(__file__), '..', 'mocks', 'github', 'check_prompt.yaml')
        with open(mock_file_path, 'r') as f:
            return f.read()
    
    @pytest.fixture
    def github_check_from_mock(self, github_mock_yaml_content) -> Check:
        """Create a Check object from GitHub mock YAML."""
        yaml_data = yaml.safe_load(github_mock_yaml_content)
        check_dict = yaml_data['checks'][0]
        
        # Extract and create all required objects
        metadata_dict = check_dict['metadata']
        operation_dict = metadata_dict['operation']
        
        metadata = CheckMetadata(
            resource_type='con_mon_v2.mappings.github.GithubResource',
            field_path=metadata_dict['field_path'],
            operation=CheckOperation(
                name=operation_dict['name'],
                logic=operation_dict['logic']
            ),
            expected_value=metadata_dict.get('expected_value'),
            tags=metadata_dict.get('tags', []),
            severity=metadata_dict.get('severity', 'medium'),
            category=metadata_dict.get('category', 'configuration')
        )
        
        output_statements = CheckResultStatement(**check_dict['output_statements'])
        fix_details = CheckFailureFix(**check_dict['fix_details'])
        
        return Check(
            id=check_dict['id'],
            name=check_dict['name'],
            description=check_dict['description'],
            category=check_dict['category'],
            created_by=check_dict.get('created_by', 'system'),
            updated_by=check_dict.get('updated_by', 'system'),
            is_deleted=check_dict.get('is_deleted', False),
            metadata=metadata,
            output_statements=output_statements,
            fix_details=fix_details
        )
    
    def test_mock_check_metadata_operation(self, github_check_from_mock):
        """Test that mock check metadata operation works correctly."""
        operation = github_check_from_mock.metadata.operation
        assert operation is not None
        assert isinstance(operation, CheckOperation)
        assert operation.name == 'custom'
        assert 'admin_count' in operation.logic
    
    def test_mock_check_operation_logic_content(self, github_check_from_mock):
        """Test that mock check operation logic has expected content."""
        logic = github_check_from_mock.metadata.operation.logic
        
        # Check for key components of the logic
        assert 'result = False' in logic
        assert 'fetched_value' in logic
        assert 'isinstance(fetched_value, list)' in logic
        assert 'admin_count' in logic
        assert 'result = True' in logic
    
    def test_mock_check_field_path(self, github_check_from_mock):
        """Test that mock check has correct field path."""
        assert github_check_from_mock.metadata.field_path == 'organization_data.members'
    
    def test_mock_check_resource_type(self, github_check_from_mock):
        """Test that mock check has correct resource type."""
        assert github_check_from_mock.metadata.resource_type == 'con_mon_v2.mappings.github.GithubResource'
    
    def test_llm_generated_check_metadata_operation(self):
        """Test operation metadata with LLM-generated check."""
        # Create a simple control for testing with all required fields
        control = Control(
            id=1,
            framework_id=1,
            control_id='AC-2',
            name='Account Management',
            description='The organization manages information system accounts.'
        )
        
        # Create ChecksYamlPrompt
        prompt = ChecksYamlPrompt(
            control_name=control.control_id,
            control_text=control.description,
            control_title=control.name,
            control_id=control.id,
            resource_type=GithubResource,
            connector_type=ConnectorType.GITHUB
        )
        
        # Mock LLM response with valid YAML
        mock_yaml = """
checks:
- id: github_resource_ac_2_compliance
  name: github_resource_ac_2_compliance
  description: Test LLM generated check
  category: access_control
  output_statements:
    success: "Check passed"
    failure: "Check failed"
    partial: "Check partially passed"
  fix_details:
    description: "Fix the issue"
    instructions:
    - "Step 1"
    estimated_date: "2024-12-31"
    automation_available: false
  created_by: "system"
  updated_by: "system"
  is_deleted: false
  metadata:
    resource_type: GithubResource
    field_path: organization_data.members
    operation:
      name: custom
      logic: |
        result = False
        if fetched_value and isinstance(fetched_value, list):
            admin_count = sum(1 for member in fetched_value if member.get('role') == 'admin')
            if admin_count > 0:
                result = True
    expected_value: null
    tags:
    - compliance
    - test
    severity: high
    category: access_control
    control_ids:
    - 1
"""
        
        from con_mon_v2.utils.llm.client import LLMResponse
        from unittest.mock import patch
        
        mock_response = LLMResponse(
            content=mock_yaml,
            model_id="test-model",
            usage={"input_tokens": 100, "output_tokens": 200},
            stop_reason="end_turn",
            raw_response={"test": "response"}
        )
        
        # Process the response with mocked test_check
        with patch.object(prompt, 'test_check', return_value=(True, "Test passed")):
            check = prompt.process_response(mock_response)
        
        # Test the metadata operation (this works without issues)
        operation = check.metadata.operation
        assert operation is not None
        assert isinstance(operation, CheckOperation)
        assert operation.name == 'custom'
        assert 'admin_count' in operation.logic
        
        # Test that we can access the logic content
        logic = operation.logic
        assert 'result = False' in logic
        assert 'fetched_value' in logic
        assert 'isinstance(fetched_value, list)' in logic
        assert 'admin_count' in logic
        assert 'result = True' in logic
    
    def test_check_operation_structure_validation(self):
        """Test that CheckOperation structure is properly validated."""
        # Test that CheckOperation requires both name and logic
        with pytest.raises(Exception):  # Should raise validation error
            CheckOperation()  # Missing required fields
        
        # Test that CheckOperation accepts valid data
        valid_operation = CheckOperation(
            name='custom',
            logic='result = True'
        )
        assert valid_operation.name == 'custom'
        assert valid_operation.logic == 'result = True'
        
        # Test that CheckOperation accepts different operation names
        operation_names = ['equals', 'contains', 'greater_than', 'custom']
        for op_name in operation_names:
            operation = CheckOperation(
                name=op_name,
                logic='result = True' if op_name == 'custom' else ''
            )
            assert operation.name == op_name 