from typing import Type
from con_mon_v2.compliance.models import Control
from con_mon_v2.utils.llm.prompts import generate_checks
from con_mon_v2.utils.services import ResourceCollectionService
from con_mon_v2.resources import Resource


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
    print(f"Operation type: {check.comparison_operation.name}")
    print(f"Operation details:")

    # Show metadata
    print(f"\nMetadata: {check.metadata}")
    print(f"Metadata type: {type(check.metadata)}")

    if check.metadata and hasattr(check, 'comparison_operation') and check.comparison_operation.logic:
        print("\nCustom Logic from metadata:")
        print("-" * 40)
        print("Field Path:")
        print("-" * 40)
        print(check.metadata.field_path)  # Pretty print
        print("Formatted Custom Logic:")
        print("-" * 40)
        print(check.comparison_operation.logic)  # Pretty print
        print("-" * 40)
    else:
        print("No custom logic found in metadata")
    print("-" * 80)

    # Evaluate check against each resource
    for resource in rc.resources:
        print(f"\n🔍 Evaluating against {resource.__class__.__name__}: {resource.id}")
        # Use the check's evaluate method
        results = check.evaluate([resource])

        for result in results:
            if result.passed:
                print(f"✅ {result.message}")
            else:
                print(f"❌ {result.message}")
                if result.error:
                    print(f"   Error: {result.error}")

def generate_check_for_control(
        control: Control,
        resource_model: Type[Resource],
):
    """
    Generate a check for a control using the updated LLM function.
    
    Args:
        control: Control object from compliance data
        resource_model: Resource type class (default: GithubResource)
        connector_type: ConnectorType enum value (default: ConnectorType.GITHUB)
    """
    print(f"📝 Generating check for control: {control.control_id}")
    print(f"Title: {control.name}")
    print(f"Description: {control.description}")
    print("-" * 80)

    # Generate the check using updated LLM function with connector_type
    checks = generate_checks(
        control_name=control.control_id,
        control_text=control.description,
        control_title=control.name,
        control_id=control.id,  # Database ID
        resource_model=resource_model,
    )