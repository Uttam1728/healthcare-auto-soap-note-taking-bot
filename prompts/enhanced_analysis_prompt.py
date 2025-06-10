"""
Enhanced conversation analysis prompt template.
Used for generating SOAP notes with source mapping from doctor-patient conversations.
"""

ENHANCED_ANALYSIS_PROMPT_TEMPLATE = """
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
        "total_segments": {total_segments},
        "overall_confidence": 85
    }}
}}
""" 