from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from config import config, validate_configuration
from backend.handlers.socket_handlers import SocketHandlers
from backend.utils.logging_config import init_logging, get_logger
from backend.utils.cache import cleanup_caches, get_cache_stats
from backend.utils.metrics import metrics_collector, healthcare_metrics
import atexit
import threading
import time

# Initialize logging
init_logging()
logger = get_logger(__name__)

# Initialize Flask app with frontend folder structure
app = Flask(__name__, 
           template_folder='frontend/templates',
           static_folder='frontend/static')

# Configure app from config object
app.config['SECRET_KEY'] = config.secret_key
app.config.update({
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB max file upload
    'JSON_SORT_KEYS': False,
    'JSONIFY_PRETTYPRINT_REGULAR': True
})

socketio = SocketIO(
    app, 
    cors_allowed_origins=config.cors_allowed_origins, 
    async_mode='threading',
    logger=logger,
    engineio_logger=logger
)

# Initialize socket handlers
socket_handlers = SocketHandlers(socketio)

@app.route('/')
def index():
    """Render the main page"""
    try:
        logger.info("Serving main page")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error serving main page: {e}", exc_info=True)
        return f"Application error: {str(e)}", 500

@app.route('/health')
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Collect various health metrics
        cache_stats = get_cache_stats()
        system_metrics = metrics_collector.get_all_metrics()
        
        # Check component health
        health_status = {
            'status': 'healthy',
            'timestamp': time.time(),
            'version': '1.0.0',
            'uptime': system_metrics.get('uptime', 0),
            'components': {
                'cache': {
                    'status': 'healthy',
                    'stats': cache_stats
                },
                'metrics': {
                    'status': 'healthy',
                    'collection_enabled': metrics_collector.system_metrics_enabled
                },
                'logging': {
                    'status': 'healthy'
                }
            },
            'system': {
                'cpu_percent': system_metrics['time_series'].get('system.cpu.percent', {}).get('latest', 0),
                'memory_percent': system_metrics['time_series'].get('system.memory.percent', {}).get('latest', 0),
                'disk_percent': system_metrics['time_series'].get('system.disk.percent', {}).get('latest', 0)
            },
            'performance': {
                'total_requests': system_metrics['gauges'].get('session.events.total', 0),
                'error_count': system_metrics['gauges'].get('errors.total', 0)
            }
        }
        
        # Check if any critical thresholds are exceeded
        cpu_percent = health_status['system']['cpu_percent']
        memory_percent = health_status['system']['memory_percent']
        disk_percent = health_status['system']['disk_percent']
        
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
            health_status['status'] = 'degraded'
            health_status['warnings'] = []
            
            if cpu_percent > 90:
                health_status['warnings'].append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 90:
                health_status['warnings'].append(f"High memory usage: {memory_percent:.1f}%")
            if disk_percent > 95:
                health_status['warnings'].append(f"High disk usage: {disk_percent:.1f}%")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            'status': 'unhealthy',
            'timestamp': time.time(),
            'error': str(e)
        }, 500

@app.route('/metrics')
def metrics_endpoint():
    """Metrics endpoint for monitoring systems"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type == 'prometheus':
            response = app.response_class(
                response=metrics_collector.export_metrics('prometheus'),
                status=200,
                mimetype='text/plain'
            )
        else:
            response = {
                'metrics': metrics_collector.get_all_metrics(),
                'timestamp': time.time()
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}", exc_info=True)
        return {'error': str(e)}, 500

# SocketIO event handlers
# Enhanced SocketIO event handlers with error handling
@socketio.on('connect')
def handle_connect(*args, **kwargs):
    """Handle client connection"""
    try:
        logger.info("Client connecting")
        socket_handlers.handle_connect()
    except Exception as e:
        logger.error(f"Error handling client connection: {e}", exc_info=True)
        emit('error', {'message': 'Connection error occurred'})

@socketio.on('disconnect')
def handle_disconnect(*args, **kwargs):
    """Handle client disconnection"""
    try:
        logger.info("Client disconnecting")
        socket_handlers.handle_disconnect()
    except Exception as e:
        logger.error(f"Error handling client disconnection: {e}", exc_info=True)

@socketio.on('start_transcription')
def handle_start_transcription(*args, **kwargs):
    """Handle start transcription request"""
    try:
        logger.info("Starting transcription session")
        socket_handlers.handle_start_transcription()
    except Exception as e:
        logger.error(f"Error starting transcription: {e}", exc_info=True)
        emit('error', {'message': f'Failed to start transcription: {str(e)}'})

@socketio.on('audio_data')
def handle_audio_data(data, *args, **kwargs):
    """Handle incoming audio data"""
    try:
        socket_handlers.handle_audio_data(data)
    except Exception as e:
        logger.error(f"Error processing audio data: {e}", exc_info=True)
        emit('error', {'message': 'Audio processing error'})

@socketio.on('stop_transcription')
def handle_stop_transcription(*args, **kwargs):
    """Handle stop transcription request"""
    try:
        logger.info("Stopping transcription session")
        socket_handlers.handle_stop_transcription()
    except Exception as e:
        logger.error(f"Error stopping transcription: {e}", exc_info=True)
        emit('error', {'message': f'Error stopping transcription: {str(e)}'})

@socketio.on('retry_analysis')
def handle_retry_analysis(*args, **kwargs):
    """Handle retry analysis request"""
    try:
        logger.info("Retrying analysis")
        socket_handlers.handle_retry_analysis()
    except Exception as e:
        logger.error(f"Error retrying analysis: {e}", exc_info=True)
        emit('error', {'message': f'Retry analysis failed: {str(e)}'})

@socketio.on('test_analysis')
def handle_test_analysis(*args, **kwargs):
    """Handle test analysis request"""
    try:
        logger.info("Running test analysis")
        socket_handlers.handle_test_analysis()
    except Exception as e:
        logger.error(f"Error in test analysis: {e}", exc_info=True)
        emit('error', {'message': f'Test analysis failed: {str(e)}'})

def setup_cleanup():
    """Setup cleanup handlers for graceful shutdown"""
    def cleanup_handler():
        logger.info("Application shutting down, cleaning up resources...")
        cleanup_caches()
        logger.info("Cleanup completed")
    
    atexit.register(cleanup_handler)

def start_background_tasks():
    """Start background maintenance tasks"""
    def cache_cleanup_task():
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                cleanup_caches()
                logger.debug("Background cache cleanup completed")
            except Exception as e:
                logger.error(f"Error in background cache cleanup: {e}")
    
    # Start cache cleanup thread
    cleanup_thread = threading.Thread(target=cache_cleanup_task, daemon=True)
    cleanup_thread.start()
    logger.info("Background maintenance tasks started")

if __name__ == '__main__':
    try:
        # Validate configuration
        if not validate_configuration():
            logger.error("Configuration validation failed")
            exit(1)
        
        logger.info("Starting Healthcare SOAP Note Taking Bot...")
        logger.info("Configuration validated successfully")
        
        # Setup cleanup handlers
        setup_cleanup()
        
        # Start background tasks
        start_background_tasks()
        
        # Start the application
        socketio.run(
            app, 
            debug=config.debug, 
            host=config.host, 
            port=config.port, 
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error starting application: {e}", exc_info=True)
        exit(1) 