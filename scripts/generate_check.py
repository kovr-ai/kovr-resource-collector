#!/usr/bin/env python3
"""
Script to generate compliance checks from controls using LLM.
"""

import yaml
from con_mon_v2.compliance.data_loader import get_db_loader
from con_mon_v2.utils.llm import generate_checks_yaml
from con_mon_v2.mappings.github import GithubResource

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

    # Save to file
    output_file = f"generated_check_{check.id}.yaml"
    with open(output_file, 'w') as f:
        f.write(yaml_content)
    print(f"\n💾 Check saved to {output_file}")

if __name__ == "__main__":
    generate_check_for_control() 