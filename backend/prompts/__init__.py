"""
Prompts package for healthcare SOAP note generation.
Contains all prompt templates used by the conversation analyzer.
"""

from .basic_analysis_prompt import BASIC_ANALYSIS_PROMPT_TEMPLATE
from .enhanced_analysis_prompt import ENHANCED_ANALYSIS_PROMPT_TEMPLATE
from .prompt_manager import PromptManager

__all__ = [
    'BASIC_ANALYSIS_PROMPT_TEMPLATE',
    'ENHANCED_ANALYSIS_PROMPT_TEMPLATE',
    'PromptManager'
] 