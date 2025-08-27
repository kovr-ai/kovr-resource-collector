import json

from llm_generator_v2 import services
from .templates import PROMPT


class Service(services.Service):
    class CannotParseLLMResponse(Exception):
        pass

    @staticmethod
    def _parse_llm_json_7_3(json_str):
        return json.loads(json_str[7:-3])

    @staticmethod
    def _parse_llm_json(json_str):
        return json.loads(json_str)

    def enrich_check(self, input_, benchmark_name: str = "OWASP"):
        prompt = PROMPT.format(
            check_name=input_.check.name,
            benchmark_name=benchmark_name,
        )

        # Get response from LLM and parse JSON
        response = self.llm_client.generate_text(prompt)
        for llm_json_parser in [
            self._parse_llm_json,
            self._parse_llm_json_7_3,
        ]:
            try:
                check_data = llm_json_parser(response)
                return self._create_check_output(check_data)
            except json.JSONDecodeError:
                # Fallback: create basic enrichment
                pass
        raise self.CannotParseLLMResponse()

    def _match_input_output(self, input_, output_):
        return input_.check.name == output_.check.name

    def _create_check_output(self, data: dict):
        """Create CheckOutput from parsed JSON data."""
        return {
            'unique_id': data.get("unique_id", ""),
            'literature': data.get("literature", ""),
            'controls': [
                {
                    'unique_id': ctrl.get("unique_id", ""),
                    'reason': ctrl.get("reason", ""),
                    'confidence': float(ctrl.get("confidence", 0.0))
                }
                for ctrl in data.get("controls", [])
            ],
            'benchmarks': [
                {
                    'unique_id': bench.get("unique_id", ""),
                    'reason': bench.get("reason", ""),
                    'confidence': float(bench.get("confidence", 0.0))
                }
                for bench in data.get("benchmarks", [])
            ],
            'category': data.get("category", "access_control"),
            'severity': data.get("severity", "medium"),
            'tags': data.get("tags", [])
        }

    def _create_fallback_enrichment(self, check_name: str):
        """Create fallback enrichment when JSON parsing fails."""
        return {
            'unique_id': f"FALLBACK-{hash(check_name) % 10000:04d}",
            'literature': f"Security check for: {check_name}. This check helps ensure system security by validating compliance with security best practices.",
            'controls': [
                {
                    'unique_id': f"FALLBACK-{hash(check_name) % 10000:04d}",
                    'reason': 'CHECK ENRICHMENT FAILED',
                    'confidence': 0.0
                }
            ],
            'benchmarks': [
                {
                    'unique_id': f"FALLBACK-{hash(check_name) % 10000:04d}",
                    'reason': 'CHECK ENRICHMENT FAILED',
                    'confidence': 0.0
                }
            ],
            'category': 'FALLBACK',
            'severity': 'FALLBACK',
            'tags': ['security', 'compliance', 'validation']
        }

    def _process_input(self, input_):
        # Get benchmark name from input
        try:
            enriched_check = self.enrich_check(input_, input_.benchmark.name)
        except self.CannotParseLLMResponse:
            enriched_check = self._create_fallback_enrichment(input_.check.name)

        return self.Output(check=enriched_check)
