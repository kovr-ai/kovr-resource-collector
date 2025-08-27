from llm_generator_v2.services import Service

from .models import (
    Input,
    Output
)
from .templates import PROMPT, UNIQUE_ID


class GenerateBenchmarkLiterature(Service):
    def generate_unique_id(self, input_: Input) -> str:
        return UNIQUE_ID.format(
            benchmark_name=input_.name,
            benchmark_version=input_.version,
        )

    def generate_literature(self, input_: Input) -> str:
        prompt = PROMPT.format(
            benchmark_name=input_.name,
            benchmark_version=input_.version,
        )
        return self.llm_client.generate_text(prompt)

    def _process_input(self, input_: Input) -> Output:
        unique_id = self.generate_unique_id(input_)
        literature = self.generate_literature(input_)

        return Output(
            unique_id=unique_id,
            literature=literature,
        )

