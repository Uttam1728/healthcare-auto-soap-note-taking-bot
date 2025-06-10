# Real-time Transcription App

A minimalistic real-time speech transcription web application using Python Flask, WebSockets, and Deepgram API.

## Features

- 🎤 Real-time audio capture from browser microphone
- 🔄 WebSocket connection for low-latency communication
- 📝 Live transcription using Deepgram's Nova-2 model
- 💬 Interim and final transcript results
- 🎨 Clean, modern UI with visual recording indicators

## Prerequisites

- Python 3.7+
- Deepgram API key ([Get one here](https://deepgram.com/))
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

### 4. Configure Deepgram API Key
Set your Deepgram API key as an environment variable:

```bash
export DEEPGRAM_API_KEY="your_actual_deepgram_api_key_here"
```

Or alternatively, modify the `config.py` file to directly include your API key:
```python
DEEPGRAM_API_KEY = "your_actual_deepgram_api_key_here"
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
4. Start speaking - you'll see interim results in gray text and final results in bold
5. Click "Stop Recording" when finished

## Project Structure

```
├── app.py              # Main Flask-SocketIO application
├── config.py           # Configuration and API key management
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Frontend HTML with embedded CSS/JS
└── README.md          # This file
```

## Technical Details

### Backend (Python)
- **Flask-SocketIO**: WebSocket server for real-time communication
- **Deepgram SDK**: Integration with Deepgram's live transcription API
- **Audio Processing**: Handles base64-encoded audio chunks from frontend

### Frontend (JavaScript)
- **Web Audio API**: Captures microphone input at 16kHz, mono
- **Socket.IO**: WebSocket client for server communication
- **Real-time Audio**: Processes audio in 4096-sample chunks

### Audio Configuration
- Sample Rate: 16,000 Hz
- Channels: 1 (Mono)
- Encoding: Linear16
- Chunk Size: 4096 samples

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**
   - Ensure you're accessing the app via HTTPS or localhost
   - Check browser permissions for microphone access

2. **Deepgram Connection Error**
   - Verify your API key is correct and active
   - Check your internet connection
   - Ensure you have sufficient Deepgram credits

3. **Audio Not Processing**
   - Try refreshing the page
   - Check browser console for JavaScript errors
   - Ensure microphone is working in other applications

4. **WebSocket Connection Issues**
   - Check if port 5000 is available
   - Try restarting the application
   - Check firewall settings

### Browser Compatibility
- Chrome (recommended)
- Firefox
- Safari
- Edge

Note: Requires browsers that support Web Audio API and WebRTC.

## API Costs

This app uses Deepgram's live transcription API. Pricing is based on:
- Duration of audio processed
- Model used (Nova-2)
- Features enabled (smart formatting, interim results)

Check [Deepgram's pricing](https://deepgram.com/pricing) for current rates.

## Development

To modify the application:

1. **Backend changes**: Edit `app.py` for server-side logic
2. **Frontend changes**: Edit `templates/index.html` for UI modifications
3. **Configuration**: Update `config.py` for API settings

## Security Notes

- Keep your Deepgram API key secure and never commit it to version control
- Consider implementing authentication for production use
- Use HTTPS in production environments
- Validate and sanitize all input data

## License

This project is for educational and development purposes. Please respect Deepgram's terms of service when using their API. 