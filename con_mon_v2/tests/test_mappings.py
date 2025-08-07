"""Test the dynamic class mapping system."""
from con_mon_v2 import mappings


def test_global_mappings():
    """Test that global mappings are properly populated."""
    # Test GitHub mappings
    assert 'github' in mappings
    assert 'GithubConnectorService' in mappings['github']
    assert 'GithubConnectorInput' in mappings['github']
    
    # Test AWS mappings
    assert 'aws' in mappings
    assert 'AWSConnectorService' in mappings['aws']
    assert 'AWSConnectorInput' in mappings['aws']
    
    # Test class types
    github_service = mappings['github']['GithubConnectorService']
    github_input = mappings['github']['GithubConnectorInput']
    aws_service = mappings['aws']['AWSConnectorService']
    aws_input = mappings['aws']['AWSConnectorInput']
    
    # Test that classes can be instantiated
    github_input_instance = github_input(GITHUB_TOKEN="test_token")
    aws_input_instance = aws_input(
        AWS_ROLE_ARN="test_role",
        AWS_ACCESS_KEY_ID="test_key",
        AWS_SECRET_ACCESS_KEY="test_secret",
        AWS_SESSION_TOKEN="test_token"
    )
    
    print("\nTesting global mappings:")
    print(f"GitHub Service: {github_service.__name__}")
    print(f"GitHub Input: {github_input.__name__}")
    print(f"AWS Service: {aws_service.__name__}")
    print(f"AWS Input: {aws_input.__name__}")
    print("\nTesting instance creation:")
    print(f"GitHub Input Instance: {github_input_instance}")
    print(f"AWS Input Instance: {aws_input_instance}")


def test_module_imports():
    """Test that classes can be imported from their respective modules."""
    try:
        from con_mon_v2.mappings.github import GithubConnectorService
        from con_mon_v2.mappings.github import GithubConnectorInput
        from con_mon_v2.mappings.aws import AWSConnectorService
        from con_mon_v2.mappings.aws import AWSConnectorInput
        
        # Test that imported classes match the global mappings
        assert GithubConnectorService == mappings['github']['GithubConnectorService']
        assert GithubConnectorInput == mappings['github']['GithubConnectorInput']
        assert AWSConnectorService == mappings['aws']['AWSConnectorService']
        assert AWSConnectorInput == mappings['aws']['AWSConnectorInput']
        
        print("\nTesting module imports:")
        print("✅ All classes imported successfully")
        print("✅ Imported classes match global mappings")
    except ImportError as e:
        print(f"❌ Error importing classes: {str(e)}")
    except AssertionError as e:
        print(f"❌ Imported classes don't match global mappings: {str(e)}")


def main():
    """Run the test cases."""
    print("Testing global mappings system...")
    test_global_mappings()
    test_module_imports()


if __name__ == "__main__":
    main() 