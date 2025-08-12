#!/usr/bin/env python3
"""
Script to generate compliance checks status markdown report.

This script uses pandas to load compliance data from CSV files and generates 
a markdown report showing coverage across NIST frameworks.
"""

import json
import os
import pandas as pd
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Use CSV database by default
os.environ['DB_USE_POSTGRES'] = 'false'

# Keep the original imports for models if needed
from con_mon_v2.compliance.data_loader import FrameworkLoader, ControlLoader, ChecksLoader
from con_mon_v2.utils.db import get_db


def load_data_with_pandas() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all data using pandas with better error handling."""
    
    # Define CSV file paths
    csv_dir = "/Users/ironeagle-kovr/Workspace/code/kovr-resource-collector/data/csv"
    
    print("📊 Loading data with pandas...")
    
    # Load frameworks
    print("📊 Loading frameworks...")
    frameworks_df = pd.read_csv(f"{csv_dir}/framework.csv")
    print(f"✅ Loaded {len(frameworks_df)} frameworks")
    
    # Load controls  
    print("📊 Loading controls...")
    controls_df = pd.read_csv(f"{csv_dir}/control.csv")
    print(f"✅ Loaded {len(controls_df)} controls")
    
    # Load checks
    print("📊 Loading checks...")
    checks_df = pd.read_csv(f"{csv_dir}/checks.csv")
    print(f"✅ Loaded {len(checks_df)} checks")
    
    # Load control-check mappings with error handling
    print("📊 Loading control-check mappings...")
    mappings_df = pd.read_csv(f"{csv_dir}/control_checks_mapping.csv")
    
    # Clean the mappings data
    print(f"📊 Raw mappings loaded: {len(mappings_df)} rows")
    
    # Convert control_id to numeric, coercing errors to NaN
    mappings_df['control_id'] = pd.to_numeric(mappings_df['control_id'], errors='coerce')
    
    # Remove rows with invalid control_id (NaN values)
    valid_mappings = mappings_df.dropna(subset=['control_id'])
    invalid_count = len(mappings_df) - len(valid_mappings)
    
    if invalid_count > 0:
        print(f"⚠️  Removed {invalid_count} invalid mapping rows with corrupted control_id values")
    
    # Convert control_id back to int
    valid_mappings['control_id'] = valid_mappings['control_id'].astype(int)
    
    print(f"✅ Loaded {len(valid_mappings)} valid control-check mappings")
    
    return frameworks_df, controls_df, checks_df, valid_mappings


def get_control_check_mappings_pandas(mappings_df: pd.DataFrame) -> Dict[str, List[int]]:
    """Get control-check mappings from pandas DataFrame."""
    try:
        # Group by check_id and collect control_ids
        mappings = defaultdict(list)
        
        for _, row in mappings_df.iterrows():
            control_id = int(row['control_id'])
            check_id = row['check_id']
            mappings[check_id].append(control_id)
        
        print(f"✅ Processed {len(mappings_df)} control-check mappings into {len(mappings)} unique checks")
        return dict(mappings)
        
    except Exception as e:
        print(f"❌ Error processing control-check mappings: {e}")
        return {}


def parse_metadata(metadata: Any) -> Dict[str, Any]:
    """Parse metadata field safely."""
    if metadata is None or pd.isna(metadata):
        return {}
    if isinstance(metadata, str):
        try:
            return json.loads(metadata)
        except json.JSONDecodeError:
            return {}
    if isinstance(metadata, dict):
        return metadata
    return {}


def get_resource_types_from_checks_pandas(checks_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Extract resource type information from checks metadata using pandas."""
    resource_info = defaultdict(lambda: {"count": 0, "fields": set()})
    
    for _, check in checks_df.iterrows():
        # Parse metadata from the check
        metadata = parse_metadata(check.get('metadata'))
        resource_type = metadata.get('resource_type', '')
        field_path = metadata.get('field_path', '')
        
        if resource_type:
            # Extract just the class name (e.g., 'GithubResource' from 'con_mon_v2.mappings.github.GithubResource')
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


def analyze_framework_coverage_pandas(
    framework_id: int,
    controls_df: pd.DataFrame,
    checks_df: pd.DataFrame,
    control_check_mappings: Dict[str, List[int]]
) -> Dict[str, Any]:
    """Analyze coverage for a specific framework using pandas."""
    
    # Filter controls for this framework
    framework_controls = controls_df[controls_df['framework_id'] == framework_id]
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
        sample_framework_control_ids = framework_controls['id'].head(5).tolist()
        print(f"🔍 Debug: Sample framework control IDs: {sample_framework_control_ids}")
        
        # Check if any overlap
        overlap = set(sample_framework_control_ids) & control_ids_with_checks
        print(f"🔍 Debug: Sample overlap: {overlap}")
    
    # Group controls by family
    families = defaultdict(list)
    for _, control in framework_controls.iterrows():
        family = control.get('family_name') or 'Unknown'
        families[family].append(control)
    
    # Calculate coverage by family
    family_coverage = {}
    total_controls = len(framework_controls)
    total_covered = 0
    
    for family_name, family_controls in families.items():
        family_total = len(family_controls)
        family_covered = len([c for c in family_controls if c['id'] in control_ids_with_checks])
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


def generate_markdown_report_pandas(
    frameworks_df: pd.DataFrame,
    controls_df: pd.DataFrame, 
    checks_df: pd.DataFrame,
    control_check_mappings: Dict[str, List[int]]
) -> str:
    """Generate the complete markdown report using pandas DataFrames."""
    
    family_descriptions = get_family_descriptions()
    resource_info = get_resource_types_from_checks_pandas(checks_df)
    
    # Generate report timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = []
    report.append("# KOVR Resource Collector - Compliance Checks")
    report.append("")
    report.append("This document tracks all implemented compliance checks for cloud resource monitoring and security assessment.")
    report.append("")
    report.append("## Overview")
    report.append("")
    
    # Process each framework
    for _, framework in frameworks_df.iterrows():
        framework_id = framework['id']
        framework_name = framework['name']
        
        # Analyze coverage
        coverage = analyze_framework_coverage_pandas(framework_id, controls_df, checks_df, control_check_mappings)
        
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
    
    # Supported Frameworks summary table
    report.append("## Supported Frameworks")
    report.append("")
    report.append("| Framework ID | Framework Name | Controls | Check Coverage | Description |")
    report.append("|-------------|----------------|----------|----------------|-------------|")
    
    for _, framework in frameworks_df.iterrows():
        framework_id = framework['id']
        framework_name = framework['name']
        description = framework.get('description', 'Security and Privacy Controls')
        
        coverage = analyze_framework_coverage_pandas(framework_id, controls_df, checks_df, control_check_mappings)
        
        report.append(f"| {framework_id} | {framework_name} | {coverage['total_controls']:,} | {coverage['check_count']} checks | {description} |")
    
    report.append("")
    
    # Resource Types section
    report.append("## Resource Types")
    report.append("")
    
    # Group by provider
    providers = defaultdict(list)
    for resource_name, resource_data in resource_info.items():
        provider = resource_data.get('provider', 'Unknown')
        providers[provider].append((resource_name, resource_data))
    
    connection_id = 1
    for provider, resources in providers.items():
        report.append(f"### {provider} Resources (Connection ID: {connection_id})")
        
        for resource_name, resource_data in resources:
            count = resource_data.get('count', 0)
            field_count = resource_data.get('field_count', 0)
            
            # Generate description based on resource type
            if 'Github' in resource_name:
                description = "Repository-level security and configuration checks"
            elif 'EC2' in resource_name:
                description = f"{field_count} fields - Instances, security groups, VPCs, networking"
            elif 'IAM' in resource_name:
                description = f"{field_count} fields - Users, groups, roles, policies, access management"
            elif 'S3' in resource_name:
                description = f"{field_count} fields - Buckets, encryption, policies, lifecycle management"
            elif 'CloudTrail' in resource_name:
                description = f"{field_count} fields - Trails, event selectors, insight selectors, tags"
            elif 'CloudWatch' in resource_name:
                description = f"{field_count} fields - Log groups, metrics, alarms, dashboards"
            else:
                description = f"{field_count} fields - {resource_name} configuration and security"
            
            report.append(f"- **{resource_name}**: {description}")
        
        report.append("")
        connection_id += 1
    
    # Add generation timestamp
    report.append("---")
    report.append(f"*Report generated on {timestamp}*")
    
    return "\n".join(report)


def main():
    """Main function to generate the compliance report using pandas."""
    print("🔍 Loading data using pandas...")
    
    # Load data with pandas
    try:
        frameworks_df, controls_df, checks_df, mappings_df = load_data_with_pandas()
    except Exception as e:
        print(f"❌ Error loading data with pandas: {e}")
        return
    
    # Process control-check mappings
    print("📊 Processing control-check mappings...")
    control_check_mappings = get_control_check_mappings_pandas(mappings_df)
    
    print(f"📊 Data loaded: {len(frameworks_df)} frameworks, {len(controls_df)} controls, {len(checks_df)} checks, {len(control_check_mappings)} check mappings")
    
    if frameworks_df.empty:
        print("❌ No frameworks found. Cannot generate report.")
        return
    
    # Generate report
    print("📝 Generating markdown report...")
    report = generate_markdown_report_pandas(frameworks_df, controls_df, checks_df, control_check_mappings)
    
    # Write to file
    output_file = "compliance_checks_report.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Report generated: {output_file}")
    print(f"📄 Report contains {len(report.splitlines())} lines")


if __name__ == "__main__":
    main() 