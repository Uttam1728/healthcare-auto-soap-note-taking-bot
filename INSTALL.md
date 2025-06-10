# Healthcare Auto SOAP Note Taking Bot - Installation Guide

## Prerequisites

- Python 3.11+ (tested with Python 3.13)
- Virtual environment (recommended)
- API keys for Deepgram and Anthropic

## Installation Steps

### 1. Clone the Repository
```bash
cd your-project-directory
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note**: If you encounter issues with package installation (especially on Python 3.13), the essential packages have been tested and work correctly.

### 4. Environment Configuration
Create a `.env` file in the project root:
```env
# API Keys
DEEPGRAM_API_KEY=your_deepgram_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Application Configuration
SECRET_KEY=your_secret_key_here
DEBUG=false
HOST=0.0.0.0
PORT=5002

# Optional: Advanced Configuration
CORS_ALLOWED_ORIGINS=*
```

### 5. Run the Application
```bash
python app.py
```

The application will start with:
- Enhanced logging and monitoring
- Input validation and security features
- Performance caching
- Error handling and recovery
- Background maintenance tasks

## Features Included

✅ **Structured Configuration**: Environment-based configuration with validation  
✅ **Comprehensive Logging**: JSON-formatted logs with performance monitoring  
✅ **Exception Handling**: Custom exception hierarchy with graceful error recovery  
✅ **Caching System**: LRU cache with TTL for improved performance  
✅ **Input Validation**: Security-focused validation for all user inputs  
✅ **Performance Monitoring**: System metrics and application performance tracking  
✅ **Enhanced Services**: Retry logic, connection management, and fallback mechanisms  

## Troubleshooting

### Package Installation Issues
If you encounter issues with `pydantic` or other packages on Python 3.13:
1. The application runs fine with the essential packages only
2. Optional development packages are commented out in requirements.txt
3. Install additional packages as needed: `pip install pytest black flake8`

### Port Already in Use
If port 5002 is already in use, change the PORT in your `.env` file or:
```bash
PORT=5003 python app.py
```

### API Key Issues
Make sure your API keys are valid and have the necessary permissions:
- Deepgram: Speech-to-text transcription
- Anthropic: AI analysis for SOAP notes

## Development

For development with additional tools:
```bash
# Install development dependencies (optional)
pip install pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black .

# Lint code
flake8 .
```

## Docker Deployment

The application includes Docker configuration:
```bash
# Build and run with Docker Compose
docker-compose up --build
``` 