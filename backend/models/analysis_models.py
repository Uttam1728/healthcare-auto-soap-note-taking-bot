from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ConversationSegment:
    """Represents a segment of conversation"""
    type: str
    content: str
    speaker: str


@dataclass
class SpeakerAnalysis:
    """Analysis of speaker distribution in conversation"""
    doctor_segments: List[str] = field(default_factory=list)
    patient_segments: List[str] = field(default_factory=list)
    doctor_percentage: float = 0.0
    patient_percentage: float = 0.0


@dataclass
class TranscriptSegment:
    """Individual segment of the transcript with metadata"""
    id: int
    text: str
    start_pos: int
    end_pos: int


@dataclass
class SourceReference:
    """Reference to source segments that support a SOAP component"""
    segment_ids: List[int]
    excerpt: str
    reasoning: str


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