import base64
import uuid
import time
from typing import Optional, Callable, Any, Dict
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents
from deepgram.clients.live.v1 import LiveOptions
from config import config
from ..utils.logging_config import LoggingMixin, log_performance
from ..utils.exceptions import (
    DeepgramConnectionError, AudioProcessingError, TranscriptionTimeoutError,
    ErrorHandler
)


class TranscriptionService(LoggingMixin):
    """Service class for handling live transcription using Deepgram"""
    
    def __init__(self):
        """Initialize the transcription service"""
        self.deepgram_connection = None
        self.current_session_id = None
        self.full_transcript = ""
        self.session_start_time = None
        self.connection_retries = 0
        self.max_retries = 3
        self.is_connected = False
        self.audio_chunks_processed = 0
        
        # Validate API key on initialization
        if not config.api.deepgram_api_key or config.api.deepgram_api_key == 'REPLACE_WITH_YOUR_DEEPGRAM_API_KEY_HERE':
            raise DeepgramConnectionError("Deepgram API key not configured")
        
    @log_performance
    def start_transcription(self, 
                          on_transcript: Callable[[dict], None],
                          on_error: Callable[[str], None],
                          on_status: Callable[[str], None]) -> bool:
        """Start live transcription session with enhanced error handling"""
        try:
            self.log_operation("start_transcription")
            
            # Clean up previous session
            self.stop_transcription()
            
            # Reset session state
            self.full_transcript = ""
            self.current_session_id = str(uuid.uuid4())
            self.session_start_time = time.time()
            self.connection_retries = 0
            self.audio_chunks_processed = 0
            
            # Initialize Deepgram client with enhanced configuration
            client_config = DeepgramClientOptions(
                options={
                    "keepalive": "true",
                    "timeout": config.ai.timeout_seconds
                }
            )
            deepgram = DeepgramClient(config.api.deepgram_api_key, client_config)
            
            # Create connection
            self.deepgram_connection = deepgram.listen.live.v("1")
            
            # Configure live transcription options (optimized for medical accuracy)
            options = LiveOptions(
                model=config.transcription.model,
                language=config.transcription.language,
                smart_format=config.transcription.enable_smart_format,
                encoding=config.transcription.encoding,
                channels=1,
                sample_rate=config.transcription.sample_rate,
                interim_results=True,
                utterance_end_ms=config.transcription.utterance_end_ms,
                vad_events=True,
                punctuate=config.transcription.enable_punctuation,
                profanity_filter=config.transcription.profanity_filter,
                redact=config.transcription.redact_pii,
                diarize=config.transcription.enable_diarization,
                numerals=config.transcription.enable_numerals,
                endpointing=config.transcription.endpointing,
                filler_words=False,
                multichannel=False,
                keywords=config.transcription.medical_keywords
            )
            
            # Set up event handlers
            self._setup_event_handlers(on_transcript, on_error, on_status)
            
            # Start the connection with retry logic
            if not self._start_connection_with_retry(options, on_error):
                return False
            
            self.is_connected = True
            on_status("Transcription started successfully")
            self.logger.info(f"Transcription session started: {self.current_session_id}")
            return True
            
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "transcription")
            self.log_error(error, "start_transcription")
            on_error(f"Failed to start transcription: {error.message}")
            return False
    
    def _start_connection_with_retry(self, options, on_error) -> bool:
        """Start connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if self.deepgram_connection.start(options) is not False:
                    return True
                
                self.connection_retries += 1
                if attempt < self.max_retries - 1:
                    self.logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                    time.sleep(1 * (attempt + 1))  # Exponential backoff
                
            except Exception as e:
                self.logger.error(f"Connection attempt {attempt + 1} error: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))
        
        on_error("Failed to establish Deepgram connection after multiple attempts")
        return False
    
    def stop_transcription(self) -> None:
        """Stop the current transcription session with proper cleanup"""
        if self.deepgram_connection:
            try:
                self.logger.info(f"Stopping transcription session: {self.current_session_id}")
                self.deepgram_connection.finish()
                
                # Log session statistics
                if self.session_start_time:
                    session_duration = time.time() - self.session_start_time
                    self.logger.info(
                        f"Session completed - Duration: {session_duration:.2f}s, "
                        f"Audio chunks: {self.audio_chunks_processed}, "
                        f"Transcript length: {len(self.full_transcript)}"
                    )
                
            except Exception as e:
                error = ErrorHandler.handle_service_error(e, "transcription_stop")
                self.log_error(error, "stop_transcription")
            finally:
                self.deepgram_connection = None
                self.is_connected = False
    
    def send_audio_data(self, audio_data: str) -> bool:
        """Send audio data to Deepgram for transcription with validation"""
        if not self.deepgram_connection or not self.is_connected:
            self.logger.warning("Attempted to send audio data without active connection")
            return False
            
        try:
            # Validate audio data
            if not audio_data or not isinstance(audio_data, str):
                raise AudioProcessingError("Invalid audio data format")
            
            # Decode base64 audio data
            decoded_audio = base64.b64decode(audio_data)
            
            # Validate decoded audio
            if len(decoded_audio) == 0:
                self.logger.debug("Received empty audio chunk, skipping")
                return False
            
            # Send audio data to Deepgram
            self.deepgram_connection.send(decoded_audio)
            self.audio_chunks_processed += 1
            
            # Log progress periodically
            if self.audio_chunks_processed % 100 == 0:
                self.logger.debug(f"Processed {self.audio_chunks_processed} audio chunks")
            
            return True
            
        except base64.binascii.Error as e:
            error = AudioProcessingError(f"Base64 decoding failed: {str(e)}")
            self.log_error(error, "send_audio_data")
            return False
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "audio_processing")
            self.log_error(error, "send_audio_data")
            return False
    
    def get_full_transcript(self) -> str:
        """Get the full transcript from the current session"""
        return self.full_transcript
    
    def get_session_id(self) -> Optional[str]:
        """Get the current session ID"""
        return self.current_session_id
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for the current session"""
        stats = {
            'session_id': self.current_session_id,
            'is_connected': self.is_connected,
            'audio_chunks_processed': self.audio_chunks_processed,
            'transcript_length': len(self.full_transcript),
            'connection_retries': self.connection_retries
        }
        
        if self.session_start_time:
            stats['session_duration'] = time.time() - self.session_start_time
        
        return stats
    
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