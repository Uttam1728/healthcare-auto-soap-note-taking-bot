import json
import re
import time
from typing import Dict, Any, List, Optional
import anthropic
from config import config
from ..models.analysis_models import (
    TranscriptSegment, ConversationAnalysis, BasicConversationAnalysis,
    SpeakerAnalysis, ConversationSegment, SOAPComponent, SOAPNoteWithSources,
    AnalysisMetadata, BasicSOAPNote, SourceReference
)
from ..prompts import PromptManager
from ..utils.logging_config import LoggingMixin, log_performance
from ..utils.exceptions import (
    AnthropicAPIError, JSONParsingError, InsufficientDataError,
    ErrorHandler
)
from ..utils.cache import analysis_cache


class ConversationAnalyzer(LoggingMixin):
    """Service class for analyzing doctor-patient conversations using Claude AI"""
    
    def __init__(self):
        """Initialize the conversation analyzer with Anthropic client"""
        # Validate API key
        if not config.api.anthropic_api_key or config.api.anthropic_api_key == 'REPLACE_WITH_YOUR_ANTHROPIC_API_KEY_HERE':
            raise AnthropicAPIError("Anthropic API key not configured")
        
        self.anthropic_client = anthropic.Anthropic(
            api_key=config.api.anthropic_api_key,
            timeout=config.ai.timeout_seconds
        )
        self.analysis_count = 0
    
    @log_performance
    def analyze_conversation(self, transcript_text: str) -> Dict[str, Any]:
        """Analyze doctor-patient conversation and generate basic SOAP note using Claude"""
        try:
            self.log_operation("analyze_conversation_basic")
            
            # Validate transcript
            ErrorHandler.validate_transcript_length(transcript_text, min_length=10)
            
            # Check cache first
            cached_result = analysis_cache.get_analysis(transcript_text, "basic")
            if cached_result:
                self.logger.info("Returning cached basic analysis")
                return cached_result
            
            prompt = PromptManager.get_basic_analysis_prompt(transcript_text)
            
            message = self.anthropic_client.messages.create(
                model=config.ai.model,
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            result = self._parse_json_response(response_text)
            
            # Cache successful result
            if "error" not in result:
                analysis_cache.cache_analysis(transcript_text, result, "basic")
                self.logger.info("Cached basic analysis result")
            
            self.analysis_count += 1
            return result
            
        except InsufficientDataError as e:
            self.log_error(e, "analyze_conversation_basic")
            return self._create_empty_analysis(e.message)
        except Exception as e:
            error = ErrorHandler.handle_api_error(e, "Anthropic")
            self.log_error(error, "analyze_conversation_basic")
            return {"error": f"Analysis failed: {error.message}"}
    
    @log_performance
    def analyze_conversation_with_sources(self, transcript_text: str) -> Dict[str, Any]:
        """Enhanced analysis that maps each SOAP component to its source transcript excerpts"""
        try:
            self.log_operation("analyze_conversation_enhanced")
            
            # Validate transcript
            ErrorHandler.validate_transcript_length(transcript_text, min_length=10)
            
            # Check cache first
            cached_result = analysis_cache.get_analysis(transcript_text, "enhanced")
            if cached_result:
                self.logger.info("Returning cached enhanced analysis")
                return cached_result
            
            # Split transcript into numbered segments for easier reference
            transcript_segments = self._create_transcript_segments(transcript_text)
            
            prompt = PromptManager.get_enhanced_analysis_prompt(transcript_text, transcript_segments)
            
            message = self.anthropic_client.messages.create(
                model=config.ai.model,
                max_tokens=config.ai.max_tokens,
                temperature=config.ai.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Parse the enhanced response with source mapping
            try:
                analysis = self._parse_enhanced_json_response(response_text)
                # Add the original transcript segments for reference
                analysis['transcript_segments'] = transcript_segments
                
                # Cache successful result
                analysis_cache.cache_analysis(transcript_text, analysis, "enhanced")
                self.logger.info("Successfully parsed and cached enhanced analysis with sources")
                
                self.analysis_count += 1
                return analysis
                
            except JSONParsingError as e:
                self.logger.warning(f"Enhanced analysis parsing failed, falling back to basic: {e}")
                # Fallback to original analysis and convert to enhanced format
                original_analysis = self.analyze_conversation(transcript_text)
                return self._convert_to_enhanced_format(original_analysis, transcript_segments)
                
        except InsufficientDataError as e:
            self.log_error(e, "analyze_conversation_enhanced")
            return self._create_empty_enhanced_analysis(e.message)
        except Exception as e:
            error = ErrorHandler.handle_api_error(e, "Anthropic")
            self.log_error(error, "analyze_conversation_enhanced")
            
            # Fallback to basic analysis
            try:
                self.logger.info("Attempting fallback to basic analysis")
                original_analysis = self.analyze_conversation(transcript_text)
                transcript_segments = self._create_transcript_segments(transcript_text)
                return self._convert_to_enhanced_format(original_analysis, transcript_segments)
            except Exception as fallback_error:
                self.log_error(fallback_error, "analyze_conversation_enhanced_fallback")
                return self._create_empty_enhanced_analysis(f"Analysis failed: {error.message}")
    
    def get_analyzer_stats(self) -> Dict[str, Any]:
        """Get statistics for the analyzer"""
        return {
            'total_analyses': self.analysis_count,
            'cache_stats': analysis_cache.stats()
        }
    
    def _create_transcript_segments(self, transcript_text: str) -> List[Dict[str, Any]]:
        """Split transcript into numbered segments for easier reference"""
        transcript_segments = []
        sentences = transcript_text.split('. ')
        for i, sentence in enumerate(sentences):
            if sentence.strip():
                transcript_segments.append({
                    "id": i + 1,
                    "text": sentence.strip() + ('.' if not sentence.endswith('.') else ''),
                    "start_pos": transcript_text.find(sentence),
                    "end_pos": transcript_text.find(sentence) + len(sentence)
                })
        return transcript_segments
    

    

    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from Claude with fallback handling"""
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group().strip()
                cleaned_json = self._clean_json_text(json_text)
                return json.loads(cleaned_json)
            else:
                return {"error": "No JSON found in response", "raw_response": response_text}
        except Exception as e:
            return {"error": f"Analysis processing failed: {str(e)}", "raw_response": response_text}
    
    def _parse_enhanced_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse enhanced JSON response with source mapping"""
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_text = json_match.group().strip()
            cleaned_json = self._clean_json_text(json_text)
            return json.loads(cleaned_json)
        else:
            raise ValueError("No JSON found in response")
    
    def _clean_json_text(self, json_text: str) -> str:
        """Clean JSON text by escaping special characters"""
        cleaned_json = json_text
        cleaned_json = re.sub(r'(?<!\\)\n', '\\n', cleaned_json)
        cleaned_json = re.sub(r'(?<!\\)\t', '\\t', cleaned_json)
        cleaned_json = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned_json)
        return cleaned_json
    
    def _convert_to_enhanced_format(self, original_analysis: Dict[str, Any], transcript_segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert original analysis format to enhanced format with source mapping"""
        if "error" in original_analysis:
            return original_analysis
        
        enhanced_soap = {}
        if "soap_note" in original_analysis:
            for section_key, content in original_analysis["soap_note"].items():
                enhanced_soap[section_key] = {
                    "content": content,
                    "sources": [],
                    "confidence": 80
                }
        
        enhanced_analysis = {
            "speaker_analysis": original_analysis.get("speaker_analysis", {
                "doctor_segments": [],
                "patient_segments": [],
                "doctor_percentage": 50,
                "patient_percentage": 50
            }),
            "conversation_segments": original_analysis.get("conversation_segments", []),
            "medical_topics": original_analysis.get("medical_topics", []),
            "summary": original_analysis.get("summary", "Analysis completed"),
            "soap_note_with_sources": enhanced_soap,
            "transcript_segments": transcript_segments
        }
        
        return enhanced_analysis
    
    def _create_empty_analysis(self, reason: str) -> Dict[str, Any]:
        """Create empty analysis for short transcripts"""
        return {
            "error": "Transcript too short for analysis",
            "reason": reason,
            "speaker_analysis": {
                "doctor_segments": [],
                "patient_segments": [],
                "doctor_percentage": 0,
                "patient_percentage": 0
            },
            "conversation_segments": [],
            "medical_topics": [],
            "summary": "Insufficient conversation content for analysis",
            "soap_note": {
                "subjective": "Insufficient data - conversation too brief",
                "objective": "Not documented - no clinical findings available",
                "assessment": "Cannot assess - inadequate clinical information",
                "plan": "Unable to formulate plan - recommend longer conversation"
            }
        }
    
    def _create_empty_enhanced_analysis(self, reason: str) -> Dict[str, Any]:
        """Create empty enhanced analysis for short transcripts"""
        return {
            "error": "Transcript too short for analysis",
            "reason": reason,
            "speaker_analysis": {
                "doctor_segments": [],
                "patient_segments": [],
                "doctor_percentage": 0,
                "patient_percentage": 0
            },
            "conversation_segments": [],
            "medical_topics": [],
            "summary": "Insufficient conversation content for analysis",
            "soap_note_with_sources": {
                "subjective": {
                    "content": "Insufficient data - conversation too brief",
                    "sources": [],
                    "confidence": 0
                },
                "objective": {
                    "content": "Not documented - no conversation recorded",
                    "sources": [],
                    "confidence": 0
                },
                "assessment": {
                    "content": "Cannot assess - inadequate information",
                    "sources": [],
                    "confidence": 0
                },
                "plan": {
                    "content": "Unable to formulate plan",
                    "sources": [],
                    "confidence": 0
                }
            }
        } 