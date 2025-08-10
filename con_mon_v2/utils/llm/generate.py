from typing import List, Dict
from con_mon_v2.utils.services import ResourceCollectionService
from con_mon_v2.connectors import ConnectorType
from con_mon_v2.utils.yaml_loader import ResourceYamlMapping
from pathlib import Path
from .prompt import CheckPrompt
from con_mon_v2.compliance.models import Check


def get_provider_resources_mapping() -> Dict[ConnectorType, List[str]]:
    """
    Dynamically get provider to resource models mapping from con_mon_v2.mappings.
    
    Returns:
        Dictionary mapping ConnectorType to list of resource model names
    """
    # Load resource mappings from YAML
    resources_yaml = Path(__file__).parent.parent.parent / 'resources' / 'resources.yaml'
    
    if not resources_yaml.exists():
        # Fallback to hardcoded mapping if YAML not found
        return {
            ConnectorType.GITHUB: ['GithubResource'],
            ConnectorType.AWS: ['EC2Resource', 'IAMResource', 'S3Resource', 'CloudTrailResource', 'CloudWatchResource'],
        }
    
    try:
        # Load mappings using the existing YAML loader
        resource_mappings = ResourceYamlMapping.load_yaml(resources_yaml)
        
        provider_resources = {}
        
        for provider_name, mapping in resource_mappings.items():
            # Convert provider name to ConnectorType (use lowercase as that's what the enum expects)
            try:
                connector_type = ConnectorType(provider_name.lower())
            except ValueError:
                # Skip unknown connector types
                continue
            
            # Extract resource model names from the YamlModelMapping objects
            resource_names = []
            for resource_mapping in mapping.resources:
                # Get the actual model class name
                model_class = resource_mapping.pydantic_model
                resource_names.append(model_class.__name__)
            
            if resource_names:
                provider_resources[connector_type] = resource_names
        
        return provider_resources
        
    except Exception as e:
        print(f"⚠️  Warning: Failed to load dynamic provider resources: {e}")
        print("   Falling back to hardcoded mapping")
        
        # Fallback to hardcoded mapping
        return {
            ConnectorType.GITHUB: ['GithubResource'],
            ConnectorType.AWS: ['EC2Resource', 'IAMResource', 'S3Resource', 'CloudTrailResource', 'CloudWatchResource'],
        }


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


def generate_check(
        control_name: str,
        control_text: str,
        control_title: str,
        control_id: int,
        connector_type: ConnectorType,
        resource_model_name: str,
        **kwargs
) -> Check:
    """
    Generate a single check using the V2 prompt system.

    Args:
        control_name: Control identifier (e.g., "AC-2")
        control_text: Full control requirement text
        control_title: Control title/name
        control_id: Database ID of the control
        connector_type: Provider type (AWS, GitHub, etc.)
        resource_model_name: Specific resource model (e.g., "GithubResource", "EC2Resource")
        **kwargs: Additional LLM parameters

    Returns:
        Validated Check object that matches schema exactly
    """
    prompt = CheckPrompt(
        control_name=control_name,
        control_text=control_text,
        control_title=control_title,
        control_id=control_id,
        connector_type=connector_type,
        resource_model_name=resource_model_name,
    )

    return prompt.generate(**kwargs)


def generate_checks_for_all_providers(
        control_name: str,
        control_text: str,
        control_title: str,
        control_id: int,
        **kwargs
) -> List[Check]:
    """
    Generate checks for all available providers and their resource models.
    
    This function now dynamically loads provider-to-resource mappings from 
    con_mon_v2.mappings (resources.yaml) instead of using hardcoded values.

    Args:
        control_name: Control identifier
        control_text: Control requirement text
        control_title: Control title
        control_id: Database ID of the control
        **kwargs: Additional LLM parameters

    Returns:
        List of Check objects for all provider/resource combinations
    """
    checks = []

    # Get provider to resource model mapping dynamically from con_mon_v2.mappings
    # This replaces the previously hardcoded provider_resources dictionary
    provider_resources = get_provider_resources_mapping()

    for connector_type, resource_models in provider_resources.items():
        for resource_model in resource_models:
            check = generate_check(
                control_name=control_name,
                control_text=control_text,
                control_title=control_title,
                control_id=control_id,
                connector_type=connector_type,
                resource_model_name=resource_model,
                **kwargs
            )
            checks.append(check)

    return checks
