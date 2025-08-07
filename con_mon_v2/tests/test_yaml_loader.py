"""Test the YAML loader functionality."""
import os
from pathlib import Path
from con_mon_v2.utils.yaml_loader import ConnectorYamlMapping


def test_load_github_connector():
    """Test loading a GitHub connector configuration."""
    # Example GitHub connector configuration
    github_config = {
        "github": {
            "connector": {
                "name": "github",
                "description": "Collect GitHub data (repositories, actions, security)",
                "connector_type": "github",
                "provider_service": "providers.gh.gh_provider",
                "method": "process"
            },
            "input": {
                "GITHUB_TOKEN": "string"
            }
        }
    }

    try:
        # Load from dictionary
        connector_mapping = ConnectorYamlMapping.load_yaml(github_config)
        print("\nLoaded GitHub connector from dictionary:")
        print(f"Connector class: {connector_mapping.connector.__name__}")
        print(f"Input class: {connector_mapping.input.__name__}")
        
        # Verify class names
        assert connector_mapping.connector.__name__ == "GithubConnectorService"
        assert connector_mapping.input.__name__ == "GithubConnectorInput"
        
        # Verify input class fields
        assert 'GITHUB_TOKEN' in connector_mapping.input.__annotations__
        assert connector_mapping.input.__annotations__['GITHUB_TOKEN'] == str
        
        print("✅ GitHub connector model classes created successfully")
    except Exception as e:
        print(f"❌ Error loading GitHub connector: {str(e)}")


def test_load_aws_connector():
    """Test loading an AWS connector configuration."""
    # Example AWS connector configuration
    aws_config = {
        "aws": {
            "connector": {
                "name": "aws",
                "description": "Collect AWS cloud resources",
                "connector_type": "aws",
                "provider_service": "providers.aws.aws_provider",
                "method": "process"
            },
            "input": {
                "AWS_ROLE_ARN": "string",
                "AWS_ACCESS_KEY_ID": "string",
                "AWS_SECRET_ACCESS_KEY": "string",
                "AWS_SESSION_TOKEN": "string"
            }
        }
    }

    try:
        # Load from dictionary
        connector_mapping = ConnectorYamlMapping.load_yaml(aws_config)
        print("\nLoaded AWS connector from dictionary:")
        print(f"Connector class: {connector_mapping.connector.__name__}")
        print(f"Input class: {connector_mapping.input.__name__}")
        
        # Verify class names
        assert connector_mapping.connector.__name__ == "AWSConnectorService"
        assert connector_mapping.input.__name__ == "AWSConnectorInput"
        
        # Verify input class fields
        expected_fields = {
            'AWS_ROLE_ARN': str,
            'AWS_ACCESS_KEY_ID': str,
            'AWS_SECRET_ACCESS_KEY': str,
            'AWS_SESSION_TOKEN': str
        }
        for field_name, field_type in expected_fields.items():
            assert field_name in connector_mapping.input.__annotations__, f"Missing field: {field_name}"
            assert connector_mapping.input.__annotations__[field_name] == field_type, f"Wrong type for {field_name}"
        
        print("✅ AWS connector model classes created successfully")
    except Exception as e:
        print(f"❌ Error loading AWS connector: {str(e)}")


def test_load_from_yaml_file():
    """Test loading connectors from a YAML file."""
    # Get the path to the test YAML file
    current_dir = Path(__file__).parent
    yaml_path = current_dir / "test_connectors.yaml"

    try:
        # Load GitHub connector from file
        github_mapping = ConnectorYamlMapping.load_yaml(str(yaml_path))
        print("\nLoaded GitHub connector from file:")
        print(f"Connector class: {github_mapping.connector.__name__}")
        print(f"Input class: {github_mapping.input.__name__}")
        
        # Verify class names
        assert github_mapping.connector.__name__ == "GithubConnectorService"
        assert github_mapping.input.__name__ == "GithubConnectorInput"
        
        # Verify input class fields
        assert 'GITHUB_TOKEN' in github_mapping.input.__annotations__
        assert github_mapping.input.__annotations__['GITHUB_TOKEN'] == str
        
        print("✅ GitHub connector model classes loaded from file successfully")
    except Exception as e:
        print(f"❌ Error loading from YAML file: {str(e)}")


def main():
    """Run the test cases."""
    print("Testing GitHub connector loading from dictionary...")
    test_load_github_connector()

    print("\nTesting AWS connector loading from dictionary...")
    test_load_aws_connector()

    print("\nTesting connector loading from YAML file...")
    test_load_from_yaml_file()


if __name__ == "__main__":
    main() 