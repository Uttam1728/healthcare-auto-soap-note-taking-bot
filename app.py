from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from config import DEEPGRAM_API_KEY, ANTHROPIC_API_KEY
from backend.handlers.socket_handlers import SocketHandlers

# Initialize Flask app with frontend folder structure
app = Flask(__name__, 
           template_folder='frontend/templates',
           static_folder='frontend/static')
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize socket handlers
socket_handlers = SocketHandlers(socketio)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

# SocketIO event handlers
@socketio.on('connect')
def handle_connect(*args, **kwargs):
    """Handle client connection"""
    socket_handlers.handle_connect()

@socketio.on('disconnect')
def handle_disconnect(*args, **kwargs):
    """Handle client disconnection"""
    socket_handlers.handle_disconnect()

@socketio.on('start_transcription')
def handle_start_transcription(*args, **kwargs):
    """Handle start transcription request"""
    socket_handlers.handle_start_transcription()

@socketio.on('audio_data')
def handle_audio_data(data, *args, **kwargs):
    """Handle incoming audio data"""
    socket_handlers.handle_audio_data(data)

@socketio.on('stop_transcription')
def handle_stop_transcription(*args, **kwargs):
    """Handle stop transcription request"""
    socket_handlers.handle_stop_transcription()

@socketio.on('retry_analysis')
def handle_retry_analysis(*args, **kwargs):
    """Handle retry analysis request"""
    socket_handlers.handle_retry_analysis()

@socketio.on('test_analysis')
def handle_test_analysis(*args, **kwargs):
    """Handle test analysis request"""
    socket_handlers.handle_test_analysis()

if __name__ == '__main__':
    # Validate configuration
    if not DEEPGRAM_API_KEY:
        print("Error: DEEPGRAM_API_KEY not found in config")
        exit(1)
    
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not found in config")
        exit(1)
    
    print("Starting Healthcare SOAP Note Taking Bot...")
    print("Configuration validated successfully")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5002, allow_unsafe_werkzeug=True) 