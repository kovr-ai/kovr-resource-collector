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
                    'unique_id': 'NIST-800-53-AC-3',
                    'reason': 'Generic access control mapping for security check',
                    'confidence': 0.5
                }
            ],
            'benchmarks': [
                {
                    'unique_id': 'MITRE-ATT&CK-T1078',
                    'reason': 'General security validation mapping',
                    'confidence': 0.5
                }
            ],
            'category': 'access_control',
            'severity': 'medium',
            'tags': ['security', 'compliance', 'validation']
        }

    def _process_input(self, input_):
        # Get benchmark name from input
        benchmark_name = getattr(input_.benchmark, 'name', 'OWASP') if hasattr(input_, 'benchmark') else 'OWASP'
        enriched_check = self.enrich_check(input_, benchmark_name)

        return self.Output(check=enriched_check)
