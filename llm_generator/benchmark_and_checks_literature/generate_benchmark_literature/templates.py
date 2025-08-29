PROMPT = """You are a cybersecurity expert generating comprehensive benchmark literature.

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

Generate the comprehensive benchmark literature now:"""

UNIQUE_ID = "{benchmark_name}-{benchmark_version}"