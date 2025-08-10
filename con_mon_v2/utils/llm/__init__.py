"""
LLM utilities for con_mon_v2.

Provides prompt templates, LLM client interfaces, and response processing.
"""

from .client import get_llm_client, LLMClient, LLMRequest, LLMResponse
from .prompts import (
    BasePrompt,
    ChecksPrompt,
    generate_checks
)

__all__ = [
    # Client
    'get_llm_client',
    'LLMClient', 
    'LLMRequest',
    'LLMResponse',
    # Prompts
    'BasePrompt',
    'ChecksPrompt',
    'generate_checks'
] 