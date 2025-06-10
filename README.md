# Healthcare Auto SOAP Note Taking Bot

A real-time speech transcription and medical conversation analysis web application using Python Flask, WebSockets, Deepgram API, and Claude AI for generating SOAP notes from doctor-patient conversations.

## Features

- 🎤 Real-time audio capture from browser microphone
- 🔄 WebSocket connection for low-latency communication
- 📝 Live transcription using Deepgram's Nova-2 model optimized for medical terminology
- 🏥 AI-powered conversation analysis for healthcare settings
- 📋 Automatic SOAP note generation with source mapping
- 💬 Speaker identification (doctor vs patient)
- 🎨 Clean, modern UI with visual recording indicators
- 📊 Enhanced analysis with confidence scores and source citations

## Prerequisites

- Python 3.7+
- Deepgram API key ([Get one here](https://deepgram.com/))
- Anthropic API key for Claude AI ([Get one here](https://console.anthropic.com/))
- Modern web browser with microphone access

## Setup Instructions

### 1. Clone and Navigate to Project
```bash
cd /path/to/your/project
```

### 2. Create Virtual Environment (Recommended)
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Set your API keys as environment variables:

```bash
export DEEPGRAM_API_KEY="your_actual_deepgram_api_key_here"
export ANTHROPIC_API_KEY="your_actual_anthropic_api_key_here"
```

Or alternatively, modify the `config.py` file to directly include your API keys:
```python
DEEPGRAM_API_KEY = "your_actual_deepgram_api_key_here"
ANTHROPIC_API_KEY = "your_actual_anthropic_api_key_here"
```

### 5. Run the Application
```bash
python app.py
```

The server will start at `http://localhost:5002`

## Usage

1. Open your web browser and navigate to `http://localhost:5002`
2. Click the "Start Recording" button
3. Allow microphone access when prompted
4. Conduct your doctor-patient conversation
5. Click "Stop Recording" when finished
6. View the generated SOAP note with source citations and analysis

## Project Structure

```
├── app.py                    # Main Flask-SocketIO application
├── config.py                 # Configuration and API key management
├── requirements.txt          # Python dependencies
├── backend/                  # Backend package (refactored)
│   ├── __init__.py          # Backend package initialization
│   ├── handlers/            # Socket.IO event handlers
│   │   ├── __init__.py
│   │   └── socket_handlers.py
│   ├── models/              # Data models for analysis
│   │   ├── __init__.py
│   │   └── analysis_models.py
│   ├── prompts/             # AI prompt templates
│   │   ├── __init__.py      
│   │   ├── basic_analysis_prompt.py
│   │   ├── enhanced_analysis_prompt.py
│   │   ├── prompt_manager.py
│   │   └── README.md
│   └── services/            # Business logic services
│       ├── __init__.py
│       ├── conversation_analyzer.py
│       └── transcription_service.py
├── frontend/                # Frontend assets
│   ├── static/             # CSS, JS, and other static files
│   └── templates/          # HTML templates
│       └── index.html
├── REFACTORING_GUIDE.md    # Detailed refactoring guide
├── FRONTEND_MODULARIZATION.md # Frontend structure guide
└── README.md               # This file
```

## Technical Details

### Backend Architecture (Refactored)
- **Flask-SocketIO**: WebSocket server for real-time communication
- **Deepgram SDK**: Integration with Deepgram's live transcription API with medical terminology optimization
- **Anthropic Claude**: AI-powered conversation analysis and SOAP note generation
- **Modular Structure**: Organized into handlers, models, prompts, and services for maintainability

#### Backend Components:
- **Handlers**: Socket.IO event handlers for real-time communication
- **Models**: Data models for conversation analysis and SOAP notes
- **Prompts**: AI prompt templates for conversation analysis
- **Services**: Core business logic for transcription and analysis

### Frontend (JavaScript)
- **Web Audio API**: Captures microphone input at 16kHz, mono
- **Socket.IO**: WebSocket client for server communication
- **Real-time Audio**: Processes audio in 4096-sample chunks
- **Enhanced UI**: SOAP note visualization with source mapping

### Medical-Specific Configuration
- **Deepgram Model**: Nova-2 optimized for medical terminology
- **Keywords**: Medical terminology boost for better accuracy
- **Speaker Diarization**: Distinguishes between doctor and patient
- **Utterance Timing**: Longer timeouts for thoughtful medical conversations
- **Profanity Filter**: Disabled to preserve medical terminology

### Audio Configuration
- Sample Rate: 16,000 Hz
- Channels: 1 (Mono)
- Encoding: Linear16
- Chunk Size: 4096 samples
- Medical Keywords: Enhanced recognition for medical terms

## SOAP Note Generation

The application generates comprehensive SOAP notes with:

- **Subjective**: Patient-reported symptoms and history
- **Objective**: Clinical findings and measurements
- **Assessment**: Medical diagnoses and clinical reasoning
- **Plan**: Treatment plans and follow-up instructions

Each component includes:
- Source citations from the conversation
- Confidence scores
- Sub-components for detailed analysis

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**
   - Ensure you're accessing the app via HTTPS or localhost
   - Check browser permissions for microphone access

2. **Deepgram Connection Error**
   - Verify your API key is correct and active
   - Check your internet connection
   - Ensure you have sufficient Deepgram credits

3. **Claude AI Analysis Errors**
   - Verify your Anthropic API key is correct
   - Check API usage limits
   - Ensure conversation is long enough for analysis

4. **Audio Not Processing**
   - Try refreshing the page
   - Check browser console for JavaScript errors
   - Ensure microphone is working in other applications

5. **Import Errors After Refactoring**
   - Ensure all backend imports use relative imports (..module)
   - Check Python path includes the backend package

### Browser Compatibility
- Chrome (recommended)
- Firefox
- Safari
- Edge

Note: Requires browsers that support Web Audio API and WebRTC.

## API Costs

This application uses:
- **Deepgram**: Live transcription API (pricing based on audio duration)
- **Anthropic Claude**: AI analysis API (pricing based on tokens processed)

Check [Deepgram's pricing](https://deepgram.com/pricing) and [Anthropic's pricing](https://www.anthropic.com/pricing) for current rates.

## Development

### Recent Refactoring (2024)
The application has been refactored to improve maintainability:
- Moved backend code to `backend/` package
- Separated concerns into handlers, models, prompts, and services
- Improved import structure with relative imports
- Enhanced documentation and guides

### Making Changes
1. **Backend changes**: Edit files in `backend/` package
2. **Frontend changes**: Edit files in `frontend/` directory
3. **Configuration**: Update `config.py` for API settings
4. **Prompts**: Modify AI prompts in `backend/prompts/`

## Security Notes

- Keep your API keys secure and never commit them to version control
- Consider implementing authentication for production use
- Use HTTPS in production environments
- Validate and sanitize all input data
- Follow HIPAA compliance guidelines for medical data

## Medical Disclaimer

This application is for educational and development purposes only. It should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare professionals for medical decisions.

## License

This project is for educational and development purposes. Please respect Deepgram's and Anthropic's terms of service when using their APIs. 