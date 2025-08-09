#!/usr/bin/env python3
"""
Script to generate compliance checks from controls using LLM.
"""

import yaml
from con_mon_v2.compliance.data_loader import get_db_loader
from con_mon_v2.utils.llm import generate_checks_yaml
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.utils.services import ResourceCollectionService


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


def generate_check_for_control():
    # Get the database loader
    loader = get_db_loader()
    
    # Load all controls
    controls = loader.load_controls()
    
    # For example, let's use AC-2 (Account Management)
    ac2_control = next(
        (c for c in controls if c.control_id == "AC-2"),
        None
    )
    
    if not ac2_control:
        print("❌ Control AC-2 not found")
        return
    
    print(f"📝 Generating check for control: {ac2_control.control_id}")
    print(f"Title: {ac2_control.name}")
    print(f"Description: {ac2_control.description}")
    print("-" * 80)
    
    # Generate the check using LLM
    check = generate_checks_yaml(
        control_name=ac2_control.control_id,
        control_text=ac2_control.description,
        control_title=ac2_control.name,
        control_id=ac2_control.id,  # Database ID
        resource_type=GithubResource,  # or "aws" for AWS resources
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
    evaluate_check_against_rc(check, "github")  # or "aws" for AWS resources
    
    # Save to file
    output_file = f"generated_check_{check.id}.yaml"
    with open(output_file, 'w') as f:
        f.write(yaml_content)
    print(f"\n💾 Check saved to {output_file}")


if __name__ == "__main__":
    generate_check_for_control() 