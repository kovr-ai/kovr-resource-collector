import os
import sys

# Add the project root to sys.path so we can import con_mon modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from con_mon.connectors import get_connector_by_id, get_connector_input_by_id


def main(
    connector_type: str,
    field_path: str | None = None,
) -> list:
    """
    Validate resource creation for a connector type.
    
    Args:
        connector_type: Type of connector to validate
        field_path: Optional field path to validate on the resources (e.g., "repository_data.basic_info.description")
        
    Returns:
        List of created resource instances
    """
    # Show which resources.yaml file is being validated
    resources_yaml_path = os.path.join(os.path.dirname(__file__), 'resources.yaml')
    print(f"🔍 Validating resources from: {resources_yaml_path}")
    
    # Show environment information
    print(f"🐍 Python executable: {sys.executable}")
    print(f"📂 Working directory: {os.getcwd()}")
    print(f"📁 Project root: {project_root}")
    print(f"🛤️ Python path (first 3): {sys.path[:3]}")
    
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
        
        print(f"✅ Created {connector_type} connector input")
        
        # Use the connector service to fetch data
        resource_collection = connector_service.fetch_data(connector_input)
        
        print(f"✅ Retrieved {len(resource_collection.resources)} {connector_type} resources")
        
        resources = resource_collection.resources
        
        # If field_path is provided, validate it on the first resource
        if field_path and resources:
            print(f"🔍 Testing field path: {field_path}")
            resource = resources[0]
            
            try:
                # Navigate through the field path
                field_parts = field_path.split('.')
                current_value = resource
                
                for i, part in enumerate(field_parts):
                    print(f"  Step {i+1}: Accessing '{part}' on {type(current_value).__name__}")
                    
                    if hasattr(current_value, part):
                        current_value = getattr(current_value, part)
                        print(f"    ✅ Found {type(current_value).__name__}")
                    elif isinstance(current_value, dict) and part in current_value:
                        current_value = current_value[part]
                        print(f"    ✅ Found dict value: {type(current_value).__name__}")
                    else:
                        print(f"    ❌ FAILED: Field '{part}' not found")
                        if hasattr(current_value, '__dict__'):
                            print(f"    Available attributes: {list(current_value.__dict__.keys())[:10]}...")
                        elif isinstance(current_value, dict):
                            print(f"    Available keys: {list(current_value.keys())[:10]}...")
                        else:
                            print(f"    Available attributes: {[attr for attr in dir(current_value) if not attr.startswith('_')][:10]}...")
                        break
                else:
                    # If we completed the loop without breaking
                    print(f"✅ Field path validation successful!")
                    print(f"  Final value type: {type(current_value).__name__}")
                    print(f"  Final value: {current_value}")
                    
            except Exception as e:
                print(f"❌ Field path validation failed: {e}")
        
        # Return the resources for use by other modules
        return resources
        
    except Exception as e:
        print(f"❌ Failed to create {connector_type} resources: {e}")
        return []
    
if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Usage: python validate.py <connector_type> [field_path]")
        print("Example: python validate.py aws account.limits.supported-platforms")
        sys.exit(1)
        
    connector_type = sys.argv[1]
    field_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Show Python path for debugging
    print("Python path:")
    for i, path in enumerate(sys.path[:3]):
        print(f"   {i+1}. {path}")
    if len(sys.path) > 3:
        print(f"   ... and {len(sys.path) - 3} more entries")
    print()
    
    # Run validation
    main(connector_type, field_path)
