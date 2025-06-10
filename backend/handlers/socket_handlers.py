from flask_socketio import emit
from ..services.transcription_service import TranscriptionService
from ..services.conversation_analyzer import ConversationAnalyzer
from ..utils.logging_config import LoggingMixin, log_performance
from ..utils.exceptions import (
    BaseHealthcareException, ErrorHandler, ClientConnectionError,
    DataTransmissionError
)
from ..utils.cache import session_cache, analysis_cache
import time


class SocketHandlers(LoggingMixin):
    """Class to handle all SocketIO events with enhanced error handling"""
    
    def __init__(self, socketio=None):
        """Initialize socket handlers with services"""
        try:
            self.transcription_service = TranscriptionService()
            self.conversation_analyzer = ConversationAnalyzer()
            self.conversation_analysis = None
            self.socketio = socketio
            self.session_start_time = None
            self.current_session_id = None
            self.logger.info("Socket handlers initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize socket handlers: {e}", exc_info=True)
            raise
    
    def handle_connect(self, *args, **kwargs):
        """Handle client connection with session management"""
        try:
            self.current_session_id = self.transcription_service.get_session_id()
            self.session_start_time = time.time()
            
            self.logger.info(f"Client connected - Session: {self.current_session_id}")
            emit('status', {
                'message': 'Connected to server',
                'session_id': self.current_session_id,
                'timestamp': self.session_start_time
            })
            
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "socket_connection")
            self.log_error(error, "handle_connect")
            emit('error', {'message': 'Connection initialization failed'})
    
    def handle_disconnect(self, *args, **kwargs):
        """Handle client disconnection with cleanup"""
        try:
            session_duration = time.time() - self.session_start_time if self.session_start_time else 0
            
            self.logger.info(f"Client disconnected - Session: {self.current_session_id}, Duration: {session_duration:.2f}s")
            
            # Stop transcription and cleanup
            self.transcription_service.stop_transcription()
            
            # Clear session cache if we have a session ID
            if self.current_session_id:
                session_cache.clear_session(self.current_session_id)
                
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "socket_disconnection")
            self.log_error(error, "handle_disconnect")
    
    @log_performance
    def handle_start_transcription(self, *args, **kwargs):
        """Handle start transcription request with enhanced error handling"""
        try:
            self.log_operation("start_transcription", session_id=self.current_session_id)
            
            # Clear frontend display
            emit('clear_session')
            
            # Define enhanced callback functions for transcription service
            def on_transcript(data):
                try:
                    # Add session context to transcript data
                    enhanced_data = {
                        **data,
                        'session_id': self.current_session_id,
                        'timestamp': time.time()
                    }
                    
                    if self.socketio:
                        self.socketio.emit('transcript', enhanced_data)
                    else:
                        emit('transcript', enhanced_data)
                        
                except Exception as e:
                    self.logger.error(f"Error emitting transcript: {e}")
            
            def on_error(message):
                try:
                    error_data = {
                        'message': message,
                        'session_id': self.current_session_id,
                        'timestamp': time.time(),
                        'type': 'transcription_error'
                    }
                    
                    if self.socketio:
                        self.socketio.emit('error', error_data)
                    else:
                        emit('error', error_data)
                        
                except Exception as e:
                    self.logger.error(f"Error emitting transcription error: {e}")
            
            def on_status(message):
                try:
                    status_data = {
                        'message': message,
                        'session_id': self.current_session_id,
                        'timestamp': time.time()
                    }
                    
                    if self.socketio:
                        self.socketio.emit('status', status_data)
                    else:
                        emit('status', status_data)
                        
                except Exception as e:
                    self.logger.error(f"Error emitting status: {e}")
            
            # Start transcription with enhanced callbacks
            success = self.transcription_service.start_transcription(
                on_transcript=on_transcript,
                on_error=on_error,
                on_status=on_status
            )
            
            if not success:
                emit('error', {
                    'message': 'Failed to start transcription',
                    'session_id': self.current_session_id,
                    'timestamp': time.time(),
                    'type': 'startup_error'
                })
            else:
                self.logger.info(f"Transcription started successfully for session: {self.current_session_id}")
                
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "start_transcription")
            self.log_error(error, "handle_start_transcription")
            emit('error', {
                'message': f'Failed to start transcription: {error.message}',
                'session_id': self.current_session_id,
                'timestamp': time.time(),
                'type': 'handler_error'
            })
    
    def handle_audio_data(self, data):
        """Handle incoming audio data with validation"""
        try:
            # Validate audio data structure
            if not isinstance(data, dict):
                raise DataTransmissionError("Invalid audio data format - expected dictionary")
            
            if 'audio' not in data:
                raise DataTransmissionError("Missing 'audio' field in data")
            
            # Send audio data to transcription service
            success = self.transcription_service.send_audio_data(data['audio'])
            
            if not success:
                self.logger.warning("Failed to process audio data chunk")
                
        except DataTransmissionError as e:
            self.log_error(e, "handle_audio_data")
            emit('error', {
                'message': f'Audio data error: {e.message}',
                'session_id': self.current_session_id,
                'timestamp': time.time(),
                'type': 'audio_data_error'
            })
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "audio_processing")
            self.log_error(error, "handle_audio_data")
            emit('error', {
                'message': 'Audio processing error',
                'session_id': self.current_session_id,
                'timestamp': time.time(),
                'type': 'audio_processing_error'
            })
    
    @log_performance
    def handle_stop_transcription(self, *args, **kwargs):
        """Handle stop transcription request with analysis"""
        try:
            self.log_operation("stop_transcription", session_id=self.current_session_id)
            
            # Stop transcription service
            self.transcription_service.stop_transcription()
            
            # Get session statistics
            session_stats = self.transcription_service.get_session_stats()
            
            emit('status', {
                'message': 'Transcription stopped',
                'session_id': self.current_session_id,
                'timestamp': time.time(),
                'stats': session_stats
            })
            
            # Get the full transcript
            full_transcript = self.transcription_service.get_full_transcript()
            
            # Analyze the conversation if we have transcript
            if full_transcript.strip():
                emit('status', {
                    'message': 'Analyzing conversation with Claude...',
                    'session_id': self.current_session_id,
                    'timestamp': time.time()
                })
                
                self.logger.info(f"Starting analysis for transcript length: {len(full_transcript)} chars")
                
                try:
                    analysis = self.conversation_analyzer.analyze_conversation_with_sources(full_transcript)
                    self.conversation_analysis = analysis
                    
                    # Add session context to analysis
                    enhanced_analysis = {
                        **analysis,
                        'session_id': self.current_session_id,
                        'analysis_timestamp': time.time(),
                        'transcript_stats': session_stats
                    }
                    
                    # Send analysis to frontend
                    if self.socketio:
                        self.socketio.emit('conversation_analysis', enhanced_analysis)
                        self.socketio.emit('status', {
                            'message': 'Analysis complete!',
                            'session_id': self.current_session_id,
                            'timestamp': time.time()
                        })
                    else:
                        emit('conversation_analysis', enhanced_analysis)
                        emit('status', {
                            'message': 'Analysis complete!',
                            'session_id': self.current_session_id,
                            'timestamp': time.time()
                        })
                    
                    self.logger.info('Analysis completed successfully')
                    
                except Exception as e:
                    error = ErrorHandler.handle_service_error(e, "conversation_analysis")
                    self.log_error(error, "handle_stop_transcription")
                    
                    error_data = {
                        'message': f'Analysis failed: {error.message}',
                        'session_id': self.current_session_id,
                        'timestamp': time.time(),
                        'type': 'analysis_error'
                    }
                    
                    if self.socketio:
                        self.socketio.emit('error', error_data)
                    else:
                        emit('error', error_data)
            else:
                # Send minimal analysis for empty transcript
                empty_analysis = self._create_empty_analysis()
                enhanced_empty_analysis = {
                    **empty_analysis,
                    'session_id': self.current_session_id,
                    'analysis_timestamp': time.time(),
                    'transcript_stats': session_stats
                }
                
                if self.socketio:
                    self.socketio.emit('conversation_analysis', enhanced_empty_analysis)
                    self.socketio.emit('status', {
                        'message': 'No transcript to analyze',
                        'session_id': self.current_session_id,
                        'timestamp': time.time()
                    })
                else:
                    emit('conversation_analysis', enhanced_empty_analysis)
                    emit('status', {
                        'message': 'No transcript to analyze',
                        'session_id': self.current_session_id,
                        'timestamp': time.time()
                    })
                    
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "stop_transcription")
            self.log_error(error, "handle_stop_transcription")
            emit('error', {
                'message': f'Error stopping transcription: {error.message}',
                'session_id': self.current_session_id,
                'timestamp': time.time(),
                'type': 'stop_error'
            })
    
    @log_performance
    def handle_retry_analysis(self, *args, **kwargs):
        """Handle retry analysis request with caching bypass"""
        try:
            self.log_operation("retry_analysis", session_id=self.current_session_id)
            
            # Get the full transcript
            full_transcript = self.transcription_service.get_full_transcript()
            
            # Analyze the conversation if we have transcript
            if full_transcript.strip():
                emit('status', {
                    'message': 'Retrying analysis with Claude...',
                    'session_id': self.current_session_id,
                    'timestamp': time.time()
                })
                
                self.logger.info(f"Retrying analysis for transcript length: {len(full_transcript)} chars")
                
                try:
                    # Clear cache for this transcript to force fresh analysis
                    analysis_cache.invalidate_transcript(full_transcript, "enhanced")
                    
                    analysis = self.conversation_analyzer.analyze_conversation_with_sources(full_transcript)
                    self.conversation_analysis = analysis
                    
                    # Add retry context to analysis
                    enhanced_analysis = {
                        **analysis,
                        'session_id': self.current_session_id,
                        'analysis_timestamp': time.time(),
                        'is_retry': True
                    }
                    
                    # Send analysis to frontend
                    if self.socketio:
                        self.socketio.emit('conversation_analysis', enhanced_analysis)
                        self.socketio.emit('status', {
                            'message': 'Retry analysis complete!',
                            'session_id': self.current_session_id,
                            'timestamp': time.time()
                        })
                    else:
                        emit('conversation_analysis', enhanced_analysis)
                        emit('status', {
                            'message': 'Retry analysis complete!',
                            'session_id': self.current_session_id,
                            'timestamp': time.time()
                        })
                    
                    self.logger.info('Retry analysis completed successfully')
                    
                except Exception as e:
                    error = ErrorHandler.handle_service_error(e, "retry_analysis")
                    self.log_error(error, "handle_retry_analysis")
                    
                    error_data = {
                        'message': f'Retry analysis failed: {error.message}',
                        'session_id': self.current_session_id,
                        'timestamp': time.time(),
                        'type': 'retry_analysis_error'
                    }
                    
                    if self.socketio:
                        self.socketio.emit('error', error_data)
                    else:
                        emit('error', error_data)
            else:
                status_data = {
                    'message': 'No transcript available to analyze',
                    'session_id': self.current_session_id,
                    'timestamp': time.time()
                }
                
                if self.socketio:
                    self.socketio.emit('status', status_data)
                else:
                    emit('status', status_data)
                    
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "retry_analysis")
            self.log_error(error, "handle_retry_analysis")
            emit('error', {
                'message': f'Error in retry analysis: {error.message}',
                'session_id': self.current_session_id,
                'timestamp': time.time(),
                'type': 'retry_handler_error'
            })
    
    def get_handler_stats(self):
        """Get comprehensive statistics for all handlers and services"""
        try:
            transcription_stats = self.transcription_service.get_session_stats()
            analyzer_stats = self.conversation_analyzer.get_analyzer_stats()
            
            return {
                'session_id': self.current_session_id,
                'session_start_time': self.session_start_time,
                'transcription': transcription_stats,
                'analyzer': analyzer_stats,
                'current_analysis_available': self.conversation_analysis is not None
            }
        except Exception as e:
            self.log_error(e, "get_handler_stats")
            return {'error': f'Stats unavailable: {str(e)}'}
    
    def cleanup_session(self):
        """Clean up session resources"""
        try:
            if self.current_session_id:
                session_cache.clear_session(self.current_session_id)
                self.logger.info(f"Cleaned up session: {self.current_session_id}")
            
            self.transcription_service.stop_transcription()
            self.conversation_analysis = None
            
        except Exception as e:
            self.log_error(e, "cleanup_session")

    def handle_test_analysis(self, *args, **kwargs):
        """Handle test analysis request with sample data"""
        try:
            self.log_operation("test_analysis", session_id=self.current_session_id)
            self.logger.info('Testing analysis with sample data including source mapping...')
            
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
                    ]
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
                    ]
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
                    ]
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
                    ]
                }
            },
            "analysis_metadata": {
                "total_segments": 7,
                "overall_confidence": 88
            }
        }
        
            # Add session context to test analysis
            enhanced_test_analysis = {
                **test_analysis,
                'session_id': self.current_session_id,
                'analysis_timestamp': time.time(),
                'is_test': True
            }
            
            if self.socketio:
                self.socketio.emit('conversation_analysis', enhanced_test_analysis)
                self.socketio.emit('status', {
                    'message': 'Test analysis with source mapping complete!',
                    'session_id': self.current_session_id,
                    'timestamp': time.time()
                })
            else:
                emit('conversation_analysis', enhanced_test_analysis)
                emit('status', {
                    'message': 'Test analysis with source mapping complete!',
                    'session_id': self.current_session_id,
                    'timestamp': time.time()
                })
                
            self.logger.info('Test analysis completed successfully')
            
        except Exception as e:
            error = ErrorHandler.handle_service_error(e, "test_analysis")
            self.log_error(error, "handle_test_analysis")
            emit('error', {
                'message': f'Test analysis failed: {error.message}',
                'session_id': self.current_session_id,
                'timestamp': time.time(),
                'type': 'test_analysis_error'
            })
    
    def _create_empty_analysis(self):
        """Create empty analysis for cases with no transcript"""
        return {
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