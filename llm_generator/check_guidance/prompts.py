"""
Check Guidance Prompts - Section 2 System Compatibility

LLM prompts for enriching checks with system-compatible resources:
- Step 1: Expand to Resource Types and Field Paths
- Generate targeted guidance with real field paths
"""

from datetime import datetime
from typing import Dict, List, Any


def get_system_enrichment_prompt(
    check_data: Dict[str, Any], 
    available_resources: List[Dict[str, Any]]
) -> str:
    """
    Step 1: Generate system-enriched check with resource types and field paths.
    
    Args:
        check_data: Enriched check metadata from Section 1
        available_resources: List of ResourceSchema objects with field paths
    """
    
    # Format available resources for the prompt
    resources_text = ""
    for resource in available_resources:
        field_paths_formatted = "\n".join([f"      - {path}" for path in resource.get('field_paths', [])])
        resources_text += f"""
  {resource.get('resource_type', 'Unknown')} ({resource.get('provider', 'Unknown')} Provider):
    Description: {resource.get('description', 'No description')}
    Available Field Paths:
{field_paths_formatted}
"""

    return """You are a cybersecurity expert creating system-actionable compliance checks.

**TASK:** Enrich a compliance check with system-compatible resource types and field paths.

**CRITICAL REQUIREMENT:** Only use field paths that are explicitly provided. DO NOT hallucinate or create new field paths.

**INPUT CHECK:**
- Check ID: {check_id}
- Name: {check_name}
- Description: {check_description}
- Category: {check_category}
- Controls: {check_controls}

**AVAILABLE SYSTEM RESOURCES:**
{available_resources}

**REQUIREMENTS:**
1. Identify the MOST COMPATIBLE resource type(s) for this check
2. Select ONLY the field paths that are relevant and actually exist in the schema
3. Generate targeted, actionable guidance referencing specific field paths
4. Ensure guidance is technically accurate and implementable
5. Use clear, specific language that references exact field paths

**OUTPUT FORMAT (JSON):**
{{
  "unique_id": "{check_id}",
  "name": "{check_name}", 
  "literature": "{check_description}",
  "controls": {check_controls},
  "frameworks": {check_frameworks},
  "benchmark_mapping": {check_benchmark_mapping},
  "mapping_confidence": {check_mapping_confidence},
  "category": "{check_category}",
  "severity": "{check_severity}",
  "tags": {check_tags},
  "extracted_at": "{check_extracted_at}",
  "mapped_at": "{check_mapped_at}",
  "resource_type": "Most compatible resource type from available options",
  "field_paths_used": [
    "List of actual field paths that will be checked",
    "Only use paths that exist in the resource schema above"
  ],
  "targeted_guidance": "Specific, actionable guidance that references the exact field paths and explains how to verify compliance. Be concrete and implementation-focused.",
  "system_enriched_at": "{current_date}"
}}

**GUIDANCE WRITING GUIDELINES:**
- Be specific about field paths: "Check that repo.basic_info.branches[].protected is true"
- Include validation criteria: "Verify all branches named 'main' or 'master'"
- Mention expected values: "The 'protected' flag must be set to true"
- Avoid generic language, be implementation-specific
- Reference exact field paths from the available schema

**FIELD PATH VALIDATION:**
- ONLY use field paths explicitly listed in the available resources above
- If no suitable field paths exist, set field_paths_used to an empty array
- If no compatible resource type exists, set resource_type to "No Compatible Resource"

Generate the system-enriched check now:""".format(
        check_id=check_data.get('unique_id', ''),
        check_name=check_data.get('name', ''),
        check_description=check_data.get('literature', ''),
        check_category=check_data.get('category', ''),
        check_controls=check_data.get('controls', []),
        check_frameworks=check_data.get('frameworks', []),
        check_benchmark_mapping=check_data.get('benchmark_mapping', []),
        check_mapping_confidence=check_data.get('mapping_confidence', 0.0),
        check_severity=check_data.get('severity', ''),
        check_tags=check_data.get('tags', []),
        check_extracted_at=check_data.get('extracted_at', ''),
        check_mapped_at=check_data.get('mapped_at', ''),
        available_resources=resources_text,
        current_date=datetime.now().isoformat()
    )


def get_resource_selection_prompt(check_category: str, available_resources: List[Dict[str, Any]]) -> str:
    """
    Helper prompt to pre-select compatible resource types for a check category.
    """
    
    resources_list = "\n".join([
        f"- {res.get('resource_type', 'Unknown')}: {res.get('description', 'No description')}"
        for res in available_resources
    ])
    
    return """You are a cybersecurity expert selecting compatible system resources for compliance checks.

**TASK:** Identify which system resources are most compatible with a security check category.

**CHECK CATEGORY:** {check_category}

**AVAILABLE RESOURCES:**
{resources_list}

**REQUIREMENTS:**
1. Select up to 3 most relevant resource types for this category
2. Consider what systems would typically need to comply with this type of check
3. Prioritize resources that would have relevant data fields

**OUTPUT FORMAT (JSON):**
{{
  "compatible_resources": [
    "ResourceType1",
    "ResourceType2"
  ],
  "reasoning": "Brief explanation of why these resources are compatible with {check_category} checks"
}}

Select compatible resources now:""".format(
        check_category=check_category,
        resources_list=resources_list
    )


def generate_system_enriched_id(check_id: str) -> str:
    """Generate system-enriched check ID."""
    return f"{check_id}-SYSTEM"


def generate_resource_schema_id(resource_type: str, provider: str) -> str:
    """Generate unique Resource Schema ID."""
    return f"{provider.upper()}::{resource_type}"
