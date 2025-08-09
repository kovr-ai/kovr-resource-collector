"""
Tests for LLM-based check generation functionality - Common tests.

This module tests common functionality of the ChecksYamlPrompt class
that applies to all providers.
"""
import yaml
import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from con_mon_v2.utils.llm.prompts import ChecksYamlPrompt
from con_mon_v2.utils.llm.client import LLMResponse
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.connectors.models import ConnectorType


class TestChecksYamlPromptCommon:
    """Test cases for common ChecksYamlPrompt functionality."""
    
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
    
    def test_process_response_invalid_yaml(self, sample_control_data):
        """Test processing an invalid LLM response."""
        prompt = ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=GithubResource,
            connector_type=ConnectorType.GITHUB
        )
        
        invalid_response = LLMResponse(
            content="invalid yaml content: [unclosed bracket",
            model_id="mock-model",
            usage={"input_tokens": 100, "output_tokens": 50},
            stop_reason="end_turn",
            raw_response={"mock": "response"}
        )
        
        with pytest.raises(yaml.YAMLError):
            prompt.process_response(invalid_response)
    
    def test_process_response_missing_checks_key(self, sample_control_data):
        """Test processing response without 'checks' key gets auto-corrected."""
        prompt = ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=GithubResource,
            connector_type=ConnectorType.GITHUB
        )
        
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
            prompt.process_response(invalid_response)
    
    def test_process_response_multiple_checks(self, sample_control_data):
        """Test processing response with multiple checks (should fail)."""
        prompt = ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=GithubResource,
            connector_type=ConnectorType.GITHUB
        )
        
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
            prompt.process_response(invalid_response)
    
    def test_process_response_markdown_removal(self, sample_control_data):
        """Test that markdown code blocks are properly removed."""
        prompt = ChecksYamlPrompt(
            control_name=sample_control_data['control_name'],
            control_text=sample_control_data['control_text'],
            control_title=sample_control_data['control_title'],
            control_id=sample_control_data['control_id'],
            resource_type=GithubResource,
            connector_type=ConnectorType.GITHUB
        )
        
        yaml_with_markdown = """```yaml
checks:
- id: test_check
  name: test_check
  description: Test check
  category: test
  metadata:
    resource_type: GithubResource
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
        
        with patch.object(prompt, 'test_check', return_value=(True, "Test passed")):
            check = prompt.process_response(response)
        
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
                control_id=sample_control_data['control_id'],
                resource_type=GithubResource,
                connector_type=ConnectorType.GITHUB
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
                control_id=sample_control_data['control_id'],
                resource_type=GithubResource,
                connector_type=ConnectorType.GITHUB
            )
            
            formatted_prompt = prompt.format_prompt()
            assert f"category: {expected_category}" in formatted_prompt 