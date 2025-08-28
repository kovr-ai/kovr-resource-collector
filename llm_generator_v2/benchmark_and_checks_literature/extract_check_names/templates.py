PROMPT = """You are a cybersecurity expert analyzing benchmark literature to extract individual security checks.

**TASK:** Extract all individual security checks from the provided {benchmark_name} literature.

**BENCHMARK:** {benchmark_name} (Version: {benchmark_version})

**LITERATURE TO ANALYZE:**
{literature}

**REQUIREMENTS:**
1. Extract ALL individual security checks/requirements from the literature
2. Each check should be a single, atomic requirement (no compound checks)
3. Use clear, descriptive names that capture the essence of each check
4. Focus on actionable security controls and requirements
5. Avoid duplicates and ensure each check is unique

**OUTPUT FORMAT:**
Return ONLY a JSON array of check names as strings. Each string should be a clear, concise check name.

Example format:
["Check name 1", "Check name 2", "Check name 3"]

**EXAMPLES OF GOOD CHECK NAMES:**
- "Multi-factor authentication enabled"
- "Encryption at rest configured"
- "Branch protection rules enforced"
- "Access logging enabled"
- "Password complexity requirements met"

Extract the check names now:"""

UNIQUE_ID = "{benchmark_name}-{benchmark_version}-{check_name}"
