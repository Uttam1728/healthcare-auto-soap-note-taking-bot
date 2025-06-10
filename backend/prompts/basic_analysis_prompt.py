"""
Basic conversation analysis prompt template.
Used for generating SOAP notes from doctor-patient conversations.
"""

BASIC_ANALYSIS_PROMPT_TEMPLATE = """
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