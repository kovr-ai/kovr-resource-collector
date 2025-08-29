import json
from llm_generator import services
from .templates import PROMPT, UNIQUE_ID


class ExtractCheckNamesService(services.Service):
    @staticmethod
    def _extract_from_text_fallback(text: str) -> list[str]:
        """Fallback method to extract check names if JSON parsing fails."""
        lines = text.strip().split('\n')
        check_names = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('**'):
                # Remove bullet points, numbers, quotes
                line = line.lstrip('- • * 1234567890. "\'').rstrip('"\'')
                if line:
                    check_names.append(line)

        return check_names

    def extract_check_names(self, input_) -> list[str]:
        prompt = PROMPT.format(
            benchmark_name=input_.benchmark.name,
            benchmark_version=input_.benchmark.version,
            literature=input_.benchmark.literature,
        )

        # Get response from LLM and parse JSON
        response = self.llm_client.generate_text(prompt)
        try:
            check_names = json.loads(response)
            return check_names if isinstance(check_names, list) else []
        except json.JSONDecodeError:
            # Fallback: try to extract from text if JSON parsing fails
            return self._extract_from_text_fallback(response)

    def generate_unique_id(self, input_, check_name):
        return UNIQUE_ID.format(
            benchmark_name=input_.benchmark.name,
            benchmark_version=input_.benchmark.version,
            check_name=check_name.lower().replace(' ', '-').replace('_', '-'),
        )

    def _process_input(self, input_):
        check_names = self.extract_check_names(input_)
        check_names = [
            self.generate_unique_id(input_, check_name)
            for check_name in check_names
        ]

        return self.Output(benchmark=dict(
            check_names=check_names,
        ))
