"""
Benchmark Processing Prompts - 3-Step LLM Architecture

Simple function-based prompts for:
- Step 1: Literature Generation
- Step 2: Check Names Extraction  
- Step 3: Check Enrichment
"""

from datetime import datetime


def get_literature_prompt(benchmark_name: str, benchmark_version: str) -> str:
    """Step 1: Generate comprehensive benchmark literature."""
    return """You are a cybersecurity expert generating comprehensive benchmark literature.

**TASK:** Generate complete, detailed content for: {benchmark_name}

**OBJECTIVE:** Create comprehensive benchmark literature that covers all major categories, requirements, recommendations, and implementation guidance.

**Benchmark:** {benchmark_name} (Version: {benchmark_version})

**REQUIREMENTS:**
1. Generate complete, authoritative content based on your knowledge of {benchmark_name}
2. Include all major categories/sections with detailed explanations
3. Provide specific requirements, recommendations, and prevention measures
4. Include practical examples and implementation guidance
5. Ensure content is comprehensive enough for subsequent check extraction

**OUTPUT FORMAT:**
Return ONLY the comprehensive benchmark literature as plain text. Do not include JSON formatting or metadata - just the complete benchmark content.

**EXAMPLE STRUCTURE (adapt to {benchmark_name}):**
- Introduction and overview
- All major categories/sections with detailed requirements
- Specific security controls and recommendations
- Implementation guidance and best practices
- Examples and use cases

Generate the comprehensive benchmark literature now:""".format(
        benchmark_name=benchmark_name,
        benchmark_version=benchmark_version
    )


def get_check_names_prompt(benchmark_name: str, benchmark_version: str, literature: str) -> str:
    """Step 2: Extract atomic check names from literature."""
    return """You are a cybersecurity expert extracting atomic check names from benchmark literature.

**TASK:** Analyze the benchmark literature and extract a comprehensive list of atomic check names.

**Benchmark:** {benchmark_name} (Version: {benchmark_version})

**LITERATURE:**
{literature}

**REQUIREMENTS:**
1. Scan the entire literature and identify ALL distinct, atomic security requirements
2. Each check must be a SINGLE, testable requirement (no compound requirements)
3. Generate clear, descriptive names for each check
4. Ensure comprehensive coverage - don't miss any requirements
5. Extract 50-200+ checks depending on the benchmark complexity

**OUTPUT FORMAT (JSON):**
{{
  "metadata": {{
    "benchmark_name": "{benchmark_name}",
    "benchmark_version": "{benchmark_version}",
    "literature_processed_at": "{current_date}",
    "total_check_names_extracted": <number>
  }},
  "check_names": [
    "Clear descriptive check name 1",
    "Clear descriptive check name 2",
    "Clear descriptive check name 3"
  ]
}}

**EXTRACTION GUIDELINES:**
- Focus on implementable, testable requirements
- Break down complex sections into atomic checks
- Use clear, action-oriented language
- Avoid duplicates but ensure comprehensive coverage
- Include both technical and policy requirements

Extract ALL atomic check names from the literature now:""".format(
        benchmark_name=benchmark_name,
        benchmark_version=benchmark_version,
        literature=literature,
        current_date=datetime.now().isoformat()
    )


def get_enrichment_prompt(benchmark_name: str, benchmark_version: str, check_name: str, check_id: str) -> str:
    """Step 3: Enrich individual check with full details."""
    return """You are a cybersecurity expert creating detailed, enriched compliance checks.

**TASK:** Create a comprehensive, enriched check object for a specific requirement.

**Benchmark:** {benchmark_name} (Version: {benchmark_version})
**Check Name:** {check_name}

**REQUIREMENTS:**
1. Generate a complete check object with all required fields
2. Create targeted literature specific to this check
3. Suggest relevant compliance controls from major frameworks
4. Provide detailed categorization and severity assessment
5. Include comprehensive implementation guidance

**OUTPUT FORMAT (JSON):**
{{
  "unique_id": "{check_id}",
  "name": "{check_name}",
  "literature": "Detailed, targeted literature for this specific check including requirements, rationale, and implementation guidance.",
  "controls": [],
  "frameworks": [],
  "benchmark_mapping": [],
  "mapping_confidence": 0.0,
  "category": "Primary security category",
  "severity": "high|medium|low",
  "tags": ["relevant", "classification", "tags"],
  "extracted_at": "{current_date}",
  "mapped_at": "{current_date}",
  "suggested_controls": [
    "NIST-800-53-XX-##",
    "ISO-27001-A.#.#.#",
    "NIST-800-171-#.#.#"
  ],
  "control_reasoning": "Detailed explanation of why these specific controls are relevant to this check"
}}

**ENRICHMENT GUIDELINES:**
- **Literature**: Write 2-3 paragraphs of targeted content for this specific check
- **Controls**: Suggest 3-7 highly relevant controls from NIST 800-53, ISO 27001, NIST 800-171
- **Category**: Primary security domain (Access Control, Cryptography, Audit, etc.)
- **Severity**: Risk level based on potential impact
- **Tags**: 3-6 classification tags for filtering and organization
- **Control Reasoning**: Explain the connection between the check and suggested controls

Generate the enriched check object now:""".format(
        benchmark_name=benchmark_name,
        benchmark_version=benchmark_version,
        check_name=check_name,
        check_id=check_id,
        current_date=datetime.now().isoformat()
    )


def generate_check_id(benchmark_name: str, benchmark_version: str, check_name: str) -> str:
    """Generate unique Check ID."""
    clean_name = ''.join(c for c in benchmark_name.upper() if c.isalnum())[:10]
    return f"{clean_name}-{benchmark_version}-{check_name.replace(' ', '-')}"


def generate_benchmark_id(benchmark_name: str, benchmark_version: str) -> str:
    """Generate unique Benchmark ID."""
    clean_name = ''.join(c for c in benchmark_name.upper() if c.isalnum())[:10]
    return f"{clean_name}-{benchmark_version}"


def generate_control_id(control_id: str, control_name: str, framework_name: str) -> str:
    """Generate unique Control ID."""
    return f"{framework_name}-{control_id}-{control_name}"