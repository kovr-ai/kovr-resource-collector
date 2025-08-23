"""
Benchmark Check Extraction Prompts - Step 1 Implementation

This module provides LLM prompt templates for extracting atomic compliance checks 
from benchmark documentation (OWASP, Mitre Att&ck).

Implements Section 1, Step 1: Extract Checks Literature
"""

from abc import ABC, abstractmethod
from datetime import datetime


class BenchmarkExtractionPrompt(ABC):
    """Base class for benchmark check extraction prompts."""
    
    def __init__(self, benchmark_source: str, benchmark_version: str):
        self.benchmark_source = benchmark_source
        self.benchmark_version = benchmark_version
    
    @abstractmethod
    def get_extraction_template(self) -> str:
        """Get the LLM prompt template for extracting checks."""
        pass
    
    @abstractmethod
    def generate_check_id(self, index: int, category: str = None) -> str:
        """Generate a global unique check ID."""
        pass
    
    def format_prompt(self, benchmark_text: str, extraction_context: str = "") -> str:
        """Format the complete prompt with benchmark text."""
        template = self.get_extraction_template()
        return template.format(
            benchmark_text=benchmark_text,
            benchmark_source=self.benchmark_source,
            benchmark_version=self.benchmark_version,
            extraction_context=extraction_context,
            current_date=datetime.now().isoformat()
        )


class GenericBenchmarkPrompt(BenchmarkExtractionPrompt):
    """Generic benchmark extraction prompt for any compliance standard."""
    
    def generate_check_id(self, index: int, category: str = None) -> str:
        """Generate generic check ID: BENCH-{version}-{category}-{index}"""
        # Clean benchmark source for ID (remove spaces, special chars)
        clean_source = ''.join(c for c in self.benchmark_source.upper() if c.isalnum())[:10]
        if category:
            return f"{clean_source}-{self.benchmark_version}-{category}-{str(index).zfill(3)}"
        return f"{clean_source}-{self.benchmark_version}-{str(index).zfill(3)}"
    
    def get_extraction_template(self) -> str:
        return """You are a cybersecurity expert extracting atomic compliance checks from benchmark documentation.

**CRITICAL REQUIREMENTS:**
1. Each check must be a SINGLE, atomic requirement (no sub-check splitting)
2. Generate globally unique check IDs following a consistent format
3. Create targeted and actionable descriptions
4. Focus on requirements that can be implemented and tested
5. **IMPORTANT**: Suggest related compliance controls (NIST, ISO, etc.) for each check

**Input Benchmark:**
Source: {benchmark_source}
Version: {benchmark_version}
Context: {extraction_context}

**Benchmark Text:**
{benchmark_text}

**Output Format (JSON):**
```json
{{
  "metadata": {{
    "benchmark_source": "{benchmark_source}",
    "benchmark_version": "{benchmark_version}",
    "extraction_date": "{current_date}",
    "total_checks_extracted": <number>
  }},
  "checks": [
    {{
      "check_id": "UNIQUE-ID-FORMAT",
      "title": "Short descriptive title",
      "description": "Specific, actionable requirement",
      "benchmark_source": "{benchmark_source}",
      "category": "category_name",
      "severity": "high|medium|low",
      "tags": ["relevant", "tags"],
      "suggested_controls": [
        "NIST-800-53-AC-3",
        "ISO-27001-A.9.1.2",
        "NIST-800-171-3.1.1"
      ],
      "control_reasoning": "Brief explanation of why these controls are relevant",
      "extracted_at": "{current_date}"
    }}
  ]
}}
```

**Instructions:**
1. Analyze the benchmark structure and identify distinct requirements
2. Generate consistent, unique check IDs based on the benchmark format
3. Create clear, implementable descriptions for each requirement
4. Categorize checks based on the benchmark's organization
5. Assign severity based on risk indicators in the text
6. Add relevant tags for filtering and organization
7. **CRITICAL**: For each check, suggest 2-5 related compliance controls from frameworks like:
   - NIST 800-53 (format: NIST-800-53-XX-##)
   - NIST 800-171 (format: NIST-800-171-#.#.#)
   - ISO 27001 (format: ISO-27001-A.#.#.#)
   - Other relevant frameworks
8. Provide brief reasoning for control suggestions
9. Ensure each check is atomic and testable

**Control Suggestion Guidelines:**
- Access Control requirements → AC controls (NIST-800-53-AC-*)
- Authentication/Identity → IA controls (NIST-800-53-IA-*)
- Audit/Logging → AU controls (NIST-800-53-AU-*)
- Configuration → CM controls (NIST-800-53-CM-*)
- Encryption/Crypto → SC controls (NIST-800-53-SC-*)
- Consider cross-framework mappings where applicable

Generate the JSON output now:"""


class PromptFactory:
    """Simplified factory for creating GenericBenchmarkPrompt instances."""
    
    @classmethod
    def create_prompt(cls, benchmark_source: str, benchmark_version: str) -> BenchmarkExtractionPrompt:
        """Create GenericBenchmarkPrompt for any benchmark source."""
        return GenericBenchmarkPrompt(benchmark_source, benchmark_version)
    
    @classmethod
    def available_prompts(cls) -> list:
        """Get list of available prompt types."""
        return ['generic']
