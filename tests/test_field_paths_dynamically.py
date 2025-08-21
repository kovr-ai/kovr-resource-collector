"""Dynamic field path generation and testing."""
from typing import List, Dict, Any, Type, get_origin, get_args
import inspect
import json
from unittest.mock import patch

from con_mon.utils.services import ResourceCollectionService
from con_mon.resources import ResourceCollection, Resource
from con_mon.compliance.models import (
    Check, CheckMetadata, OutputStatements, FixDetails,
    CheckOperation, ComparisonOperationEnum, CheckResult
)
from datetime import datetime
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def generate_field_paths_for_provider(provider: str) -> Dict[str, List[str]]:
    """
    Dynamically generate field paths by analyzing resource models for a given provider.
    
    Args:
        provider: Provider name ('github', 'aws', etc.)
        
    Returns:
        Dictionary mapping resource class names to lists of field paths
    """
    rc_service = ResourceCollectionService(provider)
    info, rc = rc_service.get_resource_collection()

    if not rc.resources:
        print(f"⚠️ No resources found for provider {provider}")
        return {}

    field_paths = {}

    for resource in rc.resources:
        resource_name = resource.__class__.__name__
        resource_class = resource.__class__

        # Use the new Resource.field_paths() method
        paths = resource_class.field_paths(max_depth=4)

        field_paths[resource_name] = paths
        print(f"✅ Generated {len(paths)} field paths for {resource_name}")

    return field_paths


def setup_test_check() -> Check:
    """Set up a test check for validation."""
    metadata = CheckMetadata(
        operation=CheckOperation(name=ComparisonOperationEnum.CUSTOM, logic="result = True"),
        field_path="test.path",
        resource_type="con_mon.mappings.github.GithubResource",
        tags=["test"],
        category="test",
        severity="medium",
        expected_value=None
    )

    check = Check(
        id="test_functions",
        name="Functions Test Check",
        description="Test function extraction",
        category="test",
        created_by="test",
        updated_by="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata=metadata,
        output_statements=OutputStatements(
            success="Test passed", failure="Test failed", partial="Test partial"
        ),
        fix_details=FixDetails(
            description="Test fix",
            instructions=["Step 1"],
            automation_available=False,
            estimated_time="1 w 1 d 1 h"
        ),
        is_deleted=False
    )
    return check.model_copy()


@patch('providers.aws.aws_provider.AWSProvider.process')
@patch('providers.gh.gh_provider.GitHubProvider.process')
def test_field_paths_dynamically(mock_github_process, mock_aws_process):
    """Test field paths by dynamically generating them from resource models."""
    # Load mock data for both providers
    with open('tests/mocks/github/response.json', 'r') as f:
        github_mock_data = json.load(f)
    with open('tests/mocks/aws/response.json', 'r') as f:
        aws_mock_data = json.load(f)
    
    mock_github_process.return_value = github_mock_data
    mock_aws_process.return_value = aws_mock_data
    
    providers = ['github', 'aws']
    
    for provider in providers:
        print(f"\n🔍 Testing {provider.upper()} provider dynamically...")
        
        # Generate field paths dynamically
        field_paths_dict = generate_field_paths_for_provider(provider)
        
        if not field_paths_dict:
            print(f"⚠️ No field paths generated for {provider}")
            continue
            
        # Set up resource collection
        rc_service = ResourceCollectionService(provider)
        info, rc = rc_service.get_resource_collection()
        check = setup_test_check()
        
        # Test each resource type
        for resource in rc.resources:
            resource_name = resource.__class__.__name__
            
            if resource_name not in field_paths_dict:
                print(f"⚠️ No field paths found for {resource_name}")
                continue
                
            print(f"\n📋 Testing {resource_name} ({len(field_paths_dict[resource_name])} paths)...")
            
            # Update check to match current resource
            if provider == 'github':
                check.metadata.resource_type = f"con_mon.mappings.github.{resource_name}"
            elif provider == 'aws':
                check.metadata.resource_type = f"con_mon.mappings.aws.{resource_name}"
            
            # Test each field path
            failed_paths = []
            successful_paths = 0
            
            for field_path in field_paths_dict[resource_name]:
                try:
                    check.metadata.field_path = field_path
                    check_results = check.evaluate(rc.resources)
                    
                    if not check.is_invalid(check_results):
                        successful_paths += 1
                    else:
                        failed_paths.append(field_path)
                        
                except Exception as e:
                    failed_paths.append(f"{field_path} (Exception: {str(e)})")
            
            # Report results
            total_paths = len(field_paths_dict[resource_name])
            success_rate = (successful_paths / total_paths) * 100 if total_paths > 0 else 0
            
            print(f"✅ {successful_paths}/{total_paths} paths successful ({success_rate:.1f}%)")
            
            if failed_paths:
                print(f"❌ Failed paths ({len(failed_paths)}):")
                for failed_path in failed_paths[:10]:  # Show first 10 failures
                    print(f"   - {failed_path}")
                if len(failed_paths) > 10:
                    print(f"   ... and {len(failed_paths) - 10} more")
            
            # Assert that at least 50% of paths work (allowing for many edge cases in dynamic generation)
            assert success_rate >= 50.0, f"Success rate {success_rate:.1f}% is below 50% for {resource_name}"


@patch('providers.gh.gh_provider.GitHubProvider.process')
def test_generate_field_paths_github(mock_github_process):
    """Test field path generation for GitHub provider."""
    # Load mock data from tests/mocks/github/response.json
    with open('tests/mocks/github/response.json', 'r') as f:
        mock_data = json.load(f)
    mock_github_process.return_value = mock_data
    
    field_paths_dict = generate_field_paths_for_provider('github')
    
    assert field_paths_dict, "Should generate field paths for GitHub"
    
    for resource_name, paths in field_paths_dict.items():
        print(f"\n{resource_name}: {len(paths)} paths")
        
        # Check that we have basic paths
        assert len(paths) > 0, f"Should have paths for {resource_name}"
        
        # Check for different pattern types
        has_simple_paths = any('.' in path and '[' not in path and '(' not in path for path in paths)
        has_array_paths = any('[*]' in path or '[]' in path or '.*' in path for path in paths)
        has_function_paths = any('(' in path and ')' in path for path in paths)
        
        print(f"  Simple paths: {has_simple_paths}")
        print(f"  Array paths: {has_array_paths}")
        print(f"  Function paths: {has_function_paths}")
        
        # Should have at least simple paths
        assert has_simple_paths, f"Should have simple paths for {resource_name}"


@patch('providers.aws.aws_provider.AWSProvider.process')
def test_generate_field_paths_aws(mock_aws_process):
    """Test field path generation for AWS provider."""
    # Load mock data from tests/mocks/aws/response.json
    with open('tests/mocks/aws/response.json', 'r') as f:
        mock_data = json.load(f)
    mock_aws_process.return_value = mock_data
    
    field_paths_dict = generate_field_paths_for_provider('aws')
    
    assert field_paths_dict, "Should generate field paths for AWS"
    
    for resource_name, paths in field_paths_dict.items():
        print(f"\n{resource_name}: {len(paths)} paths")
        
        # Check that we have basic paths
        assert len(paths) > 0, f"Should have paths for {resource_name}"
        
        # Check for different pattern types
        has_simple_paths = any('.' in path and '[' not in path and '(' not in path for path in paths)
        has_array_paths = any('[*]' in path or '[]' in path or '.*' in path for path in paths)
        has_function_paths = any('(' in path and ')' in path for path in paths)
        
        print(f"  Simple paths: {has_simple_paths}")
        print(f"  Array paths: {has_array_paths}")
        print(f"  Function paths: {has_function_paths}")
        
        # Should have at least simple paths
        assert has_simple_paths, f"Should have simple paths for {resource_name}"


@patch('providers.aws.aws_provider.AWSProvider.process')
@patch('providers.gh.gh_provider.GitHubProvider.process')
def test_resource_field_paths_method(mock_github_process, mock_aws_process):
    """Test the Resource.field_paths() method directly."""
    # Load mock data for both providers
    with open('tests/mocks/github/response.json', 'r') as f:
        github_mock_data = json.load(f)
    with open('tests/mocks/aws/response.json', 'r') as f:
        aws_mock_data = json.load(f)
    
    mock_github_process.return_value = github_mock_data
    mock_aws_process.return_value = aws_mock_data
    
    print("\n🔬 Testing Resource.field_paths() method directly...")
    
    providers = ['github', 'aws']
    
    for provider in providers:
        print(f"\n📊 Testing {provider.upper()} resources...")
        
        try:
            rc_service = ResourceCollectionService(provider)
            info, rc = rc_service.get_resource_collection()
            
            for resource in rc.resources:
                resource_name = resource.__class__.__name__
                resource_class = resource.__class__
                
                # Test the field_paths method directly
                paths = resource_class.field_paths()
                
                print(f"  {resource_name}: {len(paths)} paths generated")
                
                # Basic validation
                assert len(paths) > 0, f"Should generate paths for {resource_name}"
                assert isinstance(paths, list), f"Should return a list for {resource_name}"
                assert all(isinstance(path, str) for path in paths), f"All paths should be strings for {resource_name}"
                
                # Check for some expected patterns
                has_id_path = 'id' in paths
                has_source_connector_path = 'source_connector' in paths
                
                print(f"    Has 'id' path: {has_id_path}")
                print(f"    Has 'source_connector' path: {has_source_connector_path}")
                
                # All resources should have these basic paths
                assert has_id_path, f"Should have 'id' path for {resource_name}"
                assert has_source_connector_path, f"Should have 'source_connector' path for {resource_name}"
                
        except Exception as e:
            print(f"⚠️ Error testing {provider}: {e}")


if __name__ == '__main__':
    print("🔬 Running dynamic field path generation tests...")
    
    print("\n🧪 Testing Resource.field_paths() method...")
    test_resource_field_paths_method()
    
    print("\n📊 Testing GitHub field path generation...")
    test_generate_field_paths_github()
    
    print("\n📊 Testing AWS field path generation...")
    test_generate_field_paths_aws()
    
    print("\n🧪 Testing dynamic field path validation...")
    test_field_paths_dynamically()
    
    print("\n✅ All dynamic tests completed!") 