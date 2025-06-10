"""
Prompt manager for handling conversation analysis prompts.
Provides methods to load and format prompt templates.
"""

from typing import Dict, Any, List
from .basic_analysis_prompt import BASIC_ANALYSIS_PROMPT_TEMPLATE
from .enhanced_analysis_prompt import ENHANCED_ANALYSIS_PROMPT_TEMPLATE


class PromptManager:
    """Manager class for handling conversation analysis prompts"""
    
    @staticmethod
    def get_basic_analysis_prompt(transcript_text: str) -> str:
        """
        Get formatted basic analysis prompt.
        
        Args:
            transcript_text: The conversation transcript to analyze
            
        Returns:
            Formatted prompt string ready for API call
        """
        return BASIC_ANALYSIS_PROMPT_TEMPLATE.format(
            transcript_text=transcript_text
        )
    
    @staticmethod
    def get_enhanced_analysis_prompt(transcript_text: str, transcript_segments: List[Dict[str, Any]]) -> str:
        """
        Get formatted enhanced analysis prompt with source mapping.
        
        Args:
            transcript_text: The conversation transcript to analyze
            transcript_segments: List of numbered transcript segments
            
        Returns:
            Formatted prompt string ready for API call
        """
        segments_text = '\n'.join([f"[{seg['id']}] {seg['text']}" for seg in transcript_segments])
        
        return ENHANCED_ANALYSIS_PROMPT_TEMPLATE.format(
            segments_text=segments_text,
            total_segments=len(transcript_segments)
        ) 