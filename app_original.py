from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import asyncio
import json
import base64
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents
from deepgram.clients.live.v1 import LiveOptions
from config import DEEPGRAM_API_KEY, ANTHROPIC_API_KEY
import anthropic
import re

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global variables
deepgram_connection = None
current_session_id = None
full_transcript = ""
conversation_analysis = None

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def analyze_conversation(transcript_text):
    """Analyze doctor-patient conversation and generate SOAP note using Claude"""
    try:
        # Check if transcript is too small
        if len(transcript_text.strip()) < 10:
            return {
                "error": "Transcript too short for analysis",
                "reason": "The recorded conversation is too brief to generate a meaningful medical analysis. Please record a longer conversation with more clinical content.",
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
                    "subjective": "Insufficient data - conversation too brief to extract patient symptoms or concerns",
                    "objective": "Not documented - no clinical findings available from brief conversation",
                    "assessment": "Cannot assess - inadequate clinical information provided in short conversation",
                    "plan": "Unable to formulate plan - recommend longer clinical conversation for proper documentation"
                }
            }
        
        prompt = f"""
        Please analyze this doctor-patient conversation transcript and provide both a structured analysis AND a clinical SOAP note:

        TRANSCRIPT:
        {transcript_text}

        Please provide a comprehensive analysis including:

        1. **SPEAKER IDENTIFICATION**: Identify which parts are likely spoken by the doctor vs patient
        2. **CONVERSATION SEGMENTS**: Break down the conversation into key segments
        3. **DISTRIBUTION ANALYSIS**: Provide percentages of talking time between doctor and patient
        4. **KEY MEDICAL TOPICS**: Extract main medical topics discussed
        5. **SOAP NOTE**: Generate a professional clinical SOAP note from this conversation

        IMPORTANT: Always respond with valid JSON in the exact structure below, even if the transcript is short or lacks medical content. If there's insufficient information, provide reasons in the appropriate fields.

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
                "subjective": "Patient's reported symptoms, concerns, and history in their own words. Include chief complaint, history of present illness, review of systems, past medical history, medications, allergies, social history as mentioned.",
                "objective": "Observable findings, physical examination results, vital signs, and any diagnostic test results mentioned during the conversation.",
                "assessment": "Clinical impression, primary diagnosis, differential diagnoses, and clinical reasoning based on subjective and objective findings.",
                "plan": "Treatment plan including medications prescribed, diagnostic tests ordered, patient education provided, follow-up instructions, and any referrals mentioned."
            }}
        }}

        Guidelines for SOAP note generation:
        - Extract information accurately from the conversation
        - Use professional medical terminology
        - If information is not available for a section, note "Not documented" or "Not assessed" with specific reason
        - If transcript is too short, still provide the JSON structure with explanations of why sections cannot be completed
        - Ensure clinical accuracy and completeness
        - Focus on medically relevant information
        - IMPORTANT: Keep all text in single lines within JSON strings - use semicolons or bullet points instead of line breaks
        - Format lists as: "Item 1; Item 2; Item 3" rather than using actual line breaks
        """

        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Try to extract JSON from the response
        try:
            # First, try to parse the entire response as JSON
            try:
                analysis = json.loads(response_text.strip())
                print(f"Successfully parsed entire response as JSON")
                return analysis
            except json.JSONDecodeError:
                pass
            
            # If that fails, look for JSON block in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group().strip()
                print(f"Found JSON block, length: {len(json_text)}")
                
                # Try parsing without modifications first
                try:
                    analysis = json.loads(json_text)
                    print(f"Successfully parsed JSON without modifications")
                    return analysis
                except json.JSONDecodeError as e:
                    print(f"Initial JSON parse failed: {e}")
                
                # Try with character escaping
                try:
                    # More careful character replacement
                    cleaned_json = json_text
                    # Only escape unescaped newlines
                    cleaned_json = re.sub(r'(?<!\\)\n', '\\n', cleaned_json)
                    # Only escape unescaped tabs  
                    cleaned_json = re.sub(r'(?<!\\)\t', '\\t', cleaned_json)
                    # Remove other control characters
                    cleaned_json = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned_json)
                    
                    analysis = json.loads(cleaned_json)
                    print(f"Successfully parsed JSON after cleaning")
                    return analysis
                except json.JSONDecodeError as e:
                    print(f"Cleaned JSON parse failed: {e}")
                
                # Last resort: try to fix common JSON issues
                try:
                    fixed_json = json_text
                    # Remove trailing commas
                    fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
                    # Fix unescaped quotes in strings (basic attempt)
                    fixed_json = re.sub(r'(?<!\\)"(?![,}\]\s])', '\\"', fixed_json)
                    # Remove all problematic characters
                    fixed_json = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', fixed_json)
                    
                    analysis = json.loads(fixed_json)
                    print(f"Successfully parsed JSON after fixing")
                    return analysis
                except Exception as e:
                    print(f"Final JSON fix attempt failed: {e}")
                    
                # If all parsing attempts fail, return the raw JSON for inspection
                return {
                    "error": "Could not parse JSON response",
                    "raw_response": response_text,
                    "extracted_json": json_text,
                    "parse_error": str(e)
                }
            else:
                # No JSON found in response
                return {
                    "error": "No JSON found in response",
                    "raw_response": response_text
                }
                
        except Exception as e:
            print(f"Unexpected error in JSON processing: {e}")
            return {
                "error": f"Analysis processing failed: {str(e)}",
                "raw_response": response_text
            }
            
    except Exception as e:
        print(f"Error analyzing conversation: {e}")
        return {
            "error": f"Analysis failed: {str(e)}"
        }

def analyze_conversation_with_sources(transcript_text):
    """Enhanced analysis that maps each SOAP component to its source transcript excerpts"""
    try:
        # Check if transcript is too small
        if len(transcript_text.strip()) < 10:
            return {
                "error": "Transcript too short for analysis",
                "reason": "The recorded conversation is too brief to generate a meaningful medical analysis.",
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
        
        # Split transcript into numbered segments for easier reference
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
        
        prompt = f"""
        You are a medical AI assistant analyzing a doctor-patient conversation. Your task is to:
        1. Analyze speaker distribution and conversation flow
        2. Extract key medical topics and conversation segments  
        3. Generate a professional SOAP note with source citations
        4. For EACH statement in the SOAP note, identify the specific transcript segments that support it
        5. Provide confidence scores for each component

        TRANSCRIPT (with segment numbers for reference):
        {chr(10).join([f"[{seg['id']}] {seg['text']}" for seg in transcript_segments])}

        CRITICAL REQUIREMENTS for your response:
        - Include ALL analysis components: speaker analysis, medical topics, conversation segments, summary, AND SOAP note with sources
        - For every statement in the SOAP note, you MUST cite the specific segment numbers [1], [2], etc. that support it
        - If multiple segments support a statement, list all relevant segments
        - Provide confidence scores (0-100) for each SOAP section
        - Use professional medical language
        - If information is missing, explicitly state "Not documented" and cite supporting segments if available

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
                }},
                {{
                    "type": "chief_complaint",
                    "content": "I have chest pain",
                    "speaker": "patient"
                }}
            ],
            "medical_topics": ["symptom1", "symptom2", "diagnosis"],
            "summary": "Brief summary of the consultation",
            "soap_note_with_sources": {{
                "subjective": {{
                    "content": "Patient reports chest pain that started 2 hours ago, described as sharp and radiating to left arm",
                    "sources": [
                        {{
                            "segment_ids": [3, 5, 7],
                            "excerpt": "I have this sharp pain in my chest... started about 2 hours ago... goes down my left arm",
                            "reasoning": "Patient directly describing chief complaint and associated symptoms"
                        }}
                    ],
                    "confidence": 85,
                    "sub_components": {{
                        "chief_complaint": {{
                            "content": "Chest pain",
                            "sources": [{{
                                "segment_ids": [3],
                                "excerpt": "I have this sharp pain in my chest",
                                "reasoning": "Direct patient statement of primary concern"
                            }}],
                            "confidence": 95
                        }},
                        "history_present_illness": {{
                            "content": "Sharp chest pain started 2 hours ago, radiating to left arm",
                            "sources": [{{
                                "segment_ids": [3, 5, 7],
                                "excerpt": "sharp pain... started about 2 hours ago... goes down my left arm",
                                "reasoning": "Patient describing timeline and characteristics"
                            }}],
                            "confidence": 90
                        }}
                    }}
                }},
                "objective": {{
                    "content": "Vital signs: BP 140/90, HR 88, temp 98.6F. Physical exam reveals tenderness over precordium",
                    "sources": [
                        {{
                            "segment_ids": [12, 15],
                            "excerpt": "blood pressure is 140 over 90... heart rate 88... temperature normal... tender right here over the heart",
                            "reasoning": "Doctor documenting vital signs and physical findings"
                        }}
                    ],
                    "confidence": 80,
                    "sub_components": {{
                        "vital_signs": {{
                            "content": "BP 140/90, HR 88, temp 98.6F",
                            "sources": [{{
                                "segment_ids": [12],
                                "excerpt": "blood pressure is 140 over 90, heart rate 88, temperature normal",
                                "reasoning": "Doctor stating measured vital signs"
                            }}],
                            "confidence": 95
                        }},
                        "physical_exam": {{
                            "content": "Tenderness over precordium",
                            "sources": [{{
                                "segment_ids": [15],
                                "excerpt": "tender right here over the heart",
                                "reasoning": "Doctor documenting physical examination findings"
                            }}],
                            "confidence": 85
                        }}
                    }}
                }},
                "assessment": {{
                    "content": "Likely acute coronary syndrome based on chest pain characteristics and risk factors",
                    "sources": [
                        {{
                            "segment_ids": [18, 20],
                            "excerpt": "given your symptoms and the nature of this pain... could be related to your heart",
                            "reasoning": "Doctor's clinical reasoning and diagnostic thinking"
                        }}
                    ],
                    "confidence": 75,
                    "sub_components": {{
                        "primary_diagnosis": {{
                            "content": "Acute coronary syndrome",
                            "sources": [{{
                                "segment_ids": [20],
                                "excerpt": "could be related to your heart",
                                "reasoning": "Doctor indicating cardiac etiology"
                            }}],
                            "confidence": 70
                        }}
                    }}
                }},
                "plan": {{
                    "content": "EKG and cardiac enzymes ordered; aspirin 325mg given; cardiology consultation; follow-up in 24 hours",
                    "sources": [
                        {{
                            "segment_ids": [22, 24, 26],
                            "excerpt": "let's get an EKG... check some blood work... give you some aspirin... see cardiology... come back tomorrow",
                            "reasoning": "Doctor outlining specific treatment and follow-up plans"
                        }}
                    ],
                    "confidence": 90,
                    "sub_components": {{
                        "diagnostic_tests": {{
                            "content": "EKG and cardiac enzymes ordered",
                            "sources": [{{
                                "segment_ids": [22, 24],
                                "excerpt": "let's get an EKG... check some blood work",
                                "reasoning": "Doctor ordering specific diagnostic tests"
                            }}],
                            "confidence": 95
                        }},
                        "medications": {{
                            "content": "Aspirin 325mg given",
                            "sources": [{{
                                "segment_ids": [24],
                                "excerpt": "give you some aspirin",
                                "reasoning": "Doctor prescribing/administering medication"
                            }}],
                            "confidence": 85
                        }},
                        "follow_up": {{
                            "content": "Cardiology consultation; follow-up in 24 hours",
                            "sources": [{{
                                "segment_ids": [26],
                                "excerpt": "see cardiology... come back tomorrow",
                                "reasoning": "Doctor arranging specialist consultation and follow-up"
                            }}],
                            "confidence": 90
                        }}
                    }}
                }}
            }},
            "transcript_segments": {json.dumps(transcript_segments)},
            "analysis_metadata": {{
                "total_segments": {len(transcript_segments)},
                "processing_timestamp": "{json.dumps(transcript_segments)}",
                "overall_confidence": 85
            }}
        }}

        IMPORTANT: 
        - Every "content" field must have corresponding "sources" with specific segment_ids
        - Segment_ids must reference the numbered segments from the transcript above
        - Excerpts should be direct quotes (may be abbreviated with ...)
        - Reasoning should explain why these segments support the clinical statement
        - If no supporting evidence exists, use "Not documented" and empty sources array
        - Confidence scores should reflect the strength of evidence in the transcript
        """

        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2500,  # Increased for detailed source mapping
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        response_text = message.content[0].text
        
        # Parse the enhanced response with source mapping
        try:
            # Try to parse as JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group().strip()
                
                # Clean the JSON
                cleaned_json = json_text
                cleaned_json = re.sub(r'(?<!\\)\n', '\\n', cleaned_json)
                cleaned_json = re.sub(r'(?<!\\)\t', '\\t', cleaned_json)
                cleaned_json = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', cleaned_json)
                
                analysis = json.loads(cleaned_json)
                
                # Add the original transcript segments for reference
                analysis['transcript_segments'] = transcript_segments
                
                print(f"Successfully parsed enhanced analysis with sources")
                return analysis
                
        except Exception as e:
            print(f"Error parsing enhanced analysis: {e}")
            # Fallback to original analysis and convert to enhanced format
            original_analysis = analyze_conversation(transcript_text)
            return convert_to_enhanced_format(original_analysis, transcript_segments)
            
    except Exception as e:
        print(f"Error in enhanced analysis: {e}")
        # Fallback to original analysis and convert to enhanced format
        original_analysis = analyze_conversation(transcript_text)
        return convert_to_enhanced_format(original_analysis, transcript_segments)

def convert_to_enhanced_format(original_analysis, transcript_segments):
    """Convert original analysis format to enhanced format with source mapping"""
    if "error" in original_analysis:
        return original_analysis
    
    # Convert standard SOAP note to enhanced format
    enhanced_soap = {}
    if "soap_note" in original_analysis:
        for section_key, content in original_analysis["soap_note"].items():
            enhanced_soap[section_key] = {
                "content": content,
                "sources": [],  # No sources available from original analysis
                "confidence": 80  # Default confidence
            }
    
    # Return enhanced format with all components
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

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'message': 'Connected to server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    global deepgram_connection
    if deepgram_connection:
        try:
            deepgram_connection.finish()
        except:
            pass
        deepgram_connection = None

@socketio.on('start_transcription')
def handle_start_transcription():
    global deepgram_connection, current_session_id, full_transcript, conversation_analysis
    
    print('Starting transcription...')
    
    # Clean up previous session and reset everything
    if deepgram_connection:
        try:
            deepgram_connection.finish()
        except:
            pass
        deepgram_connection = None
    
    # Reset transcript and analysis for new session
    full_transcript = ""
    conversation_analysis = None
    
    # Generate new session ID
    import uuid
    current_session_id = str(uuid.uuid4())
    
    # Clear frontend display
    emit('clear_session')
    
    try:
        # Initialize Deepgram client
        config = DeepgramClientOptions(options={"keepalive": "true"})
        deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
        
        # Create connection
        deepgram_connection = deepgram.listen.live.v("1")
        
        # Configure live transcription options (optimized for medical accuracy)
        options = LiveOptions(
            model="nova-2",  # Best model for medical terminology
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="2000",  # Longer for medical conversations (more thoughtful speech)
            vad_events=True,
            punctuate=True,
            profanity_filter=False,  # Important for medical terms that might be flagged
            redact=False,  # Don't redact medical information
            diarize=True,  # Enable speaker separation for doctor/patient identification
            numerals=True,  # Important for medical measurements, dosages
            endpointing=800,  # More patient for medical terminology and pauses
            filler_words=False,  # Remove "um", "uh" for cleaner medical notes
            multichannel=False,
            keywords=["patient", "doctor", "symptoms", "diagnosis", "treatment", "medication", "prescription", "mg", "ml", "blood pressure", "temperature", "pain", "history", "allergies", "surgery", "chronic", "acute"]  # Medical keywords boost
        )
        
        # Event handlers
        def on_message(self, result, **kwargs):
            global full_transcript
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            
            # Extract speaker information if available (from diarization)
            speaker = None
            confidence = result.channel.alternatives[0].confidence if hasattr(result.channel.alternatives[0], 'confidence') else None
            
            # Check for speaker metadata in diarization
            if hasattr(result.channel, 'diarize') and result.channel.diarize:
                speaker = f"Speaker {result.channel.diarize.speaker}" if hasattr(result.channel.diarize, 'speaker') else None
            
            if result.is_final:
                # Enhanced transcript formatting with timestamps and speaker info
                timestamp = result.channel.alternatives[0].words[0].start if hasattr(result.channel.alternatives[0], 'words') and result.channel.alternatives[0].words else None
                
                # Add to full transcript with enhanced formatting
                if speaker:
                    full_transcript += f"[{speaker}] {sentence} "
                else:
                    full_transcript += f"{sentence} "
                
                # Send enhanced final transcript
                socketio.emit('transcript', {
                    'text': sentence,
                    'is_final': True,
                    'speaker': speaker,
                    'confidence': confidence,
                    'timestamp': timestamp
                })
                
                # Log for debugging
                print(f"Final transcript: {sentence[:50]}... (Speaker: {speaker}, Confidence: {confidence})")
            else:
                # Send interim transcript with current processing info
                socketio.emit('transcript', {
                    'text': sentence,
                    'is_final': False,
                    'speaker': speaker,
                    'confidence': confidence
                })
        
        def on_metadata(self, metadata, **kwargs):
            print(f"Metadata: {metadata}")
        
        def on_speech_started(self, speech_started, **kwargs):
            print("Speech started")
        
        def on_utterance_end(self, utterance_end, **kwargs):
            print("Utterance ended")
        
        def on_close(self, close, **kwargs):
            print("Connection closed")
        
        def on_error(self, error, **kwargs):
            print(f"Error: {error}")
            socketio.emit('error', {'message': str(error)})
        
        def on_unhandled(self, unhandled, **kwargs):
            print(f"Unhandled: {unhandled}")
        
        # Register event handlers
        deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        deepgram_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        deepgram_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        deepgram_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        deepgram_connection.on(LiveTranscriptionEvents.Close, on_close)
        deepgram_connection.on(LiveTranscriptionEvents.Error, on_error)
        deepgram_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)
        
        # Start the connection
        if deepgram_connection.start(options) is False:
            print("Failed to connect to Deepgram")
            emit('error', {'message': 'Failed to connect to Deepgram'})
            return
        
        emit('status', {'message': 'Transcription started'})
        print('Deepgram connection established')
        
    except Exception as e:
        print(f"Error starting transcription: {e}")
        emit('error', {'message': f'Error starting transcription: {str(e)}'})

@socketio.on('audio_data')
def handle_audio_data(data):
    global deepgram_connection
    
    if deepgram_connection:
        try:
            # Decode base64 audio data
            audio_data = base64.b64decode(data['audio'])
            
            # Send audio data to Deepgram with error handling
            if len(audio_data) > 0:  # Only send if we have data
                deepgram_connection.send(audio_data)
            
        except Exception as e:
            print(f"Error processing audio data: {e}")
            # Don't emit error for every audio chunk issue, just log it
            # emit('error', {'message': f'Error processing audio: {str(e)}'})

@socketio.on('stop_transcription')
def handle_stop_transcription():
    global deepgram_connection, full_transcript, conversation_analysis
    
    print('Stopping transcription...')
    
    if deepgram_connection:
        try:
            deepgram_connection.finish()
        except Exception as e:
            print(f"Error stopping transcription: {e}")
        deepgram_connection = None
    
    emit('status', {'message': 'Transcription stopped'})
    
    # Analyze the conversation if we have transcript
    if full_transcript.strip():
        emit('status', {'message': 'Analyzing conversation with Claude...'})
        print(f"Analyzing transcript: {full_transcript[:100]}...")
        
        try:
            analysis = analyze_conversation_with_sources(full_transcript)
            conversation_analysis = analysis
            
            # Send analysis to frontend
            emit('conversation_analysis', analysis)
            emit('status', {'message': 'Analysis complete!'})
            
            # Disconnect the webhook after analysis is complete
            if deepgram_connection:
                try:
                    deepgram_connection.finish()
                except:
                    pass
                deepgram_connection = None
                print('Deepgram connection disconnected after analysis')
            
        except Exception as e:
            print(f"Error in analysis: {e}")
            emit('error', {'message': f'Analysis failed: {str(e)}'})
    else:
        # Send minimal analysis for empty transcript
        empty_analysis = {
            "error": "No transcript available",
            "reason": "No speech was detected or transcribed during the recording session",
            "speaker_analysis": {
                "doctor_segments": [],
                "patient_segments": [],
                "doctor_percentage": 0,
                "patient_percentage": 0
            },
            "conversation_segments": [],
            "medical_topics": [],
            "summary": "No conversation recorded",
            "soap_note": {
                "subjective": "No patient information captured - no speech detected",
                "objective": "Not documented - no conversation recorded",
                "assessment": "Cannot assess - no clinical conversation available", 
                "plan": "Unable to create plan - please record a conversation"
            }
        }
        emit('conversation_analysis', empty_analysis)
        emit('status', {'message': 'No transcript to analyze'})

@socketio.on('retry_analysis')
def handle_retry_analysis():
    global full_transcript, conversation_analysis
    
    print('Retrying analysis...')
    
    # Analyze the conversation if we have transcript
    if full_transcript.strip():
        emit('status', {'message': 'Retrying analysis with Claude...'})
        print(f"Retrying analysis for transcript: {full_transcript[:100]}...")
        
        try:
            analysis = analyze_conversation_with_sources(full_transcript)
            conversation_analysis = analysis
            
            # Send analysis to frontend
            emit('conversation_analysis', analysis)
            emit('status', {'message': 'Analysis complete!'})
            
            # Disconnect the webhook after analysis is complete
            if deepgram_connection:
                try:
                    deepgram_connection.finish()
                except:
                    pass
                deepgram_connection = None
                print('Deepgram connection disconnected after retry analysis')
            
        except Exception as e:
            print(f"Error in retry analysis: {e}")
            emit('error', {'message': f'Retry analysis failed: {str(e)}'})
    else:
        emit('status', {'message': 'No transcript available to analyze'})

@socketio.on('test_analysis')
def handle_test_analysis():
    """Test function with enhanced source mapping"""
    print('Testing analysis with sample data including source mapping...')
    
    # Create a sample analysis with source mapping to test the frontend
    test_analysis = {
        "speaker_analysis": {
            "doctor_segments": ["How can I help you today?", "I'll prescribe some medication"],
            "patient_segments": ["I have a headache for 3 days", "Thank you doctor"],
            "doctor_percentage": 60,
            "patient_percentage": 40
        },
        "conversation_segments": [
            {
                "type": "greeting",
                "content": "How can I help you today?",
                "speaker": "doctor"
            },
            {
                "type": "chief_complaint",
                "content": "I have a headache for 3 days",
                "speaker": "patient"
            }
        ],
        "medical_topics": ["headache", "pain management", "tension headache"],
        "summary": "Patient presents with 3-day history of headache. Doctor provides treatment recommendation.",
        "transcript_segments": [
            {"id": 1, "text": "How can I help you today?", "start_pos": 0, "end_pos": 26},
            {"id": 2, "text": "I have a headache for 3 days now.", "start_pos": 27, "end_pos": 61},
            {"id": 3, "text": "It's a throbbing pain on the right side.", "start_pos": 62, "end_pos": 103},
            {"id": 4, "text": "Let me check your blood pressure.", "start_pos": 104, "end_pos": 138},
            {"id": 5, "text": "Your blood pressure is normal at 120/80.", "start_pos": 139, "end_pos": 180},
            {"id": 6, "text": "This sounds like a tension headache.", "start_pos": 181, "end_pos": 218},
            {"id": 7, "text": "I'll prescribe some ibuprofen and recommend rest.", "start_pos": 219, "end_pos": 269}
        ],
        "soap_note_with_sources": {
            "subjective": {
                "content": "Patient reports 3-day history of headache with throbbing pain on the right side.",
                "confidence": 95,
                "sources": [
                    {
                        "segment_ids": [2, 3],
                        "excerpt": "I have a headache for 3 days now. It's a throbbing pain on the right side.",
                        "reasoning": "Patient directly describing chief complaint with specific duration and characteristics"
                    }
                ],
                "sub_components": {
                    "chief_complaint": {
                        "content": "Headache",
                        "confidence": 100,
                        "sources": [
                            {
                                "segment_ids": [2],
                                "excerpt": "I have a headache for 3 days now",
                                "reasoning": "Patient's primary concern stated directly"
                            }
                        ]
                    },
                    "history_present_illness": {
                        "content": "3-day duration, throbbing quality, right-sided location",
                        "confidence": 90,
                        "sources": [
                            {
                                "segment_ids": [2, 3],
                                "excerpt": "for 3 days now... throbbing pain on the right side",
                                "reasoning": "Patient describing temporal and qualitative characteristics"
                            }
                        ]
                    }
                }
            },
            "objective": {
                "content": "Vital signs: Blood pressure 120/80 mmHg (normal). No other physical examination findings documented.",
                "confidence": 80,
                "sources": [
                    {
                        "segment_ids": [5],
                        "excerpt": "Your blood pressure is normal at 120/80",
                        "reasoning": "Doctor documenting vital signs measurement"
                    }
                ],
                "sub_components": {
                    "vital_signs": {
                        "content": "BP 120/80 mmHg",
                        "confidence": 95,
                        "sources": [
                            {
                                "segment_ids": [5],
                                "excerpt": "Your blood pressure is normal at 120/80",
                                "reasoning": "Doctor stating measured blood pressure"
                            }
                        ]
                    }
                }
            },
            "assessment": {
                "content": "Tension headache based on clinical presentation and symptom characteristics.",
                "confidence": 85,
                "sources": [
                    {
                        "segment_ids": [6],
                        "excerpt": "This sounds like a tension headache",
                        "reasoning": "Doctor's clinical assessment and diagnostic impression"
                    }
                ],
                "sub_components": {
                    "primary_diagnosis": {
                        "content": "Tension headache",
                        "confidence": 85,
                        "sources": [
                            {
                                "segment_ids": [6],
                                "excerpt": "This sounds like a tension headache",
                                "reasoning": "Doctor's diagnostic conclusion"
                            }
                        ]
                    }
                }
            },
            "plan": {
                "content": "Prescribe ibuprofen for pain relief and recommend rest for recovery.",
                "confidence": 90,
                "sources": [
                    {
                        "segment_ids": [7],
                        "excerpt": "I'll prescribe some ibuprofen and recommend rest",
                        "reasoning": "Doctor outlining treatment plan including medication and non-pharmacological management"
                    }
                ],
                "sub_components": {
                    "medications": {
                        "content": "Ibuprofen as needed for pain",
                        "confidence": 95,
                        "sources": [
                            {
                                "segment_ids": [7],
                                "excerpt": "I'll prescribe some ibuprofen",
                                "reasoning": "Doctor prescribing specific medication"
                            }
                        ]
                    },
                    "recommendations": {
                        "content": "Rest and relaxation",
                        "confidence": 85,
                        "sources": [
                            {
                                "segment_ids": [7],
                                "excerpt": "recommend rest",
                                "reasoning": "Doctor's non-pharmacological treatment recommendation"
                            }
                        ]
                    }
                }
            }
        },
        "analysis_metadata": {
            "total_segments": 7,
            "overall_confidence": 88
        }
    }
    
    emit('conversation_analysis', test_analysis)
    emit('status', {'message': 'Test analysis with source mapping complete!'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True) 