# Healthcare Auto SOAP Note Taking Bot

A comprehensive real-time speech transcription and medical conversation analysis web application built with Python Flask, WebSockets, Deepgram API, and Claude AI. This application automatically generates structured SOAP notes from doctor-patient conversations with advanced medical terminology recognition and intelligent conversation analysis.

## 🏥 Overview

This application revolutionizes medical documentation by providing real-time transcription of doctor-patient conversations and automatically generating structured SOAP (Subjective, Objective, Assessment, Plan) notes. Built with healthcare professionals in mind, it leverages cutting-edge AI technology to streamline clinical documentation workflows.

## ✨ Features

### Core Functionality
- 🎤 **Real-time Audio Capture**: Browser-based microphone integration with WebSocket streaming
- 🔄 **Live Transcription**: Deepgram's Nova-2 model optimized for medical terminology
- 🏥 **Medical AI Analysis**: Claude AI-powered conversation analysis for healthcare contexts
- 📋 **SOAP Note Generation**: Automatic generation of structured medical notes
- 💬 **Speaker Identification**: Intelligent distinction between doctor and patient voices
- 📊 **Source Citations**: Traceable analysis with confidence scores and source mapping

### Advanced Features
- 🔧 **Modular Architecture**: Clean separation of concerns with organized backend structure
- 📈 **Performance Monitoring**: Built-in metrics collection and system monitoring
- 🛡️ **Security & Validation**: Input validation, error handling, and secure configuration
- 🚀 **Caching System**: Performance optimization with intelligent caching
- 📝 **Comprehensive Logging**: Structured logging with JSON format for monitoring
- 🔄 **Retry Logic**: Robust error recovery and connection management
- 📱 **Modern UI**: Clean, responsive interface with real-time visual indicators
- 🐳 **Docker Support**: Containerized deployment with Docker Compose

## 🏗️ Architecture

### Backend Structure (Modular Design)
```
backend/
├── handlers/           # WebSocket event handlers
│   └── socket_handlers.py
├── models/            # Data models and structures
│   └── analysis_models.py
├── prompts/           # AI prompt templates
│   ├── basic_analysis_prompt.py
│   ├── enhanced_analysis_prompt.py
│   └── prompt_manager.py
├── services/          # Core business logic
│   ├── conversation_analyzer.py
│   └── transcription_service.py
└── utils/             # Utilities and helpers
    ├── logging_config.py
    ├── cache.py
    └── metrics.py
```

### Technology Stack
- **Backend**: Flask + Flask-SocketIO for real-time WebSocket communication
- **AI Integration**: Deepgram SDK for speech-to-text, Anthropic Claude for analysis
- **Frontend**: Modern JavaScript with Web Audio API and Socket.IO client
- **Configuration**: Environment-based configuration with validation
- **Monitoring**: Built-in metrics collection and health checks
- **Deployment**: Docker containerization with compose support

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (tested with Python 3.13)
- Deepgram API key ([Get one here](https://deepgram.com/))
- Anthropic API key ([Get one here](https://console.anthropic.com/))
- Modern web browser with microphone access

### Installation

1. **Clone and Setup Environment**
```bash
# Navigate to your project directory
cd /path/to/your/project

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure API Keys**

Create a `.env` file in the project root:
```env
# Required API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Configuration
SECRET_KEY=your_secret_key_here
DEBUG=false
HOST=0.0.0.0
PORT=5002
CORS_ALLOWED_ORIGINS=*
```

Alternatively, set environment variables:
```bash
export DEEPGRAM_API_KEY="your_deepgram_api_key_here"
export ANTHROPIC_API_KEY="your_anthropic_api_key_here"
```

3. **Run the Application**
```bash
python app.py
```

The server will start at `http://localhost:5002` with enhanced monitoring and logging.

### Docker Deployment

For containerized deployment:
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or with custom environment
cp .env.example .env  # Edit with your API keys
docker-compose up --build
```

## 📖 Usage

### Basic Operation
1. Navigate to `http://localhost:5002` in your web browser
2. Click "Start Recording" and allow microphone access
3. Conduct your doctor-patient conversation naturally
4. Click "Stop Recording" when the consultation is complete
5. Review the generated SOAP note with detailed source citations

### Medical Conversation Best Practices
- Speak clearly and at a moderate pace
- Ensure the doctor introduces themselves and the patient
- Use standard medical terminology for better recognition
- Allow natural pauses for better speaker identification
- Keep conversations focused on clinical relevant topics

### SOAP Note Output
The application generates comprehensive SOAP notes including:

**Subjective**: Patient-reported symptoms, history, and concerns
**Objective**: Clinical findings, measurements, and observations  
**Assessment**: Medical diagnoses and clinical reasoning
**Plan**: Treatment recommendations and follow-up instructions

Each section includes:
- Direct source citations from the conversation
- Confidence scores for analysis accuracy
- Detailed sub-components for thorough documentation

## 🔧 Configuration

### Transcription Settings
The application uses optimized settings for medical conversations:
- **Model**: Nova-2 (medical terminology optimized)
- **Sample Rate**: 16,000 Hz (optimal for speech)
- **Encoding**: Linear16 PCM
- **Speaker Diarization**: Enabled for doctor/patient identification
- **Medical Keywords**: Enhanced recognition for clinical terms
- **Utterance Timing**: Extended timeouts for thoughtful medical discussions

### AI Analysis Settings
- **Model**: Claude-3.5-Sonnet for advanced reasoning
- **Temperature**: 0.1 for consistent, precise analysis
- **Max Tokens**: 2500 for detailed SOAP notes
- **Timeout**: 30 seconds with retry logic

## 🏥 Medical Features

### Medical Terminology Enhancement
The application includes specialized configuration for healthcare:
- **Medical Keywords**: Comprehensive list of clinical terms
- **Profanity Filter**: Disabled to preserve medical terminology
- **Smart Formatting**: Automatic formatting of medical measurements
- **Punctuation**: Enhanced for clinical documentation standards

### Healthcare-Specific Components
- **Patient Privacy**: No data persistence, session-based processing
- **Clinical Accuracy**: High-confidence thresholds for medical analysis
- **Source Traceability**: Every SOAP component linked to conversation excerpts
- **Professional Format**: Standard medical documentation structure

## 🔍 Monitoring & Health Checks

### Built-in Endpoints
- `GET /health` - Comprehensive health check with system metrics
- `GET /metrics` - Performance metrics in JSON or Prometheus format
- Real-time logging with structured JSON format

### Performance Features
- **Intelligent Caching**: LRU cache with TTL for API responses
- **Connection Pooling**: Optimized API connections with retry logic
- **Background Tasks**: Automatic cache cleanup and maintenance
- **System Monitoring**: CPU, memory, and disk usage tracking

## 🛠️ Development

### Code Organization
```
├── app.py                    # Main Flask application
├── config.py                 # Configuration management
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # Docker deployment
├── backend/                  # Modular backend package
│   ├── handlers/            # WebSocket event handlers
│   ├── models/              # Data models
│   ├── prompts/             # AI prompt templates
│   ├── services/            # Business logic
│   └── utils/               # Utilities and helpers
├── frontend/                # Frontend assets
│   ├── static/             # CSS, JS, images
│   └── templates/          # HTML templates
├── tests/                   # Test suite
├── logs/                    # Application logs
└── data/                    # Temporary data storage
```

### Development Tools
```bash
# Install development dependencies
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Code formatting
black .

# Linting
flake8 .

# Type checking
mypy backend/
```

### Making Changes
1. **Backend Logic**: Edit files in `backend/` package
2. **Frontend UI**: Modify files in `frontend/` directory  
3. **AI Prompts**: Update templates in `backend/prompts/`
4. **Configuration**: Adjust settings in `config.py`

## 🔒 Security & Compliance

### Security Features
- Environment-based API key management
- Input validation and sanitization
- CORS configuration for secure origins
- Error handling without information leakage
- Session-based processing (no data persistence)

### Medical Compliance Notes
- **Data Privacy**: No conversation data is stored permanently
- **HIPAA Considerations**: Designed for secure clinical environments
- **Access Control**: Consider implementing authentication for production
- **Audit Trail**: Comprehensive logging for compliance requirements

### Production Deployment
- Use HTTPS for all communications
- Implement proper authentication and authorization
- Configure secure CORS origins
- Set up monitoring and alerting
- Regular security updates and API key rotation

## 🧪 Testing

### Automated Testing
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test categories
pytest tests/test_transcription_service.py
pytest tests/test_conversation_analyzer.py
```

### Manual Testing
1. **Audio Quality**: Test with various microphone setups
2. **Medical Terminology**: Use clinical vocabulary in test conversations
3. **Error Handling**: Test network interruptions and API failures
4. **Performance**: Monitor with extended conversations

## 🚨 Troubleshooting

### Common Issues

**Microphone Access Denied**
- Ensure HTTPS or localhost access
- Check browser microphone permissions
- Verify Web Audio API support

**API Connection Errors**
- Validate API keys in `.env` file
- Check API service status and quotas
- Verify network connectivity

**Audio Processing Issues**
- Refresh the page to reset WebSocket connection
- Check browser console for JavaScript errors
- Test microphone in other applications

**Docker Deployment Issues**
- Ensure Docker and Docker Compose are installed
- Check port availability (5002)
- Verify environment variables in docker-compose.yml

### Performance Optimization
- Monitor system resources with `/health` endpoint
- Use `/metrics` endpoint for performance tracking
- Check logs for bottlenecks and errors
- Configure cache settings for your usage patterns

## 💰 API Costs

### Pricing Considerations
- **Deepgram**: Charges based on audio duration processed
- **Anthropic**: Charges based on tokens (input + output)
- Typical cost per 10-minute consultation: $0.50-2.00 USD

Check current pricing:
- [Deepgram Pricing](https://deepgram.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)

## 📚 Additional Resources

### Documentation
- See `INSTALL.md` for detailed installation instructions
- Check `frontend/README.md` for UI development guidelines
- Review `backend/prompts/README.md` for AI prompt customization

### Medical Integration
- Consider EHR integration for production use
- Implement voice enrollment for better speaker identification
- Add clinical decision support features

## ⚖️ Legal & Medical Disclaimer

**Important**: This application is for educational and development purposes only. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical decisions.

- Not FDA approved for clinical use
- Requires validation in clinical environments
- Follow institutional policies for AI assistance tools
- Ensure compliance with local healthcare regulations

## 📄 License

This project is for educational and development purposes. Please respect Deepgram's and Anthropic's terms of service when using their APIs. Commercial use requires appropriate licensing and compliance with healthcare regulations.

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Python Compatibility**: 3.11+  
**Browser Support**: Chrome, Firefox, Safari, Edge (WebRTC required) 