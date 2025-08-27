import json
from llm_generator_v2.services import Service
from .templates import PROMPT


class EnrichIndividualChecks(Service):
    def enrich_check(self, input_, benchmark_name: str = "OWASP"):
        prompt = PROMPT.format(
            check_name=input_.check.name,
            benchmark_name=benchmark_name,
        )

        # Get response from LLM and parse JSON
        response = self.llm_client.generate_text(prompt)
        try:
            check_data = json.loads(response)
            return self._create_check_output(check_data)
        except json.JSONDecodeError:
            # Fallback: create basic enrichment
            return self._create_fallback_enrichment(input_.check.name)

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

    def _process_input(self, input_):
        enriched_check = self.enrich_check(input_)

        return self.Output(check=enriched_check)
