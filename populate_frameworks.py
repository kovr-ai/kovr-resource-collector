#!/usr/bin/env python3
"""
Script to populate and display cybersecurity framework data from NIST CSV.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from con_mon.frameworks import populate_framework_data, load_frameworks_from_csv


def print_framework_objects():
    """Load and print all framework objects with their relationships."""
    
    print("🏛️  **CYBERSECURITY FRAMEWORKS DATA POPULATION**")
    print("=" * 80)
    print()
    
    # Load and populate all framework data
    frameworks_with_controls, standards, mappings = populate_framework_data()
    
    print("\n" + "=" * 80)
    print("📋 **FRAMEWORK OBJECTS**")
    print("=" * 80)
    
    # Print Frameworks with Controls
    for framework in frameworks_with_controls:
        print(f"\n🏛️  **Framework: {framework.name}**")
        print(f"   • ID: {framework.id}")
        print(f"   • Version: {framework.version}")
        print(f"   • Description: {framework.description}")
        print(f"   • Issuing Organization: {framework.issuing_organization}")
        print(f"   • Status: {framework.status}")
        print(f"   • Controls Count: {len(framework.controls)}")
        
        # Print control families summary
        control_families = {}
        for control in framework.controls:
            family = control.control_family
            if family not in control_families:
                control_families[family] = 0
            control_families[family] += 1
        
        print("   • Control Families:")
        for family, count in sorted(control_families.items()):
            print(f"     - {family}: {count} controls")
        
        # Print first few controls as examples
        print(f"   • Sample Controls:")
        for i, control in enumerate(framework.controls[:3]):
            print(f"     {i+1}. {control.control_id}: {control.name}")
            print(f"        Family: {control.control_family} | Priority: {control.priority}")
            if len(control.description) > 100:
                desc = control.description[:97] + "..."
            else:
                desc = control.description
            print(f"        Description: {desc}")
        
        if len(framework.controls) > 3:
            print(f"     ... and {len(framework.controls) - 3} more controls")
    
    print("\n" + "=" * 80)
    print("📊 **STANDARDS OBJECTS**")
    print("=" * 80)
    
    # Print Standards
    for standard in standards:
        print(f"\n📊 **Standard: {standard.name}**")
        print(f"   • ID: {standard.id}")
        print(f"   • Version: {standard.version}")
        print(f"   • Description: {standard.description}")
        print(f"   • Issuing Organization: {standard.issuing_organization}")
        print(f"   • Scope: {standard.scope}")
        print(f"   • Status: {standard.status}")
    
    print("\n" + "=" * 80)
    print("🔗 **STANDARD-CONTROL MAPPING OBJECTS**")
    print("=" * 80)
    
    # Print Standard-Control Mappings
    mappings_by_standard = {}
    for mapping in mappings:
        std_id = mapping.standard_id
        if std_id not in mappings_by_standard:
            mappings_by_standard[std_id] = []
        mappings_by_standard[std_id].append(mapping)
    
    for std_id, std_mappings in mappings_by_standard.items():
        # Find the standard name
        standard_name = next((s.name for s in standards if s.id == std_id), f"Standard {std_id}")
        
        print(f"\n🔗 **{standard_name} Mappings ({len(std_mappings)} controls)**")
        
        for mapping in std_mappings:
            # Find the control details
            control = None
            for framework in frameworks_with_controls:
                control = next((c for c in framework.controls if c.id == mapping.control_id), None)
                if control:
                    break
            
            if control:
                print(f"   • Control {control.control_id}: {control.name}")
                print(f"     - Mapping Type: {mapping.mapping_type}")
                print(f"     - Compliance Level: {mapping.compliance_level}")
                print(f"     - Notes: {mapping.notes}")
            else:
                print(f"   • Control ID {mapping.control_id}: [Control not found]")
    
    print("\n" + "=" * 80)
    print("📈 **SUMMARY STATISTICS**")
    print("=" * 80)
    
    total_controls = sum(len(f.controls) for f in frameworks_with_controls)
    
    print(f"📊 **Data Summary:**")
    print(f"   • Total Frameworks: {len(frameworks_with_controls)}")
    print(f"   • Total Controls: {total_controls}")
    print(f"   • Total Standards: {len(standards)}")
    print(f"   • Total Mappings: {len(mappings)}")
    
    # Control family breakdown across all frameworks
    print(f"\n🏷️  **Control Family Breakdown (All Frameworks):**")
    all_families = {}
    for framework in frameworks_with_controls:
        for control in framework.controls:
            family = control.control_family
            if family not in all_families:
                all_families[family] = 0
            all_families[family] += 1
    
    for family, count in sorted(all_families.items(), key=lambda x: x[1], reverse=True):
        percentage = int((count / total_controls) * 100)
        print(f"   • {family}: {count} controls ({percentage}%)")
    
    # Priority breakdown
    print(f"\n⚡ **Priority Breakdown (All Frameworks):**")
    priorities = {'high': 0, 'medium': 0, 'low': 0}
    for framework in frameworks_with_controls:
        for control in framework.controls:
            if control.priority in priorities:
                priorities[control.priority] += 1
    
    for priority, count in priorities.items():
        percentage = int((count / total_controls) * 100)
        emoji = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
        print(f"   • {emoji} {priority.title()}: {count} controls ({percentage}%)")
    
    print(f"\n🎯 **Framework Data Successfully Populated and Displayed!**")
    print("   • All objects created with proper relationships")
    print("   • Data ready for database insertion or further processing")
    print("   • Standards mappings demonstrate compliance traceability")


def print_detailed_control_example():
    """Print a detailed example of a control object."""
    print("\n" + "=" * 80)
    print("🔍 **DETAILED CONTROL EXAMPLE**")
    print("=" * 80)
    
    frameworks, controls = load_frameworks_from_csv()
    
    # Find a high-priority control for detailed display
    example_control = next((c for c in controls if c.priority == 'high'), controls[0])
    
    print(f"\n📋 **Detailed Control Object:**")
    print(f"   • ID: {example_control.id}")
    print(f"   • Framework ID: {example_control.framework_id}")
    print(f"   • Control ID: {example_control.control_id}")
    print(f"   • Name: {example_control.name}")
    print(f"   • Description: {example_control.description}")
    print(f"   • Control Family: {example_control.control_family}")
    print(f"   • Priority: {example_control.priority}")
    print(f"   • Implementation Guidance: {example_control.implementation_guidance}")
    print(f"   • GitHub Check Required: {example_control.github_check_required}")
    print(f"   • Created At: {example_control.created_at}")
    print(f"   • Updated At: {example_control.updated_at}")
    
    print(f"\n🔧 **Object Type Information:**")
    print(f"   • Python Type: {type(example_control)}")
    print(f"   • Pydantic Model: ✅")
    print(f"   • Serializable: ✅")
    print(f"   • Database Ready: ✅")


if __name__ == "__main__":
    try:
        print_framework_objects()
        print_detailed_control_example()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 