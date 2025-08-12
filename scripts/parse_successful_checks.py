#!/usr/bin/env python3
"""
Temporary script to parse through successful checks in generate_checks/prompts
Walks over the directory structure and parses YAML from output files using existing logic
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from con_mon_v2.utils.llm.generate import get_provider_resources_mapping
from con_mon_v2.connectors.models import ConnectorType
from con_mon_v2.compliance.models import Check
import yaml

def parse_yaml_from_output_file(output_file_path: Path) -> dict:
    """Parse YAML content from output file"""
    try:
        with open(output_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find YAML content - look for line starting with "checks:"
        lines = content.split('\n')
        yaml_start = None
        yaml_end = None
        
        for i, line in enumerate(lines):
            if line.startswith('checks:'):
                yaml_start = i
                break
        
        if yaml_start is None:
            print(f"⚠️ Could not find 'checks:' line in {output_file_path}")
            return None
            
        # Find the end (next line with ===)
        for i in range(yaml_start, len(lines)):
            if '=' * 80 in lines[i]:
                yaml_end = i
                break
                
        # Extract YAML content
        yaml_content = '\n'.join(lines[yaml_start:yaml_end]) if yaml_end else '\n'.join(lines[yaml_start:])
        
        # Parse YAML - this should be in the format "checks:\n- id: ..."
        parsed_yaml = yaml.safe_load(yaml_content)
        
        # Extract the first check from the checks array
        if parsed_yaml and 'checks' in parsed_yaml and parsed_yaml['checks']:
            return parsed_yaml['checks'][0]  # Return the first (and usually only) check
        else:
            print(f"⚠️ No checks found in YAML structure for {output_file_path}")
            return None
        
    except Exception as e:
        print(f"❌ Error parsing {output_file_path}: {e}")
        return None

def main():
    """Main function to walk through prompts and parse successful checks"""
    
    print("🚀 Parsing Successful Checks from generate_checks/prompts")
    print("=" * 60)
    
    # Setup paths
    prompts_dir = project_root / "data" / "generate_checks" / "prompts"
    
    if not prompts_dir.exists():
        print(f"❌ Prompts directory not found: {prompts_dir}")
        return
    
    # Get provider resources mapping (reuse existing logic)
    provider_resources = get_provider_resources_mapping()
    
    # Statistics
    stats = {
        'total_controls': 0,
        'total_output_files': 0,
        'successfully_parsed': 0,
        'parse_errors': 0,
        'check_creation_errors': 0,
        'successful_checks': 0
    }
    
    # Walk through control directories
    control_dirs = sorted(prompts_dir.iterdir())  # Process all controls
    
    for control_dir in control_dirs:
        if not control_dir.is_dir():
            continue
            
        control_name = control_dir.name
        stats['total_controls'] += 1
        
        print(f"\n📋 Processing control: {control_name}")
        
        # Walk through provider directories
        for provider_dir in control_dir.iterdir():
            if not provider_dir.is_dir():
                continue
                
            provider_name = provider_dir.name
            
            # Convert provider name to ConnectorType
            try:
                connector_type = ConnectorType(provider_name.lower())
            except ValueError:
                print(f"  ⚠️  Unknown provider: {provider_name}")
                continue
            
            print(f"  🔗 Provider: {provider_name}")
            
            # Walk through resource directories
            for resource_dir in provider_dir.iterdir():
                if not resource_dir.is_dir():
                    continue
                    
                resource_type = resource_dir.name
                print(f"    📦 Resource: {resource_type}")
                
                # Look for output file
                output_file = resource_dir / f"output_{control_name}_{provider_name}_{resource_type}.txt"
                
                if output_file.exists():
                    stats['total_output_files'] += 1
                    print(f"      📄 Found output file: {output_file.name}")
                    
                    # Parse YAML from output file
                    yaml_data = parse_yaml_from_output_file(output_file)
                    
                    if yaml_data:
                        stats['successfully_parsed'] += 1
                        print(f"      ✅ Successfully parsed YAML")
                        
                        # Try to create Check object
                        # Add missing datetime fields that from_row expects
                        from datetime import datetime
                        yaml_data['created_at'] = datetime.now()
                        yaml_data['updated_at'] = datetime.now()
                        
                        check = Check.from_row(yaml_data)
                        
                        if check:
                            stats['successful_checks'] += 1
                            print(f"      ✅ Successfully created Check: {check.name}")
                            print(f"         ID: {check.id}")
                            print(f"         Description: {check.description[:100]}...")
                            print(f"         Field Path: {check.field_path}")
                        else:
                            stats['check_creation_errors'] += 1
                            print(f"      ❌ Failed to create Check object")
                    else:
                        stats['parse_errors'] += 1
                        print(f"      ❌ Failed to parse YAML")
                else:
                    print(f"      ⚠️  No output file found")
    
    # Print final statistics
    print("\n" + "=" * 60)
    print("📊 PARSING SUMMARY")
    print("=" * 60)
    print(f"Total controls processed: {stats['total_controls']}")
    print(f"Total output files found: {stats['total_output_files']}")
    print(f"Successfully parsed YAML: {stats['successfully_parsed']}")
    print(f"Successfully created checks: {stats['successful_checks']}")
    print(f"Parse errors: {stats['parse_errors']}")
    print(f"Check creation errors: {stats['check_creation_errors']}")
    
    if stats['total_output_files'] > 0:
        parse_success_rate = (stats['successfully_parsed'] / stats['total_output_files']) * 100
        check_success_rate = (stats['successful_checks'] / stats['total_output_files']) * 100
        print(f"Parse success rate: {parse_success_rate:.1f}%")
        print(f"Check creation success rate: {check_success_rate:.1f}%")
    
    print("\n✅ Parsing complete!")

if __name__ == "__main__":
    main() 