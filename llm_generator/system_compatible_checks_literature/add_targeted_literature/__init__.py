"""
Dynamic model generation for services.
Models are automatically created from execution.yaml configuration.
"""

from pathlib import Path
from llm_generator import service_initializer
from .services import AddTargetedLiteratureService

__all__ = service_initializer.setup(
    service_class=AddTargetedLiteratureService,
    current_path=Path(__file__).parent,
    globals_=globals()
)
