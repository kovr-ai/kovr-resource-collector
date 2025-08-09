import yaml
from con_mon_v2.compliance.models import Control
from con_mon_v2.utils.llm.prompts import generate_checks_yaml
from con_mon_v2.utils.services import ResourceCollectionService
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.connectors.models import ConnectorType


def evaluate_check_against_rc(check, connector_type: str) -> None:
    """
    Evaluate a check against a resource collection.

    Args:
        check: Check object to test
        connector_type: Connector type (github, aws)
    """
    # Get resource collection service for the connector type
    rc_service = ResourceCollectionService(connector_type)

    # Get resource collection (uses dummy credentials in test mode)
    rc = rc_service.get_resource_collection()

    print("\n🧪 Evaluating check against resources:")
    print(f"Check: {check.name}")
    print(f"Field path: {check.field_path}")
    print("\n📝 Operation Details:")
    print("-" * 80)
    print(f"Operation type: {check.operation.name}")
    print(f"Operation details:")

    # Show metadata
    print(f"\nMetadata: {check.metadata}")
    print(f"Metadata type: {type(check.metadata)}")

    if check.metadata and hasattr(check.metadata, 'logic') and check.metadata.logic:
        print("\nCustom Logic from metadata:")
        print("-" * 40)
        print("Field Path:")
        print("-" * 40)
        print(check.metadata.field_path)  # Pretty print
        print("Formatted Custom Logic:")
        print("-" * 40)
        print(check.metadata.logic)  # Pretty print
        print("-" * 40)
    else:
        print("No custom logic found in metadata")
    print("-" * 80)

    # Evaluate check against each resource
    for resource in rc.resources:
        try:
            result = check.evaluate(resource)
            status = "✅ PASS" if result.compliant else "❌ FAIL"
            message = result.success_message if result.compliant else result.failure_message
            print(f"{status} Resource: {resource.__class__.__name__}")
            print(f"Message: {message}")
            print("-" * 40)
        except Exception as e:
            print(f"❌ Error evaluating resource {resource.__class__.__name__}: {str(e)}")
            print("-" * 40)


def generate_check_for_control(control: Control, resource_type=GithubResource, connector_type=ConnectorType.GITHUB):
    """
    Generate a check for a control using the updated LLM function.
    
    Args:
        control: Control object from compliance data
        resource_type: Resource type class (default: GithubResource)
        connector_type: ConnectorType enum value (default: ConnectorType.GITHUB)
    """
    print(f"📝 Generating check for control: {control.control_id}")
    print(f"Title: {control.name}")
    print(f"Description: {control.description}")
    print("-" * 80)

    # Generate the check using updated LLM function with connector_type
    check = generate_checks_yaml(
        control_name=control.control_id,
        control_text=control.description,
        control_title=control.name,
        control_id=control.id,  # Database ID
        resource_type=resource_type,
        connector_type=connector_type,
    )

    # Convert to YAML for display
    check_yaml = {
        'checks': [check.model_dump(exclude_none=True)]
    }
    yaml_content = yaml.dump(check_yaml, default_flow_style=False, sort_keys=False)

    print("\n✅ Generated Valid Check:")
    print(yaml_content)

    # Show raw YAML before conversion
    print("\n🔍 Raw YAML from LLM:")
    print("-" * 80)
    print(check._raw_yaml if hasattr(check, '_raw_yaml') else "Raw YAML not available")
    print("-" * 80)

    # Evaluate the check against resource collection
    connector_type_str = connector_type.value.lower() if hasattr(connector_type, 'value') else str(connector_type).lower()
    evaluate_check_against_rc(check, connector_type_str)

    # Save to file
    output_file = f"generated_check_{check.id}.yaml"
    with open(output_file, 'w') as f:
        f.write(yaml_content)
    print(f"\n💾 Check saved to {output_file}")
    
    return check
