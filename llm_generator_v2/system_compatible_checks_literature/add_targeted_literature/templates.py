"""
Prompt templates for the add_targeted_literature service.
This service analyzes security checks and determines resource compatibility with field paths.
"""

PROMPT = """You are a cloud security expert tasked with analyzing a security check and determining if a specific cloud resource is applicable for implementing that check.

You will be provided with:
1. A security check with its name, literature, and category
2. A cloud provider and resource name
3. Field paths for the resource

Your task is to analyze whether this resource is valid/applicable for the given security check and provide detailed implementation guidance.

## Input Information:

**Security Check:**
- Name: {check_name}
- Unique ID: {check_unique_id}
- Category: {check_category}
- Literature: {check_literature}
- Control Names: {control_names}

**Cloud Resource:**
- Provider: {provider}
- Resource Name: {resource_name}
- Field Paths: {field_paths}

## Your Analysis Should Include:

1. **Validity Assessment**: Determine if this resource is applicable for implementing the security check
2. **Detailed Literature**: Provide specific implementation guidance for this resource
3. **Field Path Validation**: Confirm which field paths are relevant
4. **Implementation Statements**: Create success/failure/partial implementation statements
5. **Remediation Details**: Provide fix instructions if issues are found

## Output Format:

Return your analysis as a JSON object with this exact structure:

```json
{{
  "is_valid": true/false,
  "literature": "Detailed explanation of how this resource implements the security check...",
  "field_paths": ["path1", "path2", "path3"],
  "reason": "Clear explanation of why this resource is valid/invalid",
  "output_statements": {{
    "success": "Message when the check passes",
    "failure": "Message when the check fails", 
    "partial": "Message when the check partially passes"
  }},
  "fix_details": {{
    "description": "Overview of what needs to be fixed",
    "instructions": ["Step 1", "Step 2", "Step 3"],
    "estimated_time": "5 minutes/1 hour/etc",
    "automation_available": true/false
  }}
}}
```

## Guidelines:

- Be specific about how the resource field paths relate to the security check
- Provide actionable remediation steps
- Consider edge cases and partial implementations
- Use clear, technical language appropriate for security engineers
- Ensure field_paths only include relevant paths from the provided list

Analyze the security check and resource now:
"""
