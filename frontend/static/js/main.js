// Main initialization file
// This ensures all modules are loaded and initialized in the correct order

document.addEventListener('DOMContentLoaded', function() {
    // All modules should be loaded by now due to script order in HTML
    console.log('Healthcare SOAP Note Taking Bot - Frontend Initialized');
    
    // Verify all required modules are loaded
    if (!window.socketClient) {
        console.error('Socket client not loaded');
    }
    
    if (!window.audioRecorder) {
        console.error('Audio recorder not loaded');
    }
    
    if (!window.ui) {
        console.error('UI handler not loaded');
    }
    
    // All modules loaded successfully
    if (window.socketClient && window.audioRecorder && window.ui) {
        console.log('All modules loaded successfully');
        window.ui.updateStatus('Ready to start transcription', false);
    }
}); 