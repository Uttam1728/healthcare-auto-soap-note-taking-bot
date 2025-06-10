// Socket connection and event handling
class SocketClient {
    constructor() {
        this.socket = io();
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        this.socket.on('connect', () => {
            window.ui.updateStatus('Connected to server', false);
        });
        
        this.socket.on('disconnect', () => {
            window.ui.updateStatus('Disconnected from server', true);
        });
        
        this.socket.on('status', (data) => {
            window.ui.updateStatus(data.message, false);
        });
        
        this.socket.on('error', (data) => {
            window.ui.updateStatus(data.message, true);
            window.audioRecorder.stopTranscription();
        });
        
        this.socket.on('transcript', (data) => {
            window.ui.displayTranscript(data);
        });
        
        this.socket.on('conversation_analysis', (data) => {
            window.ui.displayAnalysis(data);
        });
        
        this.socket.on('clear_session', () => {
            // Clear transcript display
            document.getElementById('transcript').innerHTML = '<div class="empty-state">Waiting for speech...</div>';
            
            // Hide analysis container
            const analysisContainer = document.getElementById('analysisContainer');
            analysisContainer.style.display = 'none';
            
            // Reset status
            window.ui.updateStatus('Session cleared - ready for new recording', false);
        });
    }

    emit(event, data) {
        this.socket.emit(event, data);
    }
}

// Initialize socket client
window.socketClient = new SocketClient(); 