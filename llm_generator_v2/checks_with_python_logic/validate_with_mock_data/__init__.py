"""
Dynamic model generation for services.
Models are automatically created from execution.yaml configuration.
"""

from pathlib import Path
from llm_generator_v2 import service_initializer
from .services import ValidateWithMockDataService

__all__ = service_initializer.setup(
    service_class=ValidateWithMockDataService,
    current_path=Path(__file__).parent,
    globals_=globals()
)
