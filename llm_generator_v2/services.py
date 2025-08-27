import os


import yaml
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import Type

from llm_generator_v2.yaml_loader import ModuleYamlMapping, ServiceYamlField
from con_mon.utils.llm.client import get_llm_client


class Service:
    class ValidationError(Exception):
        pass

    def __init__(
            self,
            module_config: ModuleYamlMapping,
            service_config: ServiceYamlField,
            data_root: str = "llm_generator_v2/data"
    ):
        self.llm_client = get_llm_client()
        self._module_config = module_config

        self._service_config = service_config
        self.index = self._service_config.index
        self.name = self._service_config.name
        self.input_model = self._service_config.input_model
        self.output_model = self._service_config.output_model
        self.data_root = Path(data_root)

        # Generate timestamp for this execution run
        self.execution_timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")

    @property
    def Input(self) -> Type[BaseModel]:
        """Access to dynamically generated Input model."""
        return self.input_model.pydantic_model

    @property
    def Output(self) -> Type[BaseModel]:
        """Access to dynamically generated Output model."""
        return self.output_model.pydantic_model

    def _write_input_yaml(self, data: BaseModel, path: Path):
        """Write input data to YAML file."""
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write input.yaml file
        with open(path, 'w') as f:
            yaml.dump(data.model_dump(), f, default_flow_style=False)

    def _read_input_yaml(self, path: Path) -> BaseModel:
        """Read input data from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            return self.Input(**data)

    def _get_data_folder_path(self, step_name: str) -> Path:
        """Generate path for input/output data files."""
        # Format: data/timestamp/section/step/input_or_output/
        return self.data_root / self.execution_timestamp / f"sec{self._module_config.index}_{self._module_config.name}" / f"step{self.index}_{step_name}"

    def _process_input(self, input_) -> BaseModel:
        """
        service code to be extended by Service classes
        """
        raise NotImplementedError()

    def _prepare_input(self, input_: BaseModel):
        """
        makes sure the input_ adheres to service input model
        should be in base class
        """
        return self.Input.model_validate(input_)

    def _save_input(self, input_: BaseModel):
        """
        Save input data to input.yaml file.
        """
        input_path = self._get_data_folder_path(self.name) / "input.yaml"
        self._write_input_yaml(input_, input_path)

    def _load_input(self) -> BaseModel:
        """
        Load input data from input.yaml file.
        """
        input_path = self._get_data_folder_path(self.name) / "input.yaml"
        return self._read_input_yaml(input_path)

    def _prepare_output(self, output: BaseModel | dict | str | bytes | bytearray, ):
        """
        makes sure the output adheres to service output model
        should be in base class
        """
        if isinstance(output, (str, bytes, bytearray)):
            return self.Output.model_validate_json(output)
        if isinstance(output, (dict, BaseModel)):
            return self.Output.model_validate(output)
        raise self.ValidationError(f'type {type(output)} is not supported')

    def _save_output(self, output: BaseModel):
        """
        saves output file in set data directory
        should be in base class
        """
        raise NotImplementedError()

    def execute(self, input_: BaseModel):
        input_ = self._prepare_input(input_)
        self._save_input(input_)

        output_dict = self._process_input(input_)

        output = self._prepare_output(output_dict)
        self._save_output(output)

        return output
