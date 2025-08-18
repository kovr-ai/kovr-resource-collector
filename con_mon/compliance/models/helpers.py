"""
Helper models for displaying data with relationships.
These are not 1:1 database mappings but composite views.
"""

from typing import List
from pydantic import Field

from .framework import Framework
from .control import Control
from .standard import Standard
from .checks import Check


class FrameworkWithControls(Framework):
    """Framework with its associated controls."""
    controls: List[Control] = Field(default_factory=list, description="Controls belonging to this framework")


class StandardWithControls(Standard):
    """Standard with its control mappings.""" 
    controls: List[Control] = Field(default_factory=list, description="Controls mapped to this standard")


class ControlWithStandards(Control):
    """Control with its mapped standards."""
    standards: List[Standard] = Field(default_factory=list, description="Standards that map to this control")


class ControlWithChecks(Control):
    """Control with its associated checks."""
    checks: List[Check] = Field(default_factory=list, description="Checks that validate this control")


class CheckWithControls(Check):
    """Check with its associated controls."""
    controls: List[Control] = Field(default_factory=list, description="Controls that this check validates") 