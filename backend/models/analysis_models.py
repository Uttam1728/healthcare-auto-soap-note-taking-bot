from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import json


@dataclass
class ConversationSegment:
    """Represents a segment of conversation with validation"""
    type: str
    content: str
    speaker: str
    timestamp: Optional[float] = None
    confidence: Optional[float] = None
    
    def __post_init__(self):
        """Validate segment data"""
        if not self.content or not self.content.strip():
            raise ValueError("Content cannot be empty")
        
        if self.speaker not in ['doctor', 'patient', 'unknown']:
            self.speaker = 'unknown'
        
        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'type': self.type,
            'content': self.content,
            'speaker': self.speaker,
            'timestamp': self.timestamp,
            'confidence': self.confidence
        }


@dataclass
class SpeakerAnalysis:
    """Analysis of speaker distribution in conversation with validation"""
    doctor_segments: List[str] = field(default_factory=list)
    patient_segments: List[str] = field(default_factory=list)
    doctor_percentage: float = 0.0
    patient_percentage: float = 0.0
    total_segments: int = 0
    
    def __post_init__(self):
        """Validate and calculate speaker analysis"""
        # Ensure percentages are valid
        if not (0.0 <= self.doctor_percentage <= 100.0):
            raise ValueError("Doctor percentage must be between 0 and 100")
        if not (0.0 <= self.patient_percentage <= 100.0):
            raise ValueError("Patient percentage must be between 0 and 100")
        
        # Calculate total segments if not provided
        if self.total_segments == 0:
            self.total_segments = len(self.doctor_segments) + len(self.patient_segments)
        
        # Ensure percentages add up to approximately 100%
        total_percentage = self.doctor_percentage + self.patient_percentage
        if self.total_segments > 0 and abs(total_percentage - 100.0) > 1.0:
            # Normalize percentages
            if total_percentage > 0:
                self.doctor_percentage = (self.doctor_percentage / total_percentage) * 100.0
                self.patient_percentage = (self.patient_percentage / total_percentage) * 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'doctor_segments': self.doctor_segments,
            'patient_segments': self.patient_segments,
            'doctor_percentage': round(self.doctor_percentage, 2),
            'patient_percentage': round(self.patient_percentage, 2),
            'total_segments': self.total_segments
        }


@dataclass
class TranscriptSegment:
    """Individual segment of the transcript with metadata"""
    id: int
    text: str
    start_pos: int
    end_pos: int


@dataclass
class SourceReference:
    """Reference to source segments that support a SOAP component with validation"""
    segment_ids: List[int]
    excerpt: str
    reasoning: str
    confidence_score: Optional[float] = None
    
    def __post_init__(self):
        """Validate source reference data"""
        if not self.segment_ids:
            raise ValueError("At least one segment ID is required")
        
        if not self.excerpt or not self.excerpt.strip():
            raise ValueError("Excerpt cannot be empty")
        
        if not self.reasoning or not self.reasoning.strip():
            raise ValueError("Reasoning cannot be empty")
        
        if self.confidence_score is not None and not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        # Ensure all segment IDs are positive integers
        for segment_id in self.segment_ids:
            if not isinstance(segment_id, int) or segment_id <= 0:
                raise ValueError("All segment IDs must be positive integers")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'segment_ids': self.segment_ids,
            'excerpt': self.excerpt,
            'reasoning': self.reasoning,
            'confidence_score': self.confidence_score
        }


@dataclass
class SOAPComponent:
    """SOAP note component with source references"""
    content: str
    sources: List[SourceReference] = field(default_factory=list)
    confidence: int = 0
    sub_components: Dict[str, 'SOAPComponent'] = field(default_factory=dict)


@dataclass
class SOAPNoteWithSources:
    """Complete SOAP note with source mapping"""
    subjective: SOAPComponent
    objective: SOAPComponent
    assessment: SOAPComponent
    plan: SOAPComponent


@dataclass
class AnalysisMetadata:
    """Metadata about the analysis process"""
    total_segments: int = 0
    overall_confidence: int = 0
    processing_timestamp: Optional[str] = None


@dataclass
class ConversationAnalysis:
    """Complete conversation analysis result"""
    speaker_analysis: SpeakerAnalysis
    conversation_segments: List[ConversationSegment]
    medical_topics: List[str]
    summary: str
    soap_note_with_sources: SOAPNoteWithSources
    transcript_segments: List[TranscriptSegment]
    analysis_metadata: AnalysisMetadata
    error: Optional[str] = None
    reason: Optional[str] = None


@dataclass
class BasicSOAPNote:
    """Basic SOAP note without source mapping"""
    subjective: str
    objective: str
    assessment: str
    plan: str


@dataclass
class BasicConversationAnalysis:
    """Basic conversation analysis without enhanced source mapping"""
    speaker_analysis: SpeakerAnalysis
    conversation_segments: List[ConversationSegment]
    medical_topics: List[str]
    summary: str
    soap_note: BasicSOAPNote
    error: Optional[str] = None
    reason: Optional[str] = None 