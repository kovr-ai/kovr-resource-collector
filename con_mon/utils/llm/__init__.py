"""
LLM Sub-module

This module provides a clean interface for Large Language Model operations
with separation of concerns between the LLM client and prompt handling.

Components:
- client: Singleton LLM client for Bedrock operations
- prompts: Prompt templates and post-processing classes
"""

from .client import LLMClient, get_llm_client
from .prompts import (
    ComplianceCheckPrompt,
    ControlAnalysisPrompt,
    GeneralPrompt,
    ChecksYamlPrompt,
    PromptResult,
    generate_compliance_check,
    analyze_control,
    generate_text,
    generate_checks_yaml
)

__all__ = [
    'LLMClient',
    'get_llm_client',
    'ComplianceCheckPrompt',
    'ControlAnalysisPrompt',
    'GeneralPrompt',
    'ChecksYamlPrompt',
    'PromptResult',
    'generate_compliance_check',
    'analyze_control',
    'generate_text',
    'generate_checks_yaml'
] 