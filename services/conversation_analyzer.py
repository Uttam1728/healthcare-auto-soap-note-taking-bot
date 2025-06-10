import json
import re
from typing import Dict, Any, List
import anthropic
from config import ANTHROPIC_API_KEY
from models.analysis_models import (
    TranscriptSegment, ConversationAnalysis, BasicConversationAnalysis,
    SpeakerAnalysis, ConversationSegment, SOAPComponent, SOAPNoteWithSources,
    AnalysisMetadata, BasicSOAPNote, SourceReference
)


class ConversationAnalyzer:
    """Service class for analyzing doctor-patient conversations using Claude AI"""
    
    def __init__(self):
        """Initialize the conversation analyzer with Anthropic client"""
        self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    
    def analyze_conversation(self, transcript_text: str) -> Dict[str, Any]:
        """Analyze doctor-patient conversation and generate basic SOAP note using Claude"""
        try:
            # Check if transcript is too small
            if len(transcript_text.strip()) < 10:
                return self._create_empty_analysis("Transcript too short for analysis")
            
            prompt = self._create_basic_analysis_prompt(transcript_text)
            
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            return self._parse_json_response(response_text)
            
        except Exception as e:
            print(f"Error analyzing conversation: {e}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def analyze_conversation_with_sources(self, transcript_text: str) -> Dict[str, Any]:
        """Enhanced analysis that maps each SOAP component to its source transcript excerpts"""
        try:
            # Check if transcript is too small
            if len(transcript_text.strip()) < 10:
                return self._create_empty_enhanced_analysis("Transcript too short for analysis")
            
            # Split transcript into numbered segments for easier reference
            transcript_segments = self._create_transcript_segments(transcript_text)
            
            prompt = self._create_enhanced_analysis_prompt(transcript_text, transcript_segments)
            
            message = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2500,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            
            # Parse the enhanced response with source mapping
            try:
                analysis = self._parse_enhanced_json_response(response_text)
                # Add the original transcript segments for reference
                analysis['transcript_segments'] = transcript_segments
                print(f"Successfully parsed enhanced analysis with sources")
                return analysis
                
            except Exception as e:
                print(f"Error parsing enhanced analysis: {e}")
                # Fallback to original analysis and convert to enhanced format
                original_analysis = self.analyze_conversation(transcript_text)
                return self._convert_to_enhanced_format(original_analysis, transcript_segments)
                
        except Exception as e:
            print(f"Error in enhanced analysis: {e}")
            # Fallback to original analysis and convert to enhanced format
            original_analysis = self.analyze_conversation(transcript_text)
            transcript_segments = self._create_transcript_segments(transcript_text)
            return self._convert_to_enhanced_format(original_analysis, transcript_segments)
    
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
    
    def _create_basic_analysis_prompt(self, transcript_text: str) -> str:
        """Create prompt for basic conversation analysis"""
        return f"""
        Please analyze this doctor-patient conversation transcript and provide both a structured analysis AND a clinical SOAP note:

        TRANSCRIPT:
        {transcript_text}

        Format your response as JSON with this structure:
        {{
            "speaker_analysis": {{
                "doctor_segments": ["segment1", "segment2"],
                "patient_segments": ["segment1", "segment2"],
                "doctor_percentage": 60,
                "patient_percentage": 40
            }},
            "conversation_segments": [
                {{
                    "type": "greeting",
                    "content": "Hello, how are you feeling today?",
                    "speaker": "doctor"
                }}
            ],
            "medical_topics": ["symptom1", "symptom2", "diagnosis"],
            "summary": "Brief summary of the consultation",
            "soap_note": {{
                "subjective": "Patient's reported symptoms, concerns, and history",
                "objective": "Observable findings, physical examination results",
                "assessment": "Clinical impression, primary diagnosis",
                "plan": "Treatment plan including medications, tests, follow-up"
            }}
        }}
        """
    
    def _create_enhanced_analysis_prompt(self, transcript_text: str, transcript_segments: List[Dict[str, Any]]) -> str:
        """Create prompt for enhanced conversation analysis with source mapping"""
        segments_text = chr(10).join([f"[{seg['id']}] {seg['text']}" for seg in transcript_segments])
        
        return f"""
        You are a medical AI assistant analyzing a doctor-patient conversation.

        TRANSCRIPT (with segment numbers for reference):
        {segments_text}

        Respond with VALID JSON in this exact structure:
        {{
            "speaker_analysis": {{
                "doctor_segments": ["segment1", "segment2"],
                "patient_segments": ["segment1", "segment2"],
                "doctor_percentage": 60,
                "patient_percentage": 40
            }},
            "conversation_segments": [
                {{
                    "type": "greeting",
                    "content": "Hello, how are you feeling today?",
                    "speaker": "doctor"
                }}
            ],
            "medical_topics": ["symptom1", "symptom2", "diagnosis"],
            "summary": "Brief summary of the consultation",
            "soap_note_with_sources": {{
                "subjective": {{
                    "content": "Patient reports symptoms",
                    "sources": [
                        {{
                            "segment_ids": [3, 5],
                            "excerpt": "I have chest pain",
                            "reasoning": "Patient describing chief complaint"
                        }}
                    ],
                    "confidence": 85
                }},
                "objective": {{
                    "content": "Physical examination findings",
                    "sources": [],
                    "confidence": 80
                }},
                "assessment": {{
                    "content": "Clinical diagnosis",
                    "sources": [],
                    "confidence": 75
                }},
                "plan": {{
                    "content": "Treatment plan",
                    "sources": [],
                    "confidence": 90
                }}
            }},
            "analysis_metadata": {{
                "total_segments": {len(transcript_segments)},
                "overall_confidence": 85
            }}
        }}
        """
    
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