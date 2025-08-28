import yaml
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import Type, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_generator_v2.yaml_loader import ModuleYamlMapping, ServiceYamlField
from con_mon.utils.llm.client import get_llm_client


class Service:
    class ValidationError(Exception):
        pass
    class GenerateUniqueFilepath(Exception):
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
        self.execution_timestamp = 'debugging'

    @property
    def Input(self) -> Type[BaseModel]:
        """Access to dynamically generated Input model."""
        return self.input_model.pydantic_model

    @property
    def Output(self) -> Type[BaseModel]:
        """Access to dynamically generated Output model."""
        return self.output_model.pydantic_model

    @property
    def input_filename(self) -> str:
        return 'input.yaml'

    @property
    def output_filename(self) -> str:
        return 'output.yaml'

    def _write_yaml(self, file_path: Path, data: dict):
        """Write data to YAML file."""
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write YAML file
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def _read_yaml(self, file_path: Path) -> dict:
        """Read data from YAML file."""
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_data_folder_path(self) -> Path:
        """Generate path for input/output data files."""
        # Format: data/timestamp/section/step/
        return self.data_root / self.execution_timestamp / f"sec{self._module_config.index}_{self._module_config.name}" / f"step{self.index}_{self.name}"

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

    def _get_input_filename(self, input_: BaseModel) -> str:
        raise NotImplementedError()

    def _save_input(self, input_: BaseModel):
        """Save input data - either as single input.yaml or array in input/ folder"""
        input_data = input_.model_dump()
        data_folder = self._get_data_folder_path()

        if self.input_model.is_list:
            # Handle array input: create input/ folder with individual files
            input_folder = data_folder / "input"
            input_folder.mkdir(parents=True, exist_ok=True)

            filename = self._get_input_filename(input_)
            item_file = input_folder / filename
            self._write_yaml(item_file, input_data)
        else:
            # Handle single input: save as input.yaml
            input_file = data_folder / "input.yaml"
            self._write_yaml(input_file, input_data)

    def _prepare_output(self, output: BaseModel | List[BaseModel] | dict | str | bytes | bytearray):
        """
        makes sure the output adheres to service output model
        should be in base class
        """
        if isinstance(output, list):
            return [
                self._prepare_output(o)
                for o in output
            ]
        if isinstance(output, (str, bytes, bytearray)):
            return self.Output.model_validate_json(output)
        if isinstance(output, (dict, BaseModel)):
            return self.Output.model_validate(output)
        if isinstance(output, self.Output):
            return output
        raise self.ValidationError(f'type {type(output)} is not supported')

    def _get_output_filename(self, output_: BaseModel) -> str:
        raise NotImplementedError()

    def _save_output(self, output: BaseModel):
        """Save output data - either as single output.yaml or array in output/ folder"""
        output_data = output.model_dump()
        data_folder = self._get_data_folder_path()

        if self.output_model.is_list:
            # Handle array output: create output/ folder with individual files
            output_folder = data_folder / "output"
            output_folder.mkdir(parents=True, exist_ok=True)

            filename = self._get_output_filename(output)
            item_file = output_folder / filename
            self._write_yaml(item_file, output_data)
        else:
            # Handle single output: save as output.yaml
            output_file = data_folder / "output.yaml"
            self._write_yaml(output_file, output_data)

    def _load_output(self, input_: BaseModel) -> BaseModel | None:
        """Save output data - either as single output.yaml or array in output/ folder"""
        data_folder = self._get_data_folder_path()

        if self.output_model.is_list:
            # Handle array output: create output/ folder with individual files
            output_folder = data_folder / "output"
            output_folder.mkdir(parents=True, exist_ok=True)

            filename = self._get_output_filename(input_)
            output_file = output_folder / filename
        else:
            # Handle single output: save as output.yaml
            output_file = data_folder / "output.yaml"

        if output_file.exists():
            output_data = self._read_yaml(output_file)
            return self.Output.model_validate(output_data)
        else:
            return None

    def execute(
            self,
            input_: BaseModel | List[BaseModel],
            threads: int | None = None,
    ):
        if isinstance(input_, list):
            if threads and threads > 1:
                print(f'Opening {threads} threads...')
                return self.execute_threads(input_, threads)
                # return self.execute(input_)
            else:
                # Sequential processing (original behavior)
                print('Sequential processing...')
                return [
                    self.execute(item)
                    for item in input_
                ]
        # Regular single object processing
        self._save_input(input_)

        output_dict = self._load_output(input_)
        if not output_dict:
            output_dict = self._process_input(input_)
            # try:
            #     output_dict = self._process_input(input_)
            # except Exception:
            #     from pdb import set_trace;set_trace()

        output = self._prepare_output(output_dict)
        self._save_output(output)

        return output

    def execute_threads(
            self,
            input_: BaseModel | List[BaseModel],
            threads: int,
    ):
        # Parallel processing using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # Submit all tasks
            future_to_input = {
                executor.submit(self.execute, item): item
                for item in input_
            }

            # Collect results in original order
            results = []
            for item in input_:
                for future, original_input in future_to_input.items():
                    if original_input is item:
                        results.append(future.result())
                        break

            return results
