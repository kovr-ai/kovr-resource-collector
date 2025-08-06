#!/usr/bin/env python3
"""
Generate Compliance Checks with LLM

This script demonstrates how to use the new LLM sub-module structure
to generate compliance checks from NIST control data.

Usage:
    python generate_checks_with_llm.py --control AC-2 --resource-type github
    python generate_checks_with_llm.py --analyze --control AC-3
"""

import argparse
import logging
from typing import Dict, Any

from con_mon.utils.llm import (
    get_llm_client,
    ComplianceCheckPrompt,
    ControlAnalysisPrompt,
    ChecksYamlPrompt,
    generate_compliance_check,
    analyze_control,
    generate_checks_yaml
)
from con_mon.utils.db import get_db

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_control_from_db(control_name: str) -> Dict[str, Any]:
    """
    Get control information from the database.
    
    Args:
        control_name: Control identifier (e.g., "AC-2")
        
    Returns:
        Dictionary containing control information
    """
    db = get_db()
    
    # Query for NIST 800-53 controls (framework_id = 2)
    query = """
    SELECT 
        id,
        control_name,
        control_long_name,
        control_text,
        control_discussion,
        family_name
    FROM control 
    WHERE control_name = %s 
    AND framework_id = 2 
    AND active = true
    LIMIT 1;
    """
    
    try:
        results = db.execute_query(query, (control_name,))
        if results:
            return results[0]
        else:
            logger.error(f"Control {control_name} not found in database")
            return {}
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {}


def generate_check_for_control(control_name: str, resource_type: str = "github") -> str:
    """
    Generate compliance check code for a control.
    
    Args:
        control_name: Control identifier
        resource_type: Target resource type
        
    Returns:
        Generated Python code
    """
    print(f"🔍 Fetching control data for {control_name}...")
    
    # Get control from database
    control_data = get_control_from_db(control_name)
    if not control_data:
        return ""
    
    print(f"📋 Control: {control_data['control_long_name']}")
    print(f"🏷️ Family: {control_data['family_name']}")
    
    # Generate compliance check
    print(f"🤖 Generating compliance check code...")
    
    try:
        code = generate_compliance_check(
            control_name=control_name,
            control_text=control_data['control_text'],
            resource_type=resource_type,
            control_title=control_data['control_long_name'],
            max_tokens=800,
            temperature=0.1
        )
        
        print(f"✅ Generated {len(code)} characters of code")
        return code
        
    except Exception as e:
        logger.error(f"Failed to generate compliance check: {e}")
        return ""


def analyze_control_requirements(control_name: str) -> Dict[str, Any]:
    """
    Analyze control requirements for automation feasibility.
    
    Args:
        control_name: Control identifier
        
    Returns:
        Analysis results
    """
    print(f"🔍 Fetching control data for {control_name}...")
    
    # Get control from database
    control_data = get_control_from_db(control_name)
    if not control_data:
        return {}
    
    print(f"📋 Control: {control_data['control_long_name']}")
    print(f"🏷️ Family: {control_data['family_name']}")
    
    # Analyze control
    print(f"🔬 Analyzing control requirements...")
    
    try:
        analysis = analyze_control(
            control_name=control_name,
            control_text=control_data['control_text'],
            control_title=control_data['control_long_name'],
            max_tokens=1000,
            temperature=0.2
        )
        
        print(f"✅ Analysis completed")
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze control: {e}")
        return {}


def generate_yaml_check_for_control(
    control_name: str, 
    resource_type: str = "github",
    connection_id: int = 1,
    suggested_check_id: int = None
) -> str:
    """
    Generate complete YAML check entry for a control.
    
    Args:
        control_name: Control identifier
        resource_type: Target resource type
        connection_id: Connection ID for the check
        suggested_check_id: Suggested ID for the check
        
    Returns:
        Generated YAML content
    """
    print(f"🔍 Fetching control data for {control_name}...")
    
    # Get control from database
    control_data = get_control_from_db(control_name)
    if not control_data:
        return ""
    
    print(f"📋 Control: {control_data['control_long_name']}")
    print(f"🏷️ Family: {control_data['family_name']}")
    
    # Generate suggested check ID if not provided
    if suggested_check_id is None:
        suggested_check_id = 1000 + control_data['id']
    
    # Generate complete YAML check
    print(f"🤖 Generating complete YAML check entry...")
    
    try:
        yaml_content = generate_checks_yaml(
            control_name=control_name,
            control_text=control_data['control_text'],
            control_title=control_data['control_long_name'],
            resource_type=resource_type,
            connection_id=connection_id,
            control_id=control_data['id'],
            suggested_check_id=suggested_check_id,
            max_tokens=1200,
            temperature=0.1
        )
        
        print(f"✅ Generated {len(yaml_content)} characters of YAML")
        return yaml_content
        
    except Exception as e:
        logger.error(f"Failed to generate YAML check: {e}")
        return ""


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate compliance checks with LLM")
    parser.add_argument("--control", required=True, help="Control name (e.g., AC-2)")
    parser.add_argument("--resource-type", default="github", 
                       choices=["github", "aws", "azure", "gcp"],
                       help="Target resource type")
    parser.add_argument("--analyze", action="store_true", 
                       help="Analyze control instead of generating code")
    parser.add_argument("--yaml", action="store_true",
                       help="Generate complete YAML check entry instead of just code")
    parser.add_argument("--connection-id", type=int, default=1,
                       help="Connection ID for the check (default: 1)")
    parser.add_argument("--check-id", type=int,
                       help="Suggested check ID (auto-generated if not provided)")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    print("🚀 LLM-Powered Compliance Check Generator")
    print("=" * 60)
    
    # Test LLM connection first
    try:
        client = get_llm_client()
        if not client.test_connection():
            print("❌ LLM connection test failed. Please check your AWS configuration.")
            return 1
    except Exception as e:
        print(f"❌ Failed to initialize LLM client: {e}")
        return 1
    
    if args.analyze:
        # Analyze control
        analysis = analyze_control_requirements(args.control)
        
        if analysis:
            print("\n📊 Analysis Results:")
            print("-" * 40)
            print(f"Automation Feasibility: {analysis.get('automation_feasibility', 'unknown').upper()}")
            print(f"Implementation Complexity: {analysis.get('implementation_complexity', 'unknown').upper()}")
            print(f"Resource Types: {', '.join(analysis.get('resource_types', []))}")
            
            if analysis.get('key_requirements'):
                print("\nKey Requirements:")
                for req in analysis['key_requirements']:
                    print(f"  • {req}")
            
            if analysis.get('suggested_checks'):
                print("\nSuggested Automated Checks:")
                for check in analysis['suggested_checks']:
                    print(f"  • {check}")
            
            # Save to file if requested
            if args.output:
                import json
                with open(args.output, 'w') as f:
                    json.dump(analysis, f, indent=2)
                print(f"\n💾 Analysis saved to {args.output}")
    
    elif args.yaml:
        # Generate complete YAML check
        yaml_content = generate_yaml_check_for_control(
            args.control, 
            args.resource_type,
            args.connection_id,
            args.check_id
        )
        
        if yaml_content:
            print("\n📄 Generated YAML Check Entry:")
            print("-" * 40)
            print(yaml_content)
            
            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(yaml_content)
                print(f"\n💾 YAML saved to {args.output}")
        
    else:
        # Generate compliance check code only
        code = generate_check_for_control(args.control, args.resource_type)
        
        if code:
            print("\n🐍 Generated Python Code:")
            print("-" * 40)
            print(code)
            
            # Save to file if requested
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(code)
                print(f"\n💾 Code saved to {args.output}")
    
    return 0


if __name__ == "__main__":
    exit(main()) 