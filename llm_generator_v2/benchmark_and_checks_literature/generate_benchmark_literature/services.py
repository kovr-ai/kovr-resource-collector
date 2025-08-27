from llm_generator_v2.services import Service

from .models import (
    Input,
    Output
)


class GenerateBenchmarkLiterature(Service):
    def _process_input(self, input_: Input) -> Output:
        raise NotImplementedError()

