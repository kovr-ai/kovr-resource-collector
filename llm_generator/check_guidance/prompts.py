"""
Check Guidance Prompts - Section 2 System Compatibility

LLM prompts for enriching checks with system-compatible resources:
- Step 1: Expand to Resource Types and Field Paths
- Generate targeted guidance with real field paths
"""

from typing import List

from con_mon.connectors import ConnectorType
from llm_generator.benchmark.models import Check


def get_resource_selection_prompt(
        check: Check,
        provider: ConnectorType,
        resource_name: str,
        field_paths: List[str],
) -> str:
    """
    Helper prompt to pre-select valid resource types for a check.
    """
    field_paths_formatted = "\n".join([f"  - {path}" for path in field_paths])

    return """You are a cybersecurity expert selecting valid system resources for compliance checks.

**TASK:** Identify which system resources are valid for a particular check. Enrich a compliance check with system-compatible resource types and field paths.
**CRITICAL REQUIREMENT:** Only use field paths that are explicitly provided. DO NOT hallucinate or create new field paths.

**INPUT CHECK:**
- Check ID: {check_id}
- Name: {check_name}
- Literature: {check_literature}
- Category: {check_category}
- Controls: {check_controls}

**AVAILABLE RESOURCES:**
Provider: {provider}
Resource: {resource_name}):
Available Field Paths:
{field_paths_formatted}

**REQUIREMENTS:**
1. Select all relevant resource types for this particular check.
2. Consider what systems would typically need to comply with this type of check.
3. Consider that ONLY available data is metadata coming from API not actual systems.
4. Explain why the resource type is valid or not valid for this particular check.

**LITERATURE WRITING GUIDELINES:**
- Be specific about field paths: "Check that repo.basic_info.branches[].protected is true"
- Include validation criteria: "Verify all branches named 'main' or 'master'"
- Mention expected values: "The 'protected' flag must be set to true"
- Avoid generic language, be implementation-specific
- Reference exact field paths from the available schema
- Do not use code sensitive special characters like : or , or ; or ' or " etc  

**FIELD PATH VALIDATION:**
- ONLY use field paths explicitly listed in the available resources above
- If no suitable field paths exist, set field_paths to an empty array []
- If no valid resource type exists, set literature to empty string ""

ADHERE STRICTLY TO BELOW FORMAT FOR RESPONSE
DO NOT ADD ANY OTHER TEXT OR EXPLANATION OTHER THAN WHAT BELOW FORMAT STATES
**OUTPUT FORMAT (JSON):**
{{
    "is_valid": <true or false as boolean type>
    "reason": "Brief explanation of why this resource type is valid or invalid for {check_id}",
    "field_paths": [
        <FieldPath1>,
        <FieldPath2>,
    ],
    "literature": "<ResourceType1CheckImplementationLiterature>",
}}
""".format(
        check_id=check.unique_id,
        check_name=check.name,
        check_literature=check.literature,
        check_category=check.category,
        check_controls="\n- ".join(check.controls or []),
        resource_name=resource_name,
        provider=provider,
        field_paths_formatted=field_paths_formatted,
    )
