import os
import sys

# Add the project root to sys.path so we can import con_mon modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from con_mon.connectors import get_connector_by_id, get_connector_input_by_id


def main(
    connector_type: str,
):
    # Show which resources.yaml file is being validated
    resources_yaml_path = os.path.join(os.path.dirname(__file__), 'resources.yaml')
    print(f"🔍 Validating resources from: {resources_yaml_path}")
    
    connector_service = get_connector_by_id(connector_type)
    ConnectorInput = get_connector_input_by_id(connector_service)

    # Provide dummy credentials for validation
    if connector_type == 'github':
        credentials = {'GITHUB_TOKEN': 'dummy_token'}
    elif connector_type == 'aws':
        credentials = {
            'AWS_ROLE_ARN': 'dummy_arn',
            'AWS_ACCESS_KEY_ID': 'dummy_key',
            'AWS_SECRET_ACCESS_KEY': 'dummy_secret',
            'AWS_SESSION_TOKEN': 'dummy_token'
        }
    else:
        credentials = {}

    # Initialize connector with dummy credentials
    try:
        connector_input = ConnectorInput(**credentials)
        resource_collection = connector_service.fetch_data(connector_input)
        print(f"✅ Retrieved {len(resource_collection.resources)} {connector_type} resources")
    except Exception as e:
        print(f"❌ Validation failed for {connector_type}: {e}")
    
if __name__ == "__main__":
    for i, path in enumerate(sys.path[:3]):
        print(f"   {i+1}. {path}")
    if len(sys.path) > 3:
        print(f"   ... and {len(sys.path) - 3} more entries")
    print()
    
    main('github')
    main('aws')
