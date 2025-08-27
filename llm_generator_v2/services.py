import yaml
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import Type, List

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
        # self.execution_timestamp = '2025_08_27_10_44'
        
        # Counter to ensure unique filenames across multiple execute calls
        self._execution_counter = 0

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

    def _get_item_filename(self, item_data: dict, index: int) -> str:
        """Generate filename for individual array items"""
        # Try to use unique_id if available, otherwise use index-based naming
        if isinstance(item_data, dict):
            # Look for unique_id in nested structures
            for key, value in item_data.items():
                if isinstance(value, dict) and 'unique_id' in value:
                    return f"{value['unique_id']}.yaml"
                elif key == 'unique_id':
                    return f"{value}.yaml"
            
            # Try to generate unique name from check name if available
            if 'check' in item_data and isinstance(item_data['check'], dict) and 'name' in item_data['check']:
                check_name = item_data['check']['name']
                # Clean the name to be filename-safe
                safe_name = check_name.replace(' ', '_').replace('(', '').replace(')', '').replace(',', '').replace('.', '')
                return f"check_{index:03d}_{safe_name[:50]}.yaml"

        raise ValueError('filename not generated for output')

    def _save_input(self, input_: BaseModel):
        """Save input data - either as single input.yaml or array in input/ folder"""
        input_data = input_.model_dump()
        data_folder = self._get_data_folder_path()

        if self.input_model.is_list:
            # Handle array input: create input/ folder with individual files
            input_folder = data_folder / "input"
            input_folder.mkdir(parents=True, exist_ok=True)

            # Find the array field and save each item separately
            for field_name, field_value in input_data.items():
                if isinstance(field_value, list):
                    for i, item in enumerate(field_value):
                        filename = self._get_item_filename(item, i)
                        item_file = input_folder / filename
                        self._write_yaml(item_file, item)
                    break
        else:
            # Handle single input: save as input.yaml
            input_file = data_folder / "input.yaml"
            self._write_yaml(input_file, input_data)

    def _load_input(self) -> BaseModel:
        """Load input data - either from input.yaml or input/ folder array"""
        data_folder = self._get_data_folder_path()

        if self.input_model.is_list:
            # Handle array input: load from input/ folder
            input_folder = data_folder / "input"
            if not input_folder.exists():
                raise FileNotFoundError(f"Input folder not found: {input_folder}")

            # Load all YAML files from input folder
            items = []
            for yaml_file in sorted(input_folder.glob("*.yaml")):
                item_data = self._read_yaml(yaml_file)
                items.append(item_data)

            # Find the array field name and create input structure
            # For array models, the first field should be the array field
            if self.input_model.fields:
                first_field = self.input_model.fields[0]
                field_name = first_field.name
                clean_field_name = field_name.rstrip('[]')
                input_data = {clean_field_name: items}
            else:
                input_data = {'items': items}
        else:
            # Handle single input: load from input.yaml
            input_file = data_folder / "input.yaml"
            if not input_file.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
            input_data = self._read_yaml(input_file)

        return self.Input.model_validate(input_data)
    
    def _save_input_array(self, input_array: List[BaseModel]):
        """Save array of inputs to individual YAML files"""
        data_folder = self._get_data_folder_path()
        input_folder = data_folder / "input"
        input_folder.mkdir(parents=True, exist_ok=True)
        
        for i, input_item in enumerate(input_array):
            input_data = input_item.model_dump()
            filename = self._get_item_filename(input_data, self._execution_counter)
            item_file = input_folder / filename
            self._write_yaml(item_file, input_data)
    
    def _load_input_array(self) -> List[BaseModel]:
        """Load array of inputs from individual YAML files"""
        data_folder = self._get_data_folder_path()
        input_folder = data_folder / "input"
        
        if not input_folder.exists():
            return []
            
        items = []
        for yaml_file in sorted(input_folder.glob("*.yaml")):
            item_data = self._read_yaml(yaml_file)
            item = self.Input.model_validate(item_data)
            items.append(item)
        
        return items

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

    def _save_output(self, output_: BaseModel):
        """Save output data - either as single output.yaml or array in output/ folder"""
        output_data = output_.model_dump()
        data_folder = self._get_data_folder_path()

        if self.output_model.is_list:
            # Handle array output: create output/ folder with individual files
            output_folder = data_folder / "output"
            output_folder.mkdir(parents=True, exist_ok=True)

            # Find the array field and save each item separately
            for field_name, field_value in output_data.items():
                if isinstance(field_value, list):
                    for i, item in enumerate(field_value):
                        filename = self._get_item_filename(item, i)
                        item_file = output_folder / filename
                        self._write_yaml(item_file, item)
                    break
        else:
            # Handle single output: save as output.yaml
            output_file = data_folder / "output.yaml"
            self._write_yaml(output_file, output_data)

    def _match_input_output(self, input_: BaseModel, output_: BaseModel):
        raise NotImplementedError()

    def _load_output(self, input_: BaseModel) -> BaseModel | None:
        """Load output data - either from output.yaml or output/ folder array"""
        data_folder = self._get_data_folder_path()

        if self.output_model.is_list:
            # Handle array output: load from output/ folder
            output_folder = data_folder / "output"
            if not output_folder.exists():
                raise FileNotFoundError(f"Output folder not found: {output_folder}")

            # Load all YAML files from output folder
            for yaml_file in sorted(output_folder.glob("*.yaml")):
                output_data = self._read_yaml(yaml_file)
                output = self.Output.model_validate(output_data)
                if self._match_input_output(input_, output):
                    break
        else:
            # Handle single output: load from output.yaml
            output_file = data_folder / "output.yaml"
            if output_file.exists():
                output_data = self._read_yaml(output_file)
            else:
                output_data = None

        if output_data is None:
            return output_data

        return self.Output.model_validate(output_data)
    
    def _save_output_array(self, output_array: List[BaseModel]):
        """Save array of outputs to individual YAML files"""
        data_folder = self._get_data_folder_path()
        output_folder = data_folder / "output"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        for i, output_item in enumerate(output_array):
            output_data = output_item.model_dump()
            # Generate unique filename for outputs, even if unique_id is the same
            if isinstance(output_data, dict) and 'check' in output_data and isinstance(output_data['check'], dict):
                check_data = output_data['check']
                if 'unique_id' in check_data:
                    # Add index to make filename unique
                    unique_id = check_data['unique_id']
                    filename = f"{unique_id}_{i:03d}.yaml"
                else:
                    filename = self._get_item_filename(output_data, i)
            else:
                filename = self._get_item_filename(output_data, i)
            item_file = output_folder / filename
            self._write_yaml(item_file, output_data)
    
    def _load_output_array(self) -> List[BaseModel]:
        """Load array of outputs from individual YAML files"""
        data_folder = self._get_data_folder_path()
        output_folder = data_folder / "output"
        
        if not output_folder.exists():
            raise FileNotFoundError(f"Output folder not found: {output_folder}")
            
        items = []
        for yaml_file in sorted(output_folder.glob("*.yaml")):
            item_data = self._read_yaml(yaml_file)
            item = self.Output.model_validate(item_data)
            items.append(item)
        
        return items
    
    def _save_output_array_for_execution(self, output_array: List[BaseModel], execution_id: int):
        """Save array of outputs to individual YAML files with execution-specific naming"""
        data_folder = self._get_data_folder_path()
        output_folder = data_folder / "output"
        output_folder.mkdir(parents=True, exist_ok=True)
        
        for i, output_item in enumerate(output_array):
            output_data = output_item.model_dump()
            # Generate unique filename for outputs, using execution_id for uniqueness
            if isinstance(output_data, dict) and 'check' in output_data and isinstance(output_data['check'], dict):
                check_data = output_data['check']
                if 'unique_id' in check_data:
                    # Add execution_id to make filename unique across calls
                    unique_id = check_data['unique_id']
                    filename = f"{unique_id}_{execution_id:03d}.yaml"
                else:
                    filename = self._get_item_filename(output_data, execution_id)
            else:
                filename = self._get_item_filename(output_data, execution_id)
            item_file = output_folder / filename
            self._write_yaml(item_file, output_data)
    
    def _load_output_array_for_execution(self, execution_id: int) -> List[BaseModel]:
        """Load array of outputs from individual YAML files for specific execution"""
        data_folder = self._get_data_folder_path()
        output_folder = data_folder / "output"
        
        if not output_folder.exists():
            raise FileNotFoundError(f"Output folder not found: {output_folder}")
            
        items = []
        # Look for files with specific execution_id
        for yaml_file in sorted(output_folder.glob(f"*_{execution_id:03d}.yaml")):
            item_data = self._read_yaml(yaml_file)
            item = self.Output.model_validate(item_data)
            items.append(item)
        
        if not items:
            raise FileNotFoundError(f"No output files found for execution {execution_id}")
        
        return items

    def execute(self, input_: BaseModel | List[BaseModel]):
        if isinstance(input_, list):
            return [
                self.execute(item)
                for item in input_
            ]
        # Regular single object processing
        self._save_input(input_)

        output_dict = self._load_output(input_)
        if not output_dict:
            output_dict = self._process_input(input_)

        output = self._prepare_output(output_dict)
        self._save_output(output)

        return output
