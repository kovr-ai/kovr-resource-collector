PROMPT = """You are a cybersecurity expert enriching a security check with comprehensive metadata and mappings.

**TASK:** Enrich the provided security check with detailed literature, control mappings, benchmark mappings, and categorization.

**CHECK TO ENRICH:** {check_name}

**REQUIREMENTS:**
1. Generate a comprehensive unique_id in format: "{{benchmark_name}}-{{year}}-{{section}}-{{number}}" (e.g., "OWASP-2021-A01-001")
2. Create detailed literature explaining what this check validates and why it's important
3. Map to relevant security controls (NIST 800-53, ISO 27001, etc.) with reasoning and confidence scores
4. Map to relevant attack techniques (MITRE ATT&CK) with reasoning and confidence scores  
5. Assign appropriate category (e.g., access_control, encryption, authentication, etc.)
6. Assign severity level (low, medium, high, critical)
7. Provide relevant tags for classification

**OUTPUT FORMAT:**
Return ONLY a JSON object with this exact structure:

{{
    "unique_id": "string",
    "literature": "string", 
    "controls": [
        {{
            "unique_id": "string",
            "reason": "string",
            "confidence": 0.0-1.0
        }}
    ],
    "benchmarks": [
        {{
            "unique_id": "string", 
            "reason": "string",
            "confidence": 0.0-1.0
        }}
    ],
    "category": "string",
    "severity": "string",
    "tags": ["string"]
}}

**CONTROL MAPPING EXAMPLES:**
- NIST-800-53-AC-3 (Access Control)
- NIST-800-53-SC-28 (Protection of Information at Rest) 
- ISO-27001-A.9.4.1 (Information access restriction)

**BENCHMARK MAPPING EXAMPLES (use MITRE ATT&CK):**
- MITRE-ATT&CK-T1078 (Valid Accounts)
- MITRE-ATT&CK-T1530 (Data from Cloud Storage Object)
- MITRE-ATT&CK-T1110 (Brute Force)

**CATEGORIES:** access_control, encryption, authentication, audit, network_security, system_integrity, incident_response, risk_assessment

**SEVERITY LEVELS:** low, medium, high, critical

Enrich the check now:"""

UNIQUE_ID_TEMPLATE = "{benchmark_name}-2021-A{section:02d}-{number:03d}"
