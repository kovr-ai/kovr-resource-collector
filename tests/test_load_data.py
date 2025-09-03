"""Tests for loading and validating resource data from all connectors."""
import json
import os
from unittest.mock import patch

from con_mon.utils.services import ResourceCollectionService


@patch.dict(os.environ, {'KOVR_AWS_ACCESS_KEY_ID': 'fake_key', 'KOVR_AWS_SECRET_ACCESS_KEY': 'fake_secret'})
@patch('providers.aws.aws_provider.AWSProvider.connect')
@patch('providers.aws.aws_provider.AWSProvider._fetch_data')
@patch('providers.gh.gh_provider.GitHubProvider.connect')
@patch('providers.gh.gh_provider.GitHubProvider._fetch_data')
def test_load_data(mock_github_fetch_data, mock_github_connect, mock_aws_fetch_data, mock_aws_connect):
    """Test loading and validating resource data for all connector types."""
    # Mock GitHub
    mock_github_connect.return_value = None
    with open('tests/mocks/github/response.json', 'r') as f:
        github_mock_data = json.load(f)
    mock_github_fetch_data.return_value = github_mock_data
    
    # Mock AWS
    mock_aws_connect.return_value = None
    with open('tests/mocks/aws/response.json', 'r') as f:
        aws_mock_data = json.load(f)
    mock_aws_fetch_data.return_value = aws_mock_data
    
    print("\n🧪 Testing Resource Data Loading and Field Path Validation...")
    
    # Test connectors
    connectors = ['aws', 'github']
    
    for connector_type in connectors:
        print(f"\n📡 Testing {connector_type.upper()} connector...")
        
        try:
            # Create service and load resource collection
            rc_service = ResourceCollectionService(connector_type)
            info, rc = rc_service.get_resource_collection()
            
            # Validate that we got resources
            assert rc is not None, f"{connector_type} resource collection should not be None"
            assert hasattr(rc, 'resources'), f"{connector_type} resource collection should have resources attribute"
            assert isinstance(rc.resources, list), f"{connector_type} resources should be a list"
            assert len(rc.resources) > 0, f"{connector_type} should have at least one resource"
            
            print(f"  ✅ Loaded {len(rc.resources)} {connector_type} resources")
            
            # Validate field paths
            validation_report = rc_service.validate_resource_field_paths(rc)
            
            # Check validation results
            assert isinstance(validation_report, dict), f"{connector_type} validation report should be a dictionary"
            assert len(validation_report) > 0, f"{connector_type} validation report should not be empty"
            
            # Analyze validation results
            total_paths = 0
            successful_paths = 0
            failed_paths = 0
            error_paths = 0
            
            for resource_name, field_results in validation_report.items():
                print(f"\n  📋 Resource: {resource_name}")
                
                for field_path, status in field_results.items():
                    total_paths += 1
                    
                    if status == "success":
                        successful_paths += 1
                        print(f"    ✅ {field_path}")
                    elif status == "not found":
                        failed_paths += 1
                        print(f"    ⚠️  {field_path} (no data)")
                    elif status == "error":
                        error_paths += 1
                        print(f"    ❌ {field_path} (error)")
                        # Errors are more serious - we should investigate
                        assert False, f"{connector_type} field path {field_path} caused an error - this indicates a structural problem"
                    else:
                        print(f"    ❓ {field_path} (unknown status: {status})")
            
            # Print summary
            print(f"\n  📊 {connector_type.upper()} Validation Summary:")
            print(f"    Total field paths: {total_paths}")
            print(f"    Successful: {successful_paths}")
            print(f"    No data: {failed_paths}")
            print(f"    Errors: {error_paths}")
            
            # Validate that we have reasonable success rate
            if total_paths > 0:
                success_rate = successful_paths / total_paths
                print(f"    Success rate: {success_rate:.1%}")
                
                # We expect at least some fields to have data
                assert successful_paths > 0, f"{connector_type} should have at least some fields with data"
                
                # No structural errors should occur
                assert error_paths == 0, f"{connector_type} should not have any field path errors"
                
                # We should have a reasonable success rate for test environments
                # In test environments with mock data, we expect at least basic fields to work
                # Lower threshold accounts for many optional fields that may not have test data
                min_success_rate = 0.02  # At least 2% of fields should have data (basic fields like id, name)
                assert success_rate >= min_success_rate, f"{connector_type} success rate ({success_rate:.1%}) is too low - at least basic fields should have data (expected >= {min_success_rate:.1%})"
            
            print(f"  ✅ {connector_type.upper()} connector validation passed")
            
        except Exception as e:
            print(f"  ❌ {connector_type.upper()} connector failed: {e}")
            raise AssertionError(f"Failed to load and validate {connector_type} resources: {e}")
    
    print("\n🎉 All connector resource loading and validation tests passed!")


if __name__ == "__main__":
    test_load_data()
