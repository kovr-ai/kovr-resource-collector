import json
from llm_generator_v2.services import Service
from .templates import PROMPT


class ExtractCheckNames(Service):
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

    def _process_input(self, input_):
        check_names = self.extract_check_names(input_)

        # Use dynamic Output model
        return self.Output(
            benchmark={'check_names': check_names}
        )
