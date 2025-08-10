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
from unittest.mock import Mock, patch
from datetime import datetime

from con_mon_v2.compliance.models import (
    Check, CheckMetadata, CheckOperation, OutputStatements, 
    FixDetails
)
from con_mon_v2.compliance.models.checks import ComparisonOperationEnum
from con_mon_v2.utils.llm.prompts import ChecksPrompt
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
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
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
            'output_statements': OutputStatements(
                success='Operation test passed',
                failure='Operation test failed',
                partial='Operation test partially passed'
            ),
            'fix_details': FixDetails(
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
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_deleted=False,
                metadata=metadata,
                output_statements=OutputStatements(
                    success=f'{op_name} test passed',
                    failure=f'{op_name} test failed',
                    partial=f'{op_name} test partially passed'
                ),
                fix_details=FixDetails(
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
    
    def test_operation_expected_value_access(self, sample_check):
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
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
            metadata=metadata,
            output_statements=OutputStatements(
                success='Test passed',
                failure='Test failed',
                partial='Test partially passed'
            ),
            fix_details=FixDetails(
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


class TestCheckOperationPropertyBroken:
    """Test the broken Check.operation property to document the issue."""
    
    @pytest.fixture
    def sample_check(self) -> Check:
        """Create a sample Check object for testing."""
        return Check(
            id='test_broken_operation',
            name='test_broken_operation',
            description='Test check for broken operation property',
            category='access_control',
            created_by='system',
            updated_by='system',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
            metadata=CheckMetadata(
                resource_type='con_mon_v2.mappings.github.GithubResource',
                field_path='organization_data.members',  # Use a valid field path
                operation=CheckOperation(name='custom', logic='result = True'),
                expected_value=None,
                tags=['test'],
                severity='medium',
                category='access_control'
            ),
            output_statements=OutputStatements(
                success='Test passed',
                failure='Test failed',
                partial='Test partially passed'
            ),
            fix_details=FixDetails(
                description='Fix test',
                instructions=['Step 1'],
                estimated_date='2024-12-31',
                automation_available=False
            )
        )
    
    def test_operation_property_import_error(self, sample_check):
        """Test that accessing the comparison_operation property works correctly."""
        # The comparison_operation property should work now
        comparison_op = sample_check.comparison_operation
        assert comparison_op is not None
        assert comparison_op.name.value == 'custom'  # ComparisonOperationEnum.CUSTOM
    
    def test_evaluate_method_fails_due_to_broken_operation(self, sample_check):
        """Test that the evaluate method now works with the fixed comparison_operation property."""
        # Create a properly structured GitHub resource for testing
        github_resource = GithubResource(
            id="test_github_resource",
            source_connector="github",
            repository_data={},
            actions_data={},
            collaboration_data={},
            security_data={},
            organization_data={"members": [{"name": "user1", "role": "admin"}]},
            advanced_features_data={}
        )
        
        # The evaluate method should now work correctly
        results = sample_check.evaluate([github_resource])
        
        # Should return one result
        assert len(results) == 1
        result = results[0]
        
        # The result should be successful since we have an admin user
        assert result.passed is True
        assert "passed" in result.message.lower()
    
    def test_evaluate_method_with_empty_resources_still_fails(self, sample_check):
        """Test that even with empty resources, evaluate fails due to the broken operation property."""
        # Test with empty list - this should return empty results without hitting the operation property
        result = sample_check.evaluate([])
        assert result == []  # Should return empty list for empty input
    
    def test_evaluate_method_with_mismatched_resource_type_still_fails(self, sample_check):
        """Test that evaluate fails even when resource type doesn't match."""
        # Create a mock resource that won't match the resource_type filter
        mock_resource = Mock()
        mock_resource.id = "test_resource"
        # This resource won't be an instance of GithubResource, so should be filtered out
        
        # With mismatched resource type, it should return empty results without accessing operation
        result = sample_check.evaluate([mock_resource])
        assert result == []  # Should return empty list when no resources match the type


class TestCheckEvaluateMethodComprehensive:
    """Comprehensive tests for the evaluate method that expose real usage issues."""
    
    @pytest.fixture
    def github_resource_check(self) -> Check:
        """Create a check that targets GitHub resources."""
        return Check(
            id='github_eval_test',
            name='github_eval_test',
            description='Test GitHub resource evaluation',
            category='access_control',
            created_by='system',
            updated_by='system',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
            metadata=CheckMetadata(
                resource_type='con_mon_v2.mappings.github.GithubResource',
                field_path='organization_data.members',
                operation=CheckOperation(name='custom', logic='result = len(fetched_value) > 0'),
                expected_value=None,
                tags=['test'],
                severity='medium',
                category='access_control'
            ),
            output_statements=OutputStatements(
                success='GitHub evaluation passed',
                failure='GitHub evaluation failed',
                partial='GitHub evaluation partially passed'
            ),
            fix_details=FixDetails(
                description='Fix GitHub evaluation',
                instructions=['Step 1'],
                estimated_date='2024-12-31',
                automation_available=False
            )
        )
    
    def test_evaluate_with_real_github_resource_fails(self, github_resource_check):
        """Test that evaluate now works when called with a real GitHub resource."""
        # Create a real GitHub resource instance with all required fields
        github_resource = GithubResource(
            id="test_github_resource",
            source_connector="github",
            repository_data={},
            actions_data={},
            collaboration_data={},
            security_data={},
            organization_data={"members": [{"name": "user1", "role": "admin"}]},
            advanced_features_data={}
        )
        
        # The evaluate method should now work correctly
        results = github_resource_check.evaluate([github_resource])
        
        # Should return one result
        assert len(results) == 1
        result = results[0]
        
        # The result should be successful since we have members (len > 0)
        assert result.passed is True
        assert "passed" in result.message.lower()
    
    def test_evaluate_end_to_end_workflow_broken(self):
        """Test the complete end-to-end workflow that would be used in production."""
        # This test simulates what would happen in real usage:
        # 1. Load a check from YAML/database
        # 2. Get some resources
        # 3. Evaluate the check against the resources
        
        # Step 1: Create a check (simulating loaded from database/YAML)
        check = Check(
            id='production_test',
            name='production_test',
            description='Production-style check test',
            category='access_control',
            created_by='system',
            updated_by='system',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
            metadata=CheckMetadata(
                resource_type='con_mon_v2.mappings.github.GithubResource',
                field_path='len(organization_data.members123)',  # Get length of members
                operation=CheckOperation(name=ComparisonOperationEnum.EQUAL, logic=''),
                expected_value=3,  # Expect 3 members (matching the test data)
                tags=['production'],
                severity='high',
                category='access_control'
            ),
            output_statements=OutputStatements(
                success='Production check passed',
                failure='Production check failed',
                partial='Production check partially passed'
            ),
            fix_details=FixDetails(
                description='Fix production issue',
                instructions=['Contact admin'],
                estimated_date='2024-12-31',
                automation_available=False
            )
        )
        
        # Step 2: Create a proper GitHub resource (simulating real resource collection)
        github_resource = GithubResource(
            id="production_github_resource",
            source_connector="github",
            repository_data={},
            actions_data={},
            collaboration_data={},
            security_data={},
            organization_data={"members": [{"name": f"user{i}", "role": "member"} for i in range(3)]},
            advanced_features_data={}
        )
        
        # Step 3: Evaluate (this is what would happen in production)
        results = check.evaluate([github_resource])
        
        # Should return one result
        assert len(results) == 1
        result = results[0]
        
        # The result should be successful because we have 3 members and expect 3
        assert result.passed is False
        assert result.error
        
        # This demonstrates that the production workflow now works!

    def test_evaluate_end_to_end_workflow(self):
        """Test the complete end-to-end workflow that would be used in production."""
        # This test simulates what would happen in real usage:
        # 1. Load a check from YAML/database
        # 2. Get some resources
        # 3. Evaluate the check against the resources

        # Step 1: Create a check (simulating loaded from database/YAML)
        check = Check(
            id='production_test',
            name='production_test',
            description='Production-style check test',
            category='access_control',
            created_by='system',
            updated_by='system',
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=False,
            metadata=CheckMetadata(
                resource_type='con_mon_v2.mappings.github.GithubResource',
                field_path='len(organization_data.members)',  # Get length of members
                operation=CheckOperation(name=ComparisonOperationEnum.EQUAL, logic=''),
                expected_value=3,  # Expect 3 members (matching the test data)
                tags=['production'],
                severity='high',
                category='access_control'
            ),
            output_statements=OutputStatements(
                success='Production check passed',
                failure='Production check failed',
                partial='Production check partially passed'
            ),
            fix_details=FixDetails(
                description='Fix production issue',
                instructions=['Contact admin'],
                estimated_date='2024-12-31',
                automation_available=False
            )
        )

        # Step 2: Create a proper GitHub resource (simulating real resource collection)
        github_resource = GithubResource(
            id="production_github_resource",
            source_connector="github",
            repository_data={},
            actions_data={},
            collaboration_data={},
            security_data={},
            organization_data={"members": [{"name": f"user{i}", "role": "member"} for i in range(3)]},
            advanced_features_data={}
        )

        # Step 3: Evaluate (this is what would happen in production)
        results = check.evaluate([github_resource])

        # Should return one result
        assert len(results) == 1
        result = results[0]

        # The result should be successful because we have 3 members and expect 3
        assert result.passed is True
        assert "passed" in result.message.lower()

        # This demonstrates that the production workflow now works!


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
        
        output_statements = OutputStatements(**check_dict['output_statements'])
        fix_details = FixDetails(**check_dict['fix_details'])
        
        return Check(
            id=check_dict['id'],
            name=check_dict['name'],
            description=check_dict['description'],
            category=check_dict['category'],
            created_by=check_dict.get('created_by', 'system'),
            updated_by=check_dict.get('updated_by', 'system'),
            created_at=datetime.now(),
            updated_at=datetime.now(),
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
    
    def test_mock_check_evaluate_fails_in_real_usage(self, github_check_from_mock):
        """Test that the mock check now works when actually evaluated."""
        # Create a GitHub resource for evaluation with all required fields
        github_resource = GithubResource(
            id="mock_test_github_resource",
            source_connector="github",
            repository_data={},
            actions_data={},
            collaboration_data={},
            security_data={},
            organization_data={"members": [
                {"name": "admin1", "role": "admin"},
                {"name": "user1", "role": "member"},
                {"name": "user2", "role": "member"}
            ]},
            advanced_features_data={}
        )
        
        # The evaluate method should now work correctly
        results = github_check_from_mock.evaluate([github_resource])
        
        # Should return one result
        assert len(results) == 1
        result = results[0]
        
        # The result should be successful since we have admin users
        assert result.passed is True
        assert "passed" in result.message.lower()
    
    def test_llm_generated_check_metadata_operation_basic(self):
        """Test basic operation metadata with LLM-generated check (without evaluation)."""
        # Create a simple control for testing with all required fields
        control = Control(
            id=1,
            framework_id=1,
            control_name='AC-2',
            control_long_name='Account Management',
            control_text='The organization manages information system accounts.'
        )
        
        # Create ChecksPrompt
        prompt = ChecksPrompt(
            control_name=control.control_name,
            control_text=control.control_text,
            control_title=control.control_long_name,
            control_id=control.id,
            resource_model=GithubResource,
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
    resource_type: con_mon_v2.mappings.github.GithubResource
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
        
        # Note: We don't test evaluation here because the LLM prompt processing
        # has issues with resource_type resolution that are separate from
        # the operation property testing we're focused on
    
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