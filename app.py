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
        
        # Configure live transcription options (optimized for accuracy)
        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1200",  # Balanced for accuracy and speed
            vad_events=True,
            punctuate=True,
            profanity_filter=False,
            redact=False,
            diarize=False,
            numerals=True,
            endpointing=500,  # More patient for slow speech
            filler_words=True,  # Include filler words for better context
            multichannel=False
        )
        
        # Event handlers
        def on_message(self, result, **kwargs):
            global full_transcript
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            
            if result.is_final:
                # Add to full transcript
                full_transcript += sentence + " "
                
                # Send final transcript
                socketio.emit('transcript', {
                    'text': sentence,
                    'is_final': True
                })
            else:
                # Send interim transcript
                socketio.emit('transcript', {
                    'text': sentence,
                    'is_final': False
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
            analysis = analyze_conversation(full_transcript)
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
            analysis = analyze_conversation(full_transcript)
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
    """Test function with known good JSON"""
    print('Testing analysis with sample data...')
    
    # Create a sample analysis to test the frontend
    test_analysis = {
        "speaker_analysis": {
            "doctor_segments": ["How can I help you today?", "I'll prescribe some medication"],
            "patient_segments": ["I have a headache", "Thank you doctor"],
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
                "content": "I have a headache",
                "speaker": "patient"
            }
        ],
        "medical_topics": ["headache", "pain management"],
        "summary": "Patient presents with headache complaint. Doctor provides treatment recommendation.",
        "soap_note": {
            "subjective": "Patient reports headache symptoms.",
            "objective": "No physical examination documented.",
            "assessment": "Tension headache likely.",
            "plan": "Prescribe pain medication and recommend rest."
        }
    }
    
    emit('conversation_analysis', test_analysis)
    emit('status', {'message': 'Test analysis complete!'})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True) 