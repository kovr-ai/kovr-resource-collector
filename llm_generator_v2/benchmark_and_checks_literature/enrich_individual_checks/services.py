import json
from pydantic import BaseModel

from llm_generator_v2 import services
from .templates import PROMPT


class EnrichIndividualChecksService(services.Service):
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

    def _get_input_filename(self, input_: BaseModel) -> str:
        """Generate unique filename for input based on check unique_id."""
        return f"{input_.check.unique_id}.yaml"

    def _get_output_filename(self, output: BaseModel) -> str:
        """Generate unique filename for output based on check unique_id."""
        return f"{output.check.unique_id}.yaml"

    def _process_input(self, input_):
        # Get benchmark name from input
        enriched_check = self.enrich_check(input_, input_.benchmark.name)
        enriched_check.update(unique_id=input_.check.unique_id)

        return self.Output(check=enriched_check)

    # def _load_output(self, input_):
    #     response = super()._load_output(input_)
    #     from pdb import set_trace;set_trace()
    #     return response

    # def _save_output(self, output):
    #     response = super()._save_output(output)
    #     from pdb import set_trace;set_trace()
    #     return response
