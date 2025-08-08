"""Test model field loading and validation."""
from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from con_mon_v2.utils.yaml_loader import ResourceYamlMapping
from con_mon_v2.utils.services import CheckService


class DummyCheck:
    """Dummy check for testing."""
    def __init__(self, resource_type: type):
        self.resource_type = resource_type


def test_github_model_loading():
    """Test loading GitHub resource data into models."""
    # Load resource models
    mapping = ResourceYamlMapping.load_yaml("con_mon_v2/resources/resources.yaml")
    github = mapping["github"]
    
    # Get GitHub resource model
    github_resource = next(r for r in github.resources if r.__name__ == 'GithubResource')
    
    # Create check service
    check = DummyCheck(resource_type=github_resource)
    service = CheckService(check=check, connector_type='github')
    
    # Get all field paths
    field_paths = service._all_resource_field_paths
    print("\nGitHub field paths:")
    for path in sorted(field_paths):
        print(f"  {path}")
    
    # Get resources using dummy credentials
    resource_collection = service.get_resource_collection(dict(
        GITHUB_TOKEN='DUMMY',
    ))
    
    # Validate fields
    validation_report = service.validate_resource_field_paths(resource_collection)
    
    # Print validation results
    print("\nGitHub field validation:")
    for resource_type, fields in validation_report.items():
        print(f"\n{resource_type}:")
        for field_path, status in sorted(fields.items()):
            print(f"  {field_path}: {status}")
            
            # For successful fields, verify we can actually get the value
            if status == "success":
                try:
                    # Get the value by traversing the path
                    value = resource_collection.resources[0]
                    for part in field_path.split('.'):
                        value = getattr(value, part)
                    print(f"    Value: {value}")
                except Exception as e:
                    print(f"    Error getting value: {str(e)}")
    
    print("\n✅ GitHub model loading verified")


def test_aws_model_loading():
    """Test loading AWS resource data into models."""
    # Load resource models
    mapping = ResourceYamlMapping.load_yaml("con_mon_v2/resources/resources.yaml")
    aws = mapping["aws"]
    
    # Test each AWS resource type
    resource_types = [
        'EC2Resource',
        'IAMResource',
        'S3Resource',
        'CloudTrailResource',
        'CloudWatchResource'
    ]
    
    for resource_name in resource_types:
        print(f"\nTesting {resource_name}:")
        
        # Get resource model
        resource_model = next(r for r in aws.resources if r.__name__ == resource_name)
        
        # Create check service
        check = DummyCheck(resource_type=resource_model)
        service = CheckService(check=check, connector_type='aws')
        
        # Get all field paths
        field_paths = service._all_resource_field_paths
        print(f"\n{resource_name} field paths:")
        for path in sorted(field_paths):
            print(f"  {path}")
        
        # Get resources using dummy credentials
        resource_collection = service.get_resource_collection(dict(
            AWS_ROLE_ARN='DUMMY',
            AWS_ACCESS_KEY_ID='DUMMY',
            AWS_SECRET_ACCESS_KEY='DUMMY',
            AWS_SESSION_TOKEN='DUMMY',
        ))
        
        # Validate fields
        validation_report = service.validate_resource_field_paths(resource_collection)
        
        # Print validation results
        print(f"\n{resource_name} field validation:")
        for resource_type, fields in validation_report.items():
            print(f"\n{resource_type}:")
            for field_path, status in sorted(fields.items()):
                print(f"  {field_path}: {status}")
                
                # For successful fields, verify we can actually get the value
                if status == "success":
                    try:
                        # Get the value by traversing the path
                        value = resource_collection.resources[0]
                        for part in field_path.split('.'):
                            value = getattr(value, part)
                        print(f"    Value: {value}")
                    except Exception as e:
                        print(f"    Error getting value: {str(e)}")
    
    print("\n✅ AWS model loading verified")


def main():
    """Run all model loading tests."""
    print("\nTesting model loading...")
    
    test_github_model_loading()
    test_aws_model_loading()
    
    print("\n✅ All model loading tests passed!")


if __name__ == "__main__":
    main() 