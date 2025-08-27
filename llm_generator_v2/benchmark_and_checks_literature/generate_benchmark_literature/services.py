from llm_generator_v2 import services
from .templates import PROMPT, UNIQUE_ID


class Service(services.Service):
    def generate_unique_id(self, input_) -> str:
        return UNIQUE_ID.format(
            benchmark_name=input_.benchmark.name,
            benchmark_version=input_.benchmark.version,
        )

    def generate_literature(self, input_) -> str:
        prompt = PROMPT.format(
            benchmark_name=input_.benchmark.name,
            benchmark_version=input_.benchmark.version,
        )
        return self.llm_client.generate_text(prompt)

    def _process_input(self, input_):
        unique_id = self.generate_unique_id(input_)
        literature = self.generate_literature(input_)

        return self.Output(benchmark=dict(
            unique_id=unique_id,
            literature=literature,
        ))

