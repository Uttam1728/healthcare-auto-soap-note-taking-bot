from flask_socketio import emit
from services.transcription_service import TranscriptionService
from services.conversation_analyzer import ConversationAnalyzer


class SocketHandlers:
    """Class to handle all SocketIO events"""
    
    def __init__(self, socketio=None):
        """Initialize socket handlers with services"""
        self.transcription_service = TranscriptionService()
        self.conversation_analyzer = ConversationAnalyzer()
        self.conversation_analysis = None
        self.socketio = socketio
    
    def handle_connect(self, *args, **kwargs):
        """Handle client connection"""
        print('Client connected')
        emit('status', {'message': 'Connected to server'})
    
    def handle_disconnect(self, *args, **kwargs):
        """Handle client disconnection"""
        print('Client disconnected')
        self.transcription_service.stop_transcription()
    
    def handle_start_transcription(self, *args, **kwargs):
        """Handle start transcription request"""
        print('Starting transcription...')
        
        # Clear frontend display
        emit('clear_session')
        
        # Define callback functions for transcription service
        def on_transcript(data):
            if self.socketio:
                self.socketio.emit('transcript', data)
            else:
                emit('transcript', data)
        
        def on_error(message):
            if self.socketio:
                self.socketio.emit('error', {'message': message})
            else:
                emit('error', {'message': message})
        
        def on_status(message):
            if self.socketio:
                self.socketio.emit('status', {'message': message})
            else:
                emit('status', {'message': message})
        
        # Start transcription
        success = self.transcription_service.start_transcription(
            on_transcript=on_transcript,
            on_error=on_error,
            on_status=on_status
        )
        
        if not success:
            emit('error', {'message': 'Failed to start transcription'})
    
    def handle_audio_data(self, data):
        """Handle incoming audio data"""
        if 'audio' in data:
            self.transcription_service.send_audio_data(data['audio'])
    
    def handle_stop_transcription(self, *args, **kwargs):
        """Handle stop transcription request"""
        print('Stopping transcription...')
        
        # Stop transcription service
        self.transcription_service.stop_transcription()
        emit('status', {'message': 'Transcription stopped'})
        
        # Get the full transcript
        full_transcript = self.transcription_service.get_full_transcript()
        
        # Analyze the conversation if we have transcript
        if full_transcript.strip():
            emit('status', {'message': 'Analyzing conversation with Claude...'})
            print(f"Analyzing transcript: {full_transcript[:100]}...")
            
            try:
                analysis = self.conversation_analyzer.analyze_conversation_with_sources(full_transcript)
                self.conversation_analysis = analysis
                
                # Send analysis to frontend
                if self.socketio:
                    self.socketio.emit('conversation_analysis', analysis)
                    self.socketio.emit('status', {'message': 'Analysis complete!'})
                else:
                    emit('conversation_analysis', analysis)
                    emit('status', {'message': 'Analysis complete!'})
                
                print('Analysis completed successfully')
                
            except Exception as e:
                print(f"Error in analysis: {e}")
                if self.socketio:
                    self.socketio.emit('error', {'message': f'Analysis failed: {str(e)}'})
                else:
                    emit('error', {'message': f'Analysis failed: {str(e)}'})
        else:
            # Send minimal analysis for empty transcript
            empty_analysis = self._create_empty_analysis()
            if self.socketio:
                self.socketio.emit('conversation_analysis', empty_analysis)
                self.socketio.emit('status', {'message': 'No transcript to analyze'})
            else:
                emit('conversation_analysis', empty_analysis)
                emit('status', {'message': 'No transcript to analyze'})
    
    def handle_retry_analysis(self, *args, **kwargs):
        """Handle retry analysis request"""
        print('Retrying analysis...')
        
        # Get the full transcript
        full_transcript = self.transcription_service.get_full_transcript()
        
        # Analyze the conversation if we have transcript
        if full_transcript.strip():
            emit('status', {'message': 'Retrying analysis with Claude...'})
            print(f"Retrying analysis for transcript: {full_transcript[:100]}...")
            
            try:
                analysis = self.conversation_analyzer.analyze_conversation_with_sources(full_transcript)
                self.conversation_analysis = analysis
                
                # Send analysis to frontend
                if self.socketio:
                    self.socketio.emit('conversation_analysis', analysis)
                    self.socketio.emit('status', {'message': 'Analysis complete!'})
                else:
                    emit('conversation_analysis', analysis)
                    emit('status', {'message': 'Analysis complete!'})
                
                print('Retry analysis completed successfully')
                
            except Exception as e:
                print(f"Error in retry analysis: {e}")
                if self.socketio:
                    self.socketio.emit('error', {'message': f'Retry analysis failed: {str(e)}'})
                else:
                    emit('error', {'message': f'Retry analysis failed: {str(e)}'})
        else:
            if self.socketio:
                self.socketio.emit('status', {'message': 'No transcript available to analyze'})
            else:
                emit('status', {'message': 'No transcript available to analyze'})
    
    def handle_test_analysis(self, *args, **kwargs):
        """Handle test analysis request with sample data"""
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
        
        if self.socketio:
            self.socketio.emit('conversation_analysis', test_analysis)
            self.socketio.emit('status', {'message': 'Test analysis with source mapping complete!'})
        else:
            emit('conversation_analysis', test_analysis)
            emit('status', {'message': 'Test analysis with source mapping complete!'})
    
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