"""Integration tests for field structures defined in YAML files."""
from typing import List, Dict, Any, Type
from datetime import datetime
from pydantic import BaseModel
from con_mon_v2.utils.yaml_loader import ResourceYamlMapping
import yaml


def test_github_fields():
    """Test GitHub field structures."""
    # Load all models
    mapping = ResourceYamlMapping.load_yaml("con_mon_v2/resources/resources.yaml")
    
    # Get GitHub models
    github = mapping["github"]
    models = {model.__name__: model for model in github.nested_schemas}
    resources = {model.__name__: model for model in github.resources}
    
    # Verify we only got GitHub models
    assert set(models.keys()) == {
        'RepositoryData', 'ActionsData', 'CollaborationData',
        'SecurityData', 'OrganizationData', 'AdvancedFeaturesData'
    }
    assert set(resources.keys()) == {'GithubResource'}
    assert github.resources_collection.__name__ == 'GithubResourceCollection'
    
    # Test repository data fields
    repo_data = models['RepositoryData']
    assert 'basic_info' in repo_data.__annotations__
    basic_info = repo_data.__annotations__['basic_info']
    assert basic_info.__annotations__['id'] == int
    assert basic_info.__annotations__['name'] == str
    assert basic_info.__annotations__['private'] == bool
    assert basic_info.__annotations__['owner'] == str
    assert basic_info.__annotations__['size'] == int
    assert basic_info.__annotations__['stargazers_count'] == int
    
    # Test collaboration data fields
    collab_data = models['CollaborationData']
    assert 'issues' in collab_data.__annotations__
    issues = collab_data.__annotations__['issues']
    assert isinstance(issues, type(List[Any]))  # Should be List type
    issue_model = issues.__args__[0]  # Get item type
    assert issue_model.__annotations__['number'] == int
    assert issue_model.__annotations__['title'] == str
    assert issue_model.__annotations__['labels'] == List[str]
    
    # Test security data fields
    security_data = models['SecurityData']
    assert 'security_analysis' in security_data.__annotations__
    analysis = security_data.__annotations__['security_analysis']
    assert analysis.__annotations__['advanced_security_enabled'] == bool
    assert analysis.__annotations__['secret_scanning_enabled'] == bool
    
    print("✅ GitHub field structures verified")


def test_aws_fields():
    """Test AWS field structures."""
    # Load all models
    mapping = ResourceYamlMapping.load_yaml("con_mon_v2/resources/resources.yaml")
    
    # Get AWS models
    aws = mapping["aws"]
    resources = {model.__name__: model for model in aws.resources}
    
    # Verify we only got AWS models
    assert set(resources.keys()) == {
        'EC2Resource', 'IAMResource', 'S3Resource',
        'CloudTrailResource', 'CloudWatchResource'
    }
    assert aws.resources_collection.__name__ == 'AwsResourceCollection'
    
    # Test EC2 fields
    ec2 = resources['EC2Resource']
    assert 'instances' in ec2.__annotations__
    instances = ec2.__annotations__['instances']
    assert hasattr(instances, '__annotations__')  # Should be a model
    instance_model = instances.__annotations__
    assert instance_model['instance_type'] == str
    assert instance_model['state'] == str
    assert instance_model['security_groups'] == List[str]
    
    # Test IAM fields
    iam = resources['IAMResource']
    assert 'users' in iam.__annotations__
    users = iam.__annotations__['users']
    assert hasattr(users, '__annotations__')  # Should be a model
    user_model = users.__annotations__
    assert user_model['arn'] == str
    assert user_model['user_id'] == str
    assert user_model['access_keys'] == List[str]
    
    # Test S3 fields
    s3 = resources['S3Resource']
    assert 'buckets' in s3.__annotations__
    buckets = s3.__annotations__['buckets']
    assert hasattr(buckets, '__annotations__')  # Should be a model
    bucket_model = buckets.__annotations__
    assert bucket_model['name'] == str
    assert bucket_model['creation_date'] == str
    assert bucket_model['region'] == str
    
    # Test CloudWatch fields
    cloudwatch = resources['CloudWatchResource']
    assert 'alarms' in cloudwatch.__annotations__
    alarms = cloudwatch.__annotations__['alarms']
    assert hasattr(alarms, '__annotations__')  # Should be a model
    alarm_model = alarms.__annotations__
    assert alarm_model['alarm_name'] == str
    assert alarm_model['actions_enabled'] == bool
    assert alarm_model['threshold'] == float
    
    print("✅ AWS field structures verified")


def main():
    """Run all field structure tests."""
    print("\nTesting field structures...")
    
    test_github_fields()
    test_aws_fields()
    
    print("\n✅ All field structures verified!")


if __name__ == "__main__":
    main() 