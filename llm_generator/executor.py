import importlib
from pathlib import Path
# from collections import ChainMap

from pydantic import BaseModel
from mergedeep import merge

from .yaml_loader import ExecutionYamlMapping


class Executor(object):
    def __init__(
        self,
        execution_yaml_path: Path | None = None
    ):
        # Get the execution.yaml path relative to this module
        self._yaml_path = execution_yaml_path or Path(__file__).parents[0] / "execution.yaml"
        # Load execution configuration
        self._config = ExecutionYamlMapping.load_yaml(self._yaml_path)

    def execute(
        self,
        input_dict: dict | BaseModel,
    ) -> BaseModel:
        if isinstance(input_dict, BaseModel):
            input_dict = input_dict.model_dump()

        for module_config in self._config.modules:
            # module = importlib.import_module(module_config.name)
            for step_config in module_config.steps:
                step_module_path = f'{module_config.name}.{step_config.name}'
                step = importlib.import_module(step_module_path)

                input_object = step.service.Input.model_validate(input_dict)
                print(f'input_object: {input_object}')
                print(f'step: {step_module_path} with input: {input_object}')
                output_object = step.service.execute(input_object)
                print(f'step: {step_module_path} with output: {output_object}')
                input_dict = merge(input_object.model_dump(), output_object.model_dump())

        return output_object
