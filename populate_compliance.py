#!/usr/bin/env python3
"""
Populate and display cybersecurity compliance data using the con_mon compliance module.
This script demonstrates loading frameworks, controls, standards, and their relationships from the database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from con_mon.compliance import get_db_loader


def main():
    """Load and display compliance framework data."""
    
    print("🛡️  **COMPLIANCE DATA LOADER**")
    print("=" * 80)
    print("Loading cybersecurity frameworks, controls, and standards...")
    print()
    
    try:
        # Get database loader instance
        db_loader = get_db_loader()
        
        # Load all framework data with relationships
        frameworks, standards, controls_with_standards, mappings = db_loader.populate_all_data()
        
        print("\n" + "=" * 80)
        print("📊 **COMPLIANCE OVERVIEW**")
        print("=" * 80)
        
        # Display summary statistics
        total_framework_controls = sum(len(fw.controls) for fw in frameworks)
        total_standard_controls = sum(len(std.controls) for std in standards)
        avg_controls_per_framework = total_framework_controls / len(frameworks) if frameworks else 0
        avg_controls_per_standard = total_standard_controls / len(standards) if standards else 0
        
        print(f"📋 Data Summary:")
        print(f"   • Frameworks: {len(frameworks)}")
        print(f"   • Standards: {len(standards)}")
        print(f"   • Control-Standard Mappings: {len(mappings)}")
        print(f"   • Total Controls: {total_framework_controls}")
        print(f"   • Average Controls per Framework: {avg_controls_per_framework:.1f}")
        print(f"   • Average Controls per Standard: {avg_controls_per_standard:.1f}")
        
        print("\n" + "=" * 80)
        print("🏛️  **FRAMEWORKS**")
        print("=" * 80)
        
        # Display frameworks with their controls
        for i, framework in enumerate(frameworks, 1):
            print(f"\n{i}. {framework.name}")
            print(f"   • Version: {framework.version or 'N/A'}")
            print(f"   • Status: {framework.status}")
            print(f"   • Controls: {len(framework.controls)}")
            print(f"   • Description: {framework.description[:100]}..." if framework.description else "   • Description: N/A")
            
            # Show sample controls
            if framework.controls:
                print(f"   • Sample Controls:")
                for j, control in enumerate(framework.controls[:3]):
                    print(f"     {j+1}. {control.control_id} - {control.name[:60]}...")
                if len(framework.controls) > 3:
                    print(f"     ... and {len(framework.controls) - 3} more controls")
        
        print("\n" + "=" * 80)
        print("📊 **STANDARDS**")
        print("=" * 80)
        
        # Display standards with their mapped controls
        for i, standard in enumerate(standards, 1):
            print(f"\n{i}. {standard.name}")
            print(f"   • Status: {standard.status}")
            print(f"   • Mapped Controls: {len(standard.controls)}")
            print(f"   • Description: {standard.description[:100]}..." if standard.description else "   • Description: N/A")
            
            # Show sample controls
            if standard.controls:
                print(f"   • Sample Controls:")
                for j, control in enumerate(standard.controls[:3]):
                    print(f"     {j+1}. {control.control_id} - {control.name[:60]}...")
                if len(standard.controls) > 3:
                    print(f"     ... and {len(standard.controls) - 3} more controls")
        
        print("\n" + "=" * 80)
        print("🔧 **CONTROL-STANDARD RELATIONSHIPS**")
        print("=" * 80)
        
        # Find controls mapped to multiple standards
        multi_standard_controls = [c for c in controls_with_standards if len(c.standards) > 3]
        multi_standard_controls.sort(key=lambda c: len(c.standards), reverse=True)
        
        print(f"📈 Found {len(multi_standard_controls)} controls mapped to 4+ standards")
        
        # Show most connected controls
        for i, control in enumerate(multi_standard_controls[:5]):
            print(f"\n{i+1}. {control.control_id} - {control.name}")
            print(f"   • Family: {control.control_family}")
            print(f"   • Framework: {control.framework_id}")
            print(f"   • Priority: {control.priority}")
            print(f"   • Mapped to {len(control.standards)} standards:")
            
            for j, standard in enumerate(control.standards[:5]):
                print(f"     {j+1}. {standard.name}")
            if len(control.standards) > 5:
                print(f"     ... and {len(control.standards) - 5} more standards")
        
        print("\n" + "=" * 80)
        print("📈 **COMPLIANCE INSIGHTS**")
        print("=" * 80)
        
        # Find the most connected control
        most_connected = max(controls_with_standards, key=lambda c: len(c.standards))
        print(f"🏆 Most Connected Control:")
        print(f"   • {most_connected.control_id} - {most_connected.name}")
        print(f"   • Mapped to {len(most_connected.standards)} standards!")
        print(f"   • Family: {most_connected.control_family}")
        
        # Control family analysis
        family_counts = {}
        for control in controls_with_standards:
            family = control.control_family or 'Unknown'
            family_counts[family] = family_counts.get(family, 0) + 1
        
        print(f"\n📊 Control Families:")
        sorted_families = sorted(family_counts.items(), key=lambda x: x[1], reverse=True)
        for family, count in sorted_families[:5]:
            print(f"   • {family}: {count} controls")
        
        # Priority analysis
        priority_counts = {}
        for control in controls_with_standards:
            priority = control.priority or 'Unknown'
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        print(f"\n🎯 Control Priorities:")
        for priority in ['high', 'medium', 'low', 'Unknown']:
            count = priority_counts.get(priority, 0)
            if count > 0:
                print(f"   • {priority.title()}: {count} controls")
        
        print("\n" + "=" * 80)
        print("✅ **COMPLIANCE DATA LOADED SUCCESSFULLY**")
        print("=" * 80)
        print("🎉 All frameworks, standards, and controls loaded with relationships!")
        print("📊 Rich compliance data ready for analysis and reporting!")
        print("🔒 Database-driven compliance management system operational!")
        print(f"🏗️  Loaded via modern {db_loader.name} architecture!")
        
    except Exception as e:
        print(f"\n❌ **Error loading compliance data:** {e}")
        print("Please ensure:")
        print("   • Database connection is available")
        print("   • Required tables exist (framework, control, standard, standard_control_mapping)")
        print("   • Virtual environment is activated")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 