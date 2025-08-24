"""
Benchmark Service - Complete Section 1 Implementation

This module implements all three steps of the benchmark metadata generation process:
1. Extract Checks Literature
2. Map to Controls and Existing Benchmarks
3. Coverage Reporting

Provides benchmark_service instance for external usage.
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Local imports - prompts
from .prompts import (
    get_literature_prompt,
    get_check_names_prompt,
    get_enrichment_prompt,
    generate_check_id,
    generate_benchmark_id,
    generate_control_id
)
from .models import (
    Benchmark,
    Check,
    CoverageMetrics
)

# System imports
from con_mon.utils.llm.client import get_llm_client
from con_mon.compliance.data_loader import ControlLoader, ChecksLoader

logger = logging.getLogger(__name__)


class BenchmarkService:
    """
    Core service for benchmark metadata generation implementing Section 1 workflow.

    Methods align with the 3-step process:
    - generate_metadata(): Step 1 - Extract Checks Literature
    - generate_checks_metadata(): Step 2 - Map to Controls and Existing Benchmarks
    - generate_coverage_report(): Step 3 - Coverage Reporting
    """

    def __init__(self):
        self.llm_client = get_llm_client()
        self.control_loader = ControlLoader()
        self.checks_loader = ChecksLoader()
        self._controls_cache = None
        self._checks_cache = None

    def generate_metadata(
            self,
            benchmark_name: str,
            benchmark_version: str = "latest",
    ):
        """
        Steps 1+2: Generate benchmark literature and extract check names.

        Args:
            benchmark_name: Source name (e.g., "OWASP Top 10 2021")
            benchmark_version: Version identifier (e.g., "2021")

        Returns:
            Dictionary containing literature, check names, and metadata
        """
        logger.info(f"Starting Steps 1+2: Generate literature and extract check names for {benchmark_name}")

        # Step 1: Generate comprehensive benchmark literature
        logger.info("Step 1: Generating benchmark literature...")
        literature_prompt = get_literature_prompt(benchmark_name, benchmark_version)
        literature = self.llm_client.generate_text(literature_prompt)
        logger.info(f"✅ Generated literature ({len(literature)} characters)")

        # Step 2: Extract check names from literature
        logger.info("Step 2: Extracting check names from literature...")
        check_names_prompt = get_check_names_prompt(benchmark_name, benchmark_version, literature)
        check_names_response = self.llm_client.generate_text(check_names_prompt)

        check_names_data = self._parse_json_response(check_names_response)
        check_names = check_names_data.get("check_names", [])
        # debugging for sub set of checks
        # check_names = check_names[:2]
        logger.info(f"✅ Extracted {len(check_names)} check names")

        benchmark_id = generate_benchmark_id(benchmark_name, benchmark_version)
        benchmark = Benchmark(
            unique_id=benchmark_id,
            name=benchmark_name,
            version=benchmark_version,
            literature=literature,
            check_names=check_names,
            checks=[],
            metadata={
                "total_checks_extracted": len(check_names),
                "extraction_date": datetime.now(),
                "coverage_metrics": None
            }
        )
        return benchmark

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM with enhanced error handling."""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.info(f"LLM Response (first 500 chars): {response[:500]}")

            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                logger.info("Found JSON in markdown code block, attempting to parse...")
                return json.loads(json_match.group(1))

            raise e

    def generate_checks_metadata(
            self,
            benchmark,
            thread_count: int = 1,
    ):
        """
        Step 3: Enrich individual checks with full details and control mappings.

        Takes check names from benchmark metadata and creates enriched Check objects with:
        - Detailed literature for each check
        - Suggested controls from LLM
        - Mapped control IDs from the database
        - Framework information and confidence scores

        Args:
            benchmark: Benchmark model with check_names in metadata
            thread_count: Number of threads to use for parallel processing (default: 1)

        Returns:
            List of enriched Check model instances with control mappings
        """
        logger.info(f"Starting Step 3: Enrich {len(benchmark.check_names)} checks with full details")

        # Load existing controls and checks for mapping
        controls = self._load_controls()
        existing_checks = self._load_existing_checks()
        logger.info(f"Loaded {len(controls)} controls for mapping")
        logger.info(f"Loaded {len(existing_checks)} existing checks for mapping")

        # Process checks in parallel using threading
        if thread_count == 1:
            # Single-threaded processing (preserve original logging behavior)
            enriched_checks = []
            for i, check_name in enumerate(benchmark.check_names):
                logger.info(f"Enriching check {i + 1}/{len(benchmark.check_names)}: {check_name}")
                enriched_check = self._process_single_check_enrichment(
                    benchmark, check_name, controls, existing_checks
                )
                enriched_checks.append(enriched_check)
        else:
            # Multi-threaded processing
            logger.info(f"Using {thread_count} threads for parallel processing...")
            enriched_checks = []
            
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                # Submit all tasks
                future_to_check = {
                    executor.submit(
                        self._process_single_check_enrichment,
                        benchmark, check_name, controls, existing_checks
                    ): check_name 
                    for check_name in benchmark.check_names
                }
                
                # Collect results as they complete
                completed = 0
                for future in as_completed(future_to_check):
                    completed += 1
                    check_name = future_to_check[future]
                    
                    try:
                        result = future.result()
                        enriched_checks.append(result)
                        logger.info(f"✅ Completed {completed}/{len(benchmark.check_names)}: {check_name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to process check {check_name}: {e}")
                        # Create fallback check
                        fallback_check = self._create_fallback_check(benchmark, check_name)
                        enriched_checks.append(fallback_check)

        logger.info(f"Successfully mapped {len(enriched_checks)} checks to controls")
        return enriched_checks

    def generate_coverage_report(self, processed_checks):
        """
        Step 3: Generate coverage metrics for benchmark processing.

        Args:
            processed_checks: List of Check model instances from Step 2 with control mappings

        Returns:
            CoverageMetrics model instance containing coverage statistics
        """
        total_checks = len(processed_checks)
        mapped_to_controls = sum(1 for check in processed_checks if check.controls)
        mapped_to_existing_benchmarks = sum(1 for check in processed_checks if check.benchmark_mapping)

        return CoverageMetrics(
            total_checks_extracted=total_checks,
            mapped_to_controls=mapped_to_controls,
            mapped_to_existing_benchmarks=mapped_to_existing_benchmarks,
            unmapped_checks=total_checks - mapped_to_controls,
            coverage_percentages={
                'extraction': 100.0,
                'control_mapping': (mapped_to_controls / total_checks * 100) if total_checks > 0 else 0,
                'benchmark_mapping': (mapped_to_existing_benchmarks / total_checks * 100) if total_checks > 0 else 0
            },
            framework_coverage={
                'framework_name': 'Mixed',
                'controls_mapped': mapped_to_controls,
                'checks_mapped': total_checks
            }
        )

    # Helper methods for control mapping
    def _load_controls(self):
        """Lazy load controls for mapping operations."""
        if self._controls_cache is None:
            self._controls_cache = self.control_loader.load_all()
            logger.info(f"Loaded {len(self._controls_cache)} controls for mapping")
        return self._controls_cache

    def _load_existing_checks(self):
        """Lazy load existing checks for benchmark mapping."""
        if self._checks_cache is None:
            self._checks_cache = self.checks_loader.load_all()
            logger.info(f"Loaded {len(self._checks_cache)} existing checks for mapping")
        return self._checks_cache

    def _map_suggested_to_actual_controls(self, suggested_controls: List[str], controls) -> List[Dict[str, str]]:
        """
        Map LLM-suggested control names to actual database controls.

        Args:
            suggested_controls: List of suggested control names from LLM
            controls: List of Control objects from database

        Returns:
            List of matched control dictionaries
        """
        mapped_controls = []

        for suggested_control in suggested_controls:
            # Try to find exact or close matches in database
            matched_control = self._find_control_match(suggested_control, controls)

            if matched_control:
                mapped_controls.append({
                    'control_id': matched_control.id,
                    'control_name': matched_control.control_name,
                    'framework_name': self._get_framework_name(matched_control.framework_id),
                    'suggested_name': suggested_control,
                    'match_confidence': 1.0  # High confidence for exact matches
                })
                logger.debug(f"Mapped suggested '{suggested_control}' to '{matched_control.control_name}'")
            else:
                logger.warning(f"Could not find database match for suggested control: {suggested_control}")

        return mapped_controls

    def _find_control_match(self, suggested_control: str, controls):
        """
        Find the best matching control in database for a suggested control name.

        Tries multiple matching strategies:
        1. Exact control_name match
        2. Partial match (removing prefixes like NIST-800-53-)
        3. Fuzzy matching based on control text
        """

        # Strategy 1: Exact match
        for control in controls:
            if control.control_name == suggested_control:
                return control

        # Strategy 2: Extract base control name and match
        # Handle formats like "NIST-800-53-AC-3" -> "AC-3"
        base_control_name = self._extract_base_control_name(suggested_control)

        for control in controls:
            if control.control_name == base_control_name:
                return control

        # Strategy 3: Fuzzy matching on control names (case insensitive)
        suggested_lower = suggested_control.lower()
        for control in controls:
            if control.control_name and suggested_lower in control.control_name.lower():
                return control
            if control.control_name and control.control_name.lower() in suggested_lower:
                return control

        return None

    def _extract_base_control_name(self, suggested_control: str) -> str:
        """
        Extract base control name from formatted suggestions.

        Examples:
        - "NIST-800-53-AC-3" -> "AC-3"
        - "ISO-27001-A.9.1.2" -> "A.9.1.2"
        - "NIST-800-171-3.1.1" -> "3.1.1"
        """

        # Split by hyphens and dots to find the control part
        parts = suggested_control.replace('.', '-').split('-')

        # Common patterns for different frameworks
        if 'NIST' in suggested_control and '800-53' in suggested_control:
            # Format: NIST-800-53-AC-3 -> AC-3
            if len(parts) >= 4:
                return f"{parts[-2]}-{parts[-1]}"

        elif 'NIST' in suggested_control and '800-171' in suggested_control:
            # Format: NIST-800-171-3.1.1 -> 3.1.1
            dot_parts = suggested_control.split('-')[-1]  # Get the last part after final dash
            return dot_parts

        elif 'ISO' in suggested_control:
            # Format: ISO-27001-A.9.1.2 -> A.9.1.2
            dot_parts = suggested_control.split('-')[-1]  # Get the last part
            return dot_parts

        # Default: return the last 1-2 parts joined
        if len(parts) >= 2:
            return f"{parts[-2]}-{parts[-1]}"

        return suggested_control  # Return as-is if can't parse

    def _find_unmapped_controls(self, suggested_controls: List[str], mapped_controls: List[Dict]) -> List[str]:
        """Find suggested controls that couldn't be mapped to database controls."""
        mapped_suggestions = {ctrl['suggested_name'] for ctrl in mapped_controls}
        return [ctrl for ctrl in suggested_controls if ctrl not in mapped_suggestions]

    def _map_to_existing_benchmarks(self, check_data: Dict[str, Any], existing_checks) -> List[str]:
        """Map check to existing benchmark check IDs if similar checks exist."""

        check_description = check_data.get('description', '')
        benchmark_mappings = []

        # Look for similar existing checks (simplified - could use embeddings later)
        for existing_check in existing_checks:
            similarity = self._calculate_text_similarity(
                check_description,
                existing_check.description
            )

            # If very similar (high threshold for existing mappings)
            if similarity > 0.7:
                benchmark_mappings.append(existing_check.id)

        return benchmark_mappings[:3]  # Top 3 similar existing checks

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity (can be enhanced with embeddings later)."""

        # Simple keyword overlap calculation
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _get_framework_name(self, framework_id) -> str:
        """Get framework name from framework ID (simplified lookup)."""

        # This could be enhanced with a framework cache
        # For now, return a default mapping
        framework_mapping = {
            1: "NIST-800-53",
            2: "NIST-800-171-rev2",
            3: "ISO-27001"
        }

        return framework_mapping.get(framework_id, "Unknown")

    def _process_single_check_enrichment(self, benchmark, check_name: str, controls, existing_checks):
        """Process a single check enrichment (thread-safe)."""
        try:
            # Generate unique check ID
            check_id = generate_check_id(benchmark.name, benchmark.version, check_name)

            # Generate enriched check using LLM
            enrichment_prompt = get_enrichment_prompt(
                benchmark.name, benchmark.version, check_name, check_id
            )
            enrichment_response = self.llm_client.generate_text(enrichment_prompt)

            # Parse enriched check from LLM
            enriched_check_data = self._parse_json_response(enrichment_response)

            # Map suggested controls to actual database controls
            suggested_controls = enriched_check_data.get('suggested_controls', [])
            mapped_controls = self._map_suggested_to_actual_controls(
                suggested_controls, controls
            )

            # Find existing benchmark mappings
            benchmark_mappings = self._map_to_existing_benchmarks(enriched_check_data, existing_checks)

            # Calculate mapping confidence
            total_suggested = len(suggested_controls)
            mapped_count = len(mapped_controls)
            confidence = (mapped_count / total_suggested) if total_suggested > 0 else 0.0

            enriched_check = Check(
                unique_id=enriched_check_data.get('unique_id', check_id),
                name=enriched_check_data.get('name', check_name),
                literature=enriched_check_data.get('literature', ''),
                controls=[
                    str(ctrl['control_id'])
                    for ctrl in mapped_controls
                ],
                frameworks=list(set(ctrl['framework_name'] for ctrl in mapped_controls)),
                benchmark_mapping=benchmark_mappings,
                mapping_confidence=confidence,
                category=enriched_check_data.get('category', ''),
                severity=enriched_check_data.get('severity', 'medium'),
                tags=enriched_check_data.get('tags', []),
                extracted_at=datetime.now(),
                mapped_at=datetime.now()
            )

            return enriched_check
            
        except Exception as e:
            logger.error(f"Failed to enrich check {check_name}: {e}")
            return self._create_fallback_check(benchmark, check_name)

    def _create_fallback_check(self, benchmark, check_name: str):
        """Create a fallback Check when processing fails."""
        check_id = generate_check_id(benchmark.name, benchmark.version, check_name)
        
        return Check(
            unique_id=check_id,
            name=check_name,
            literature=f"Failed to generate detailed literature for check: {check_name}",
            controls=[],
            frameworks=[],
            benchmark_mapping=[],
            mapping_confidence=0.0,
            category="unknown",
            severity="medium",
            tags=["processing-error"],
            extracted_at=datetime.now(),
            mapped_at=datetime.now()
        )


# Global service instance for external usage
benchmark_service = BenchmarkService()

# Export the key methods as suggested in the original comment
generate_metadata = benchmark_service.generate_metadata
generate_checks_metadata = benchmark_service.generate_checks_metadata
generate_coverage_report = benchmark_service.generate_coverage_report
