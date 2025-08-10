#!/usr/bin/env python3
"""
LLM-Powered Check Generation Script

This script demonstrates how to use the LLM integration to automatically generate
compliance checks from control descriptions.
"""

import os
import sys
import yaml
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from con_mon_v2.compliance.models import Control
from con_mon_v2.utils.llm.prompts import (
    generate_checks
)
from con_mon_v2.mappings.github import GithubResource
from con_mon_v2.connectors.models import ConnectorType


def main():
    """Main function to demonstrate LLM check generation."""
    
    # Sample control for testing
    control_data = {
        'control_name': 'AC-2',
        'control_text': '''
        Account Management: The organization:
        a. Identifies and selects the following types of information system accounts to support organizational missions/business functions: [Assignment: organization-defined information system account types];
        b. Assigns account managers for information system accounts;
        c. Establishes conditions for group and role membership;
        d. Specifies authorized users of the information system, group and role membership, and access authorizations (i.e., privileges) and other attributes (as required) for each account;
        e. Requires approvals by [Assignment: organization-defined personnel or roles] for requests to create information system accounts;
        f. Creates, enables, modifies, disables, and removes information system accounts in accordance with [Assignment: organization-defined procedures or conditions];
        g. Monitors the use of information system accounts;
        h. Notifies account managers: (1) When accounts are no longer required; (2) When users are terminated or transferred; and (3) When individual information system usage or need-to-know changes;
        i. Authorizes access to the information system based on: (1) A valid access authorization; (2) Intended system usage; and (3) Other attributes as required by the organization or associated missions/business functions;
        j. Reviews accounts for compliance with account management requirements [Assignment: organization-defined frequency]; and
        k. Establishes a process for reissuing shared/group account credentials (if deployed) when individuals are removed from the group.
        ''',
        'control_title': 'Account Management',
        'control_id': 1,
        'resource_type': GithubResource,
    }
    
    print("🚀 LLM Check Generation Demo")
    print("=" * 60)
    print(f"Control: {control_data['control_name']}")
    print(f"Title: {control_data['control_title']}")
    print(f"Resource Type: {control_data['resource_type'].__name__}")
    print()
    
    try:
        print("📝 Generating checks using LLM...")
        
        # Generate checks for all connector types
        checks = generate_checks(
            control_name=control_data['control_name'],
            control_text=control_data['control_text'],
            control_title=control_data['control_title'],
            control_id=control_data['control_id'],
            resource_type=control_data['resource_type'],
            # LLM parameters
            model_id='anthropic.claude-3-sonnet-20240229-v1:0',
            max_tokens=4000,
            temperature=0.1
        )
        
        print(f"✅ Successfully generated {len(checks)} checks")
        
        # Process each generated check
        for i, check in enumerate(checks, 1):
            print(f"\n{'='*60}")
            print(f"📋 CHECK {i}/{len(checks)}")
            print(f"{'='*60}")
            
            # Display check details
            print(f"ID: {check.id}")
            print(f"Name: {check.name}")
            print(f"Description: {check.description}")
            print(f"Category: {check.category}")
            print(f"Resource Type: {check.metadata.resource_type}")
            print(f"Field Path: {check.metadata.field_path}")
            print(f"Severity: {check.metadata.severity}")
            print(f"Tags: {', '.join(check.metadata.tags)}")
            
            # Show operation details
            print(f"\n🔧 Operation Details:")
            print(f"Type: {check.metadata.operation.name}")
            if check.metadata.operation.logic:
                print(f"Custom Logic:")
                print("-" * 40)
                print(check.metadata.operation.logic)
                print("-" * 40)
            
            # Show output statements
            print(f"\n📢 Output Statements:")
            print(f"Success: {check.output_statements.success}")
            print(f"Failure: {check.output_statements.failure}")
            print(f"Partial: {check.output_statements.partial}")
            
            # Show fix details
            print(f"\n🔧 Fix Details:")
            print(f"Description: {check.fix_details.description}")
            print(f"Instructions: {check.fix_details.instructions}")
            print(f"Estimated Date: {check.fix_details.estimated_date}")
            print(f"Automation Available: {check.fix_details.automation_available}")
            
            # Convert to YAML for saving
            check_dict = check.model_dump(exclude_none=True)
            yaml_content = yaml.dump({'checks': [check_dict]}, 
                                   default_flow_style=False, 
                                   sort_keys=False,
                                   allow_unicode=True)
            
            # Save to file
            connector_name = check.metadata.resource_type.split('.')[-1].lower().replace('resource', '')
            output_file = f"generated_check_{control_data['control_name'].lower()}_{connector_name}.yaml"
            
            with open(output_file, 'w') as f:
                f.write(yaml_content)
            
            print(f"\n💾 Check saved to: {output_file}")
            
            # Show raw YAML for debugging
            if hasattr(check, '_raw_yaml'):
                print(f"\n🔍 Raw LLM Output:")
                print("-" * 40)
                print(check._raw_yaml)
                print("-" * 40)
        
        print(f"\n🎉 Generation complete! Created {len(checks)} check files.")
        
    except Exception as e:
        print(f"❌ Error generating checks: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 