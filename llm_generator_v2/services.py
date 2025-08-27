from pydantic import BaseModel
from llm_generator_v2.yaml_loader import ServiceYamlField
from con_mon.utils.llm.client import get_llm_client


class Service:
    def __init__(
            self,
            service_config: ServiceYamlField,
    ):
        self.llm_client = get_llm_client()
        self._service_config = service_config
        self.index = self._service_config.index
        self.name = self._service_config.name
        self.input_model = self._service_config.input_model
        self.output_model = self._service_config.output_model

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
        raise NotImplementedError()

    def _save_input(self, input_: BaseModel):
        """
        this should be part of base class to read from data files
        and prepare full input for process function
        should be in base class
        """
        raise NotImplementedError()

    def _prepare_output(self, output: BaseModel):
        """
        makes sure the output adheres to service output model
        should be in base class
        """
        raise NotImplementedError()

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
