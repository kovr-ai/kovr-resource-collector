from pydantic import BaseModel
from llm_generator_v2.services import Service


class GenerateBenchmarkLiterature(Service):
    def _process_input(self, input_) -> BaseModel:
        raise NotImplementedError()

