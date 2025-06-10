"""
Pytest configuration and shared fixtures for healthcare bot tests.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from flask import Flask
from flask_socketio import SocketIO

# Add the project root to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import AppConfig, APIConfig, TranscriptionConfig, AIConfig
from backend.services.transcription_service import TranscriptionService
from backend.services.conversation_analyzer import ConversationAnalyzer
from backend.handlers.socket_handlers import SocketHandlers


@pytest.fixture
def test_config():
    """Create test configuration"""
    api_config = APIConfig(
        deepgram_api_key="test_deepgram_key",
        anthropic_api_key="test_anthropic_key"
    )
    
    transcription_config = TranscriptionConfig()
    ai_config = AIConfig()
    
    return AppConfig(
        secret_key="test-secret-key",
        host="localhost",
        port=5002,
        debug=True,
        cors_allowed_origins="*",
        api=api_config,
        transcription=transcription_config,
        ai=ai_config
    )


@pytest.fixture
def mock_deepgram_client():
    """Mock Deepgram client for testing"""
    with patch('backend.services.transcription_service.DeepgramClient') as mock:
        mock_instance = Mock()
        mock_connection = Mock()
        
        # Mock connection methods
        mock_connection.start.return_value = True
        mock_connection.finish.return_value = None
        mock_connection.send.return_value = None
        mock_connection.on.return_value = None
        
        # Mock client methods
        mock_instance.listen.live.v.return_value = mock_connection
        mock.return_value = mock_instance
        
        yield mock_instance


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    with patch('backend.services.conversation_analyzer.anthropic.Anthropic') as mock:
        mock_instance = Mock()
        mock_message = Mock()
        
        # Mock response structure
        mock_content = Mock()
        mock_content.text = '{"test": "response"}'
        mock_message.content = [mock_content]
        
        mock_instance.messages.create.return_value = mock_message
        mock.return_value = mock_instance
        
        yield mock_instance


@pytest.fixture
def transcription_service(test_config, mock_deepgram_client):
    """Create transcription service for testing"""
    with patch('config.config', test_config):
        service = TranscriptionService()
        return service


@pytest.fixture
def conversation_analyzer(test_config, mock_anthropic_client):
    """Create conversation analyzer for testing"""
    with patch('config.config', test_config):
        analyzer = ConversationAnalyzer()
        return analyzer


@pytest.fixture
def socket_handlers(test_config, transcription_service, conversation_analyzer):
    """Create socket handlers for testing"""
    with patch('config.config', test_config):
        handlers = SocketHandlers()
        handlers.transcription_service = transcription_service
        handlers.conversation_analyzer = conversation_analyzer
        return handlers


@pytest.fixture
def flask_app(test_config):
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = test_config.secret_key
    app.config['TESTING'] = True
    return app


@pytest.fixture
def socket_io(flask_app):
    """Create SocketIO instance for testing"""
    return SocketIO(flask_app, async_mode='threading')


@pytest.fixture
def client(flask_app):
    """Create test client"""
    return flask_app.test_client()


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing"""
    return """
    Doctor: Good morning. How can I help you today?
    Patient: I've been having a headache for the past 3 days. It's a throbbing pain on the right side.
    Doctor: I see. Let me check your blood pressure.
    Doctor: Your blood pressure is normal at 120/80.
    Doctor: This sounds like a tension headache. I'll prescribe some ibuprofen and recommend rest.
    Patient: Thank you, doctor.
    """


@pytest.fixture
def sample_audio_data():
    """Sample base64 encoded audio data for testing"""
    import base64
    # Create some dummy audio data
    dummy_audio = b'\x00\x01\x02\x03' * 100
    return base64.b64encode(dummy_audio).decode('utf-8')


@pytest.fixture
def sample_analysis():
    """Sample analysis result for testing"""
    return {
        "speaker_analysis": {
            "doctor_segments": ["Good morning. How can I help you today?"],
            "patient_segments": ["I've been having a headache for the past 3 days"],
            "doctor_percentage": 60,
            "patient_percentage": 40,
            "total_segments": 6
        },
        "conversation_segments": [
            {
                "type": "greeting",
                "content": "Good morning. How can I help you today?",
                "speaker": "doctor"
            }
        ],
        "medical_topics": ["headache", "blood pressure", "tension headache"],
        "summary": "Patient presents with 3-day headache history.",
        "soap_note_with_sources": {
            "subjective": {
                "content": "Patient reports 3-day history of headache",
                "confidence": 95,
                "sources": []
            },
            "objective": {
                "content": "Blood pressure 120/80 mmHg",
                "confidence": 90,
                "sources": []
            },
            "assessment": {
                "content": "Tension headache",
                "confidence": 85,
                "sources": []
            },
            "plan": {
                "content": "Ibuprofen and rest",
                "confidence": 90,
                "sources": []
            }
        }
    }


@pytest.fixture
def temp_log_file():
    """Create temporary log file for testing"""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as f:
        yield f.name
    os.unlink(f.name)


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow 