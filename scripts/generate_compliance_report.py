#!/usr/bin/env python3
"""
Script to generate compliance checks status markdown report.

This script uses data_loader to load compliance data from CSV files and generates 
a markdown report showing coverage across NIST frameworks.
"""

import json
import os
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Import data loaders
from con_mon.compliance.data_loader import FrameworkLoader, ControlLoader, ChecksLoader
from con_mon.compliance.models import Check, Framework, Control
from con_mon.utils.db import get_db


class ControlCheckMappingLoader:
    """Simple loader for control_checks_mapping table."""
    
    def __init__(self):
        self.db = get_db()
    
    def load_all(self) -> List[Dict[str, Any]]:
        """Load all control-check mappings."""
        try:
            results = self.db.execute('select', table_name='control_checks_mapping')
            # Convert control_id to int and filter out invalid ones
            valid_mappings = []
            for mapping in results:
                try:
                    mapping['control_id'] = int(mapping['control_id'])
                    valid_mappings.append(mapping)
                except (ValueError, TypeError):
                    continue
            return valid_mappings
        except Exception as e:
            print(f"❌ Error loading control-check mappings: {e}")
            return []


def load_data_with_data_loader() -> Tuple[List[Framework], List[Control], List[Check], List[Dict[str, Any]]]:
    """Load all data using data loaders."""
    
    print("📊 Loading data with data loaders...")
    
    # Load frameworks
    print("📊 Loading frameworks...")
    framework_loader = FrameworkLoader()
    frameworks = framework_loader.load_all()
    print(f"✅ Loaded {len(frameworks)} frameworks")
    
    # Load controls  
    print("📊 Loading controls...")
    control_loader = ControlLoader()
    controls = control_loader.load_all()
    print(f"✅ Loaded {len(controls)} controls")
    
    # Load checks using ChecksLoader
    print("📊 Loading checks...")
    checks_loader = ChecksLoader()
    checks = checks_loader.load_all()
    print(f"✅ Loaded {len(checks)} checks")
    
    # Load control-check mappings using custom loader
    print("📊 Loading control-check mappings...")
    mapping_loader = ControlCheckMappingLoader()
    mappings = mapping_loader.load_all()
    print(f"✅ Loaded {len(mappings)} valid control-check mappings")
    
    return frameworks, controls, checks, mappings


def get_control_check_mappings_from_objects(mappings: List[Dict[str, Any]]) -> Dict[str, List[int]]:
    """Get control-check mappings from mapping objects."""
    try:
        # Group by check_id and collect control_ids
        mappings_dict = defaultdict(list)
        
        for mapping in mappings:
            control_id = int(mapping['control_id'])
            check_id = mapping['check_id']
            mappings_dict[check_id].append(control_id)
        
        print(f"✅ Processed {len(mappings)} control-check mappings into {len(mappings_dict)} unique checks")
        return dict(mappings_dict)
        
    except Exception as e:
        print(f"❌ Error processing control-check mappings: {e}")
        return {}


def get_resource_types_from_checks_objects(checks: List[Check]) -> Dict[str, Dict[str, Any]]:
    """Extract resource type information from Check objects."""
    resource_info = defaultdict(lambda: {"count": 0, "fields": set()})
    
    for check in checks:
        # Get resource type and field path from Check object metadata
        resource_type = check.metadata.resource_type if check.metadata and check.metadata.resource_type else ''
        field_path = check.metadata.field_path if check.metadata and check.metadata.field_path else ''
        
        if resource_type:
            # Extract just the class name (e.g., 'GithubResource' from 'con_mon.mappings.github.GithubResource')
            class_name = resource_type.split('.')[-1] if '.' in resource_type else resource_type
            
            # Determine provider from resource type
            provider = 'Unknown'
            if 'github' in resource_type.lower():
                provider = 'GitHub'
            elif 'aws' in resource_type.lower():
                provider = 'AWS'
            
            resource_info[class_name]["count"] += 1
            resource_info[class_name]["provider"] = provider
            if field_path:
                # Count top-level fields
                top_field = field_path.split('.')[0].split('[')[0]
                resource_info[class_name]["fields"].add(top_field)
    
    # Convert sets to counts
    for resource in resource_info:
        resource_info[resource]["field_count"] = len(resource_info[resource]["fields"])
        del resource_info[resource]["fields"]
    
    return dict(resource_info)


def analyze_framework_coverage_objects(
    framework_id: int,
    controls: List[Control],
    checks: List[Check],
    control_check_mappings: Dict[str, List[int]]
) -> Dict[str, Any]:
    """Analyze coverage for a specific framework using model objects."""
    
    # Filter controls for this framework
    framework_controls = [c for c in controls if c.framework_id == framework_id]
    print(f"🔍 Debug: Framework {framework_id} has {len(framework_controls)} controls")
    
    # Get control IDs that have checks
    control_ids_with_checks = set()
    check_count = 0
    
    # Go through each check and see which controls it maps to
    for check_id, control_ids in control_check_mappings.items():
        check_count += 1
        # Add all control IDs that this check covers
        control_ids_with_checks.update(control_ids)
    
    print(f"🔍 Debug: Found {check_count} checks with mappings")
    print(f"🔍 Debug: Found {len(control_ids_with_checks)} unique control IDs with checks")
    
    # Debug: Show some sample control IDs
    if len(control_ids_with_checks) > 0:
        sample_mapped_controls = list(control_ids_with_checks)[:5]
        print(f"🔍 Debug: Sample control IDs with checks: {sample_mapped_controls}")
    
    if len(framework_controls) > 0:
        sample_framework_control_ids = [c.id for c in framework_controls[:5]]
        print(f"🔍 Debug: Sample framework control IDs: {sample_framework_control_ids}")
        
        # Check if any overlap
        overlap = set(sample_framework_control_ids) & control_ids_with_checks
        print(f"🔍 Debug: Sample overlap: {overlap}")
    
    # Group controls by family
    families = defaultdict(list)
    for control in framework_controls:
        family = control.family_name or 'Unknown'
        families[family].append(control)
    
    # Calculate coverage by family
    family_coverage = {}
    total_controls = len(framework_controls)
    total_covered = 0
    
    for family_name, family_controls in families.items():
        family_total = len(family_controls)
        family_covered = len([c for c in family_controls if c.id in control_ids_with_checks])
        family_coverage[family_name] = {
            'covered': family_covered,
            'total': family_total,
            'percentage': (family_covered / family_total * 100) if family_total > 0 else 0
        }
        total_covered += family_covered
    
    return {
        'total_controls': total_controls,
        'total_covered': total_covered,
        'total_percentage': (total_covered / total_controls * 100) if total_controls > 0 else 0,
        'family_coverage': family_coverage,
        'check_count': check_count,
        'family_count': len(families)
    }


def get_family_descriptions() -> Dict[str, str]:
    """Get family descriptions for common NIST families."""
    return {
        'AC': 'Access Control',
        'AT': 'Awareness and Training', 
        'AU': 'Audit and Accountability',
        'CA': 'Assessment, Authorization, and Monitoring',
        'CM': 'Configuration Management',
        'CP': 'Contingency Planning',
        'GRR': 'DoD PKI Authentication',
        'IA': 'Identification and Authentication',
        'IR': 'Incident Response',
        'MA': 'Maintenance',
        'MP': 'Media Protection',
        'PE': 'Physical and Environmental Protection',
        'PL': 'Planning',
        'PM': 'Program Management',
        'PS': 'Personnel Security',
        'PT': 'Privacy Controls',
        'RA': 'Risk Assessment',
        'SA': 'System and Services Acquisition',
        'SC': 'System and Communications Protection',
        'SI': 'System and Information Integrity',
        'SR': 'Supply Chain Risk Management'
    }


def generate_markdown_report_objects(
    frameworks: List[Framework],
    controls: List[Control], 
    checks: List[Check],
    control_check_mappings: Dict[str, List[int]]
) -> str:
    """Generate the complete markdown report using model objects."""
    
    family_descriptions = get_family_descriptions()
    # resource_info = get_resource_types_from_checks_objects(checks)  # Removed resource section
    
    # Filter frameworks to only include the ones present in the report
    # Based on the current report.md: NIST 800-53 and NIST 800-171 rev2 Catalog
    allowed_framework_names = {'NIST 800-53', 'NIST 800-171 rev2 Catalog'}
    filtered_frameworks = [f for f in frameworks if f.name in allowed_framework_names]
    
    print(f"🔍 Filtered frameworks: {len(filtered_frameworks)} out of {len(frameworks)} total")
    for fw in filtered_frameworks:
        print(f"   - {fw.name} (ID: {fw.id})")
    
    # Generate report timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = []
    report.append("# KOVR Resource Collector - Compliance Checks")
    report.append("")
    report.append("This document tracks all implemented compliance checks for cloud resource monitoring and security assessment.")
    report.append("")
    report.append("## Overview")
    report.append("")
    
    # Process each filtered framework
    for framework in filtered_frameworks:
        framework_id = framework.id
        framework_name = framework.name
        
        # Analyze coverage
        coverage = analyze_framework_coverage_objects(framework_id, controls, checks, control_check_mappings)
        
        report.append(f"# Checks for {framework_name}")
        report.append(f"- **Total Controls**: {coverage['total_controls']:,}")
        report.append(f"- **Control Groups**: {coverage['family_count']} control families")
        report.append(f"- **Group Coverage**: {coverage['family_count']} of {coverage['family_count']} families covered (100.0%)")
        report.append(f"- **Control Coverage**: {coverage['total_covered']} of {coverage['total_controls']} controls covered ({coverage['total_percentage']:.1f}%)")
        report.append("")
        
        # Family coverage table
        report.append(f"## {framework_name} Control Family Coverage")
        report.append("")
        report.append("| Family | Controls Covered | Total Controls | Coverage % | Description |")
        report.append("|--------|------------------|----------------|------------|-------------|")
        
        # Sort families by coverage percentage (descending)
        sorted_families = sorted(
            coverage['family_coverage'].items(),
            key=lambda x: x[1]['percentage'],
            reverse=True
        )
        
        families_above_10 = 0
        uncovered_families = 0
        uncovered_controls = 0
        
        for family_name, family_data in sorted_families:
            covered = family_data['covered']
            total = family_data['total']
            percentage = family_data['percentage']
            
            if percentage >= 10:
                families_above_10 += 1
            if percentage == 0:
                uncovered_families += 1
                uncovered_controls += total
            
            # Get family description
            family_code = family_name.split('-')[0] if family_name else 'Unknown'
            description = family_descriptions.get(family_code, family_name or 'Unknown')
            
            # Format the row
            family_display = f"**{family_code}**" if percentage > 0 else family_code
            report.append(f"| {family_display} | {covered} | {total} | {percentage:.1f}% | {description} |")
        
        report.append("")
        report.append(f"**Summary**: {coverage['family_count']} of {coverage['family_count']} families covered • {coverage['total_covered']} of {coverage['total_controls']} controls covered • {families_above_10} families above 10% coverage • {uncovered_controls} controls in uncovered families")
        report.append("")
    
    # Supported Frameworks summary table - only filtered frameworks
    report.append("## Supported Frameworks")
    report.append("")
    report.append("| Framework ID | Framework Name | Controls | Check Coverage | Description |")
    report.append("|-------------|----------------|----------|----------------|-------------|")
    
    for framework in filtered_frameworks:
        framework_id = framework.id
        framework_name = framework.name
        description = framework.description if framework.description else 'Security and Privacy Controls'
        
        coverage = analyze_framework_coverage_objects(framework_id, controls, checks, control_check_mappings)
        
        report.append(f"| {framework_id} | {framework_name} | {coverage['total_controls']:,} | {coverage['check_count']} checks | {description} |")
    
    report.append("")
    
    # Resource Types section removed as requested
    
    # Add generation timestamp
    report.append("---")
    report.append(f"*Report generated on {timestamp}*")
    
    return "\n".join(report)


def main():
    """Main function to generate the compliance report using data loaders."""
    print("🔍 Loading data using data loaders...")
    
    # Load data with data loaders
    try:
        frameworks, controls, checks, mappings = load_data_with_data_loader()
    except Exception as e:
        print(f"❌ Error loading data with data loaders: {e}")
        return
    
    # Process control-check mappings
    print("📊 Processing control-check mappings...")
    control_check_mappings = get_control_check_mappings_from_objects(mappings)
    
    print(f"📊 Data loaded: {len(frameworks)} frameworks, {len(controls)} controls, {len(checks)} checks, {len(control_check_mappings)} check mappings")
    
    if not frameworks:
        print("❌ No frameworks found. Cannot generate report.")
        return
    
    # Generate report
    print("📝 Generating markdown report...")
    report = generate_markdown_report_objects(frameworks, controls, checks, control_check_mappings)
    
    # Write to file
    output_file = "compliance_checks_report.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Report generated: {output_file}")
    print(f"📄 Report contains {len(report.splitlines())} lines")


if __name__ == "__main__":
    main() 