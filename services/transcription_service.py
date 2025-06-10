import base64
from typing import Optional, Callable, Any
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents
from deepgram.clients.live.v1 import LiveOptions
from config import DEEPGRAM_API_KEY


class TranscriptionService:
    """Service class for handling live transcription using Deepgram"""
    
    def __init__(self):
        """Initialize the transcription service"""
        self.deepgram_connection = None
        self.current_session_id = None
        self.full_transcript = ""
        
    def start_transcription(self, 
                          on_transcript: Callable[[dict], None],
                          on_error: Callable[[str], None],
                          on_status: Callable[[str], None]) -> bool:
        """Start live transcription session"""
        try:
            # Clean up previous session
            self.stop_transcription()
            
            # Reset transcript for new session
            self.full_transcript = ""
            
            # Generate new session ID
            import uuid
            self.current_session_id = str(uuid.uuid4())
            
            # Initialize Deepgram client
            config = DeepgramClientOptions(options={"keepalive": "true"})
            deepgram = DeepgramClient(DEEPGRAM_API_KEY, config)
            
            # Create connection
            self.deepgram_connection = deepgram.listen.live.v("1")
            
            # Configure live transcription options (optimized for medical accuracy)
            options = LiveOptions(
                model="nova-2",  # Best model for medical terminology
                language="en-US",
                smart_format=True,
                encoding="linear16",
                channels=1,
                sample_rate=16000,
                interim_results=True,
                utterance_end_ms="2000",  # Longer for medical conversations
                vad_events=True,
                punctuate=True,
                profanity_filter=False,  # Important for medical terms
                redact=False,  # Don't redact medical information
                diarize=True,  # Enable speaker separation
                numerals=True,  # Important for medical measurements
                endpointing=800,  # More patient for medical terminology
                filler_words=False,  # Remove "um", "uh" for cleaner notes
                multichannel=False,
                keywords=[
                    "patient", "doctor", "symptoms", "diagnosis", "treatment", 
                    "medication", "prescription", "mg", "ml", "blood pressure", 
                    "temperature", "pain", "history", "allergies", "surgery", 
                    "chronic", "acute"
                ]  # Medical keywords boost
            )
            
            # Set up event handlers
            self._setup_event_handlers(on_transcript, on_error, on_status)
            
            # Start the connection
            if self.deepgram_connection.start(options) is False:
                on_error("Failed to connect to Deepgram")
                return False
            
            on_status("Transcription started")
            print('Deepgram connection established')
            return True
            
        except Exception as e:
            print(f"Error starting transcription: {e}")
            on_error(f"Error starting transcription: {str(e)}")
            return False
    
    def stop_transcription(self) -> None:
        """Stop the current transcription session"""
        if self.deepgram_connection:
            try:
                self.deepgram_connection.finish()
            except Exception as e:
                print(f"Error stopping transcription: {e}")
            finally:
                self.deepgram_connection = None
    
    def send_audio_data(self, audio_data: str) -> bool:
        """Send audio data to Deepgram for transcription"""
        if not self.deepgram_connection:
            return False
            
        try:
            # Decode base64 audio data
            decoded_audio = base64.b64decode(audio_data)
            
            # Send audio data to Deepgram if we have data
            if len(decoded_audio) > 0:
                self.deepgram_connection.send(decoded_audio)
                return True
            return False
            
        except Exception as e:
            print(f"Error processing audio data: {e}")
            return False
    
    def get_full_transcript(self) -> str:
        """Get the full transcript from the current session"""
        return self.full_transcript
    
    def get_session_id(self) -> Optional[str]:
        """Get the current session ID"""
        return self.current_session_id
    
    def _setup_event_handlers(self, 
                            on_transcript: Callable[[dict], None],
                            on_error: Callable[[str], None],
                            on_status: Callable[[str], None]) -> None:
        """Set up Deepgram event handlers"""
        
        # Capture the service instance in the closure to avoid confusion with Deepgram's self
        service_instance = self
        
        def on_message(dg_self, result, **kwargs):
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
                    service_instance.full_transcript += f"[{speaker}] {sentence} "
                else:
                    service_instance.full_transcript += f"{sentence} "
                
                # Send enhanced final transcript
                on_transcript({
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
                on_transcript({
                    'text': sentence,
                    'is_final': False,
                    'speaker': speaker,
                    'confidence': confidence
                })
        
        def on_metadata(dg_self, metadata, **kwargs):
            print(f"Metadata: {metadata}")
        
        def on_speech_started(dg_self, speech_started, **kwargs):
            print("Speech started")
        
        def on_utterance_end(dg_self, utterance_end, **kwargs):
            print("Utterance ended")
        
        def on_close(dg_self, close, **kwargs):
            print("Connection closed")
        
        def on_error_handler(dg_self, error, **kwargs):
            print(f"Error: {error}")
            on_error(str(error))
        
        def on_unhandled(dg_self, unhandled, **kwargs):
            print(f"Unhandled: {unhandled}")
        
        # Register event handlers
        self.deepgram_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        self.deepgram_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        self.deepgram_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        self.deepgram_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        self.deepgram_connection.on(LiveTranscriptionEvents.Close, on_close)
        self.deepgram_connection.on(LiveTranscriptionEvents.Error, on_error_handler)
        self.deepgram_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled) 