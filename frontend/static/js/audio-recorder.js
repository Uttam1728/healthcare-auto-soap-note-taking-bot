// Audio recording and processing
class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioContext = null;
        this.source = null;
        this.processor = null;
        this.isRecording = false;
        this.bufferInterval = null;
        this.sendAudioBuffer = null;
        this.audioIndicatorTimeout = null;
    }

    // Check browser compatibility
    checkBrowserCompatibility() {
        if (!navigator.mediaDevices) {
            return 'Your browser does not support microphone access. Please use Chrome, Firefox, or Safari.';
        }
        
        if (!navigator.mediaDevices.getUserMedia) {
            return 'Your browser does not support getUserMedia. Please update your browser.';
        }
        
        if (!window.AudioContext && !window.webkitAudioContext) {
            return 'Your browser does not support Web Audio API. Please use a modern browser.';
        }
        
        if (location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
            return 'Microphone access requires HTTPS or localhost. Please use a secure connection.';
        }
        
        return null;
    }

    async startTranscription() {
        try {
            // Check browser compatibility first
            const compatibilityError = this.checkBrowserCompatibility();
            if (compatibilityError) {
                window.ui.updateStatus(compatibilityError, true);
                return;
            }
            
            window.ui.updateStatus('Requesting microphone access...', false);
            
            // Request microphone access with better error handling
            let stream;
            try {
                stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        sampleRate: 16000,
                        channelCount: 1,
                        volume: 1.0,
                        echoCancellation: true,
                        noiseSuppression: false,  // Disable to preserve quiet speech
                        autoGainControl: true,    // Enable for better volume
                        googEchoCancellation: true,
                        googAutoGainControl: true,
                        googNoiseSuppression: false,
                        googHighpassFilter: false  // Don't filter low frequencies
                    }
                });
            } catch (mediaError) {
                let errorMessage = 'Microphone access denied. ';
                if (mediaError.name === 'NotAllowedError') {
                    errorMessage += 'Please allow microphone access and try again.';
                } else if (mediaError.name === 'NotFoundError') {
                    errorMessage += 'No microphone found. Please connect a microphone.';
                } else if (mediaError.name === 'NotReadableError') {
                    errorMessage += 'Microphone is already in use by another application.';
                } else {
                    errorMessage += `Error: ${mediaError.message}`;
                }
                window.ui.updateStatus(errorMessage, true);
                return;
            }
            
            window.ui.updateStatus('Setting up audio processing...', false);
            
            // Create audio context with optimal settings for medical conversations
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 16000,
                latencyHint: 'interactive' // Optimize for real-time interaction
            });
            
            this.source = this.audioContext.createMediaStreamSource(stream);
            
            // Create filter chain for better medical speech recognition
            
            // 1. High-pass filter to remove low-frequency noise (AC hum, etc.)
            const highPassFilter = this.audioContext.createBiquadFilter();
            highPassFilter.type = 'highpass';
            highPassFilter.frequency.value = 80; // Remove frequencies below 80Hz
            
            // 2. Compressor to normalize audio levels (important for varying speaking volumes)
            const compressor = this.audioContext.createDynamicsCompressor();
            compressor.threshold.value = -20;
            compressor.knee.value = 5;
            compressor.ratio.value = 5;
            compressor.attack.value = 0.005;
            compressor.release.value = 0.1;
            
            // 3. Gain node for controlled amplification
            const gainNode = this.audioContext.createGain();
            gainNode.gain.value = 1.8; // Slightly less aggressive gain to prevent clipping
            
            // 4. Low-pass filter to remove high-frequency noise while preserving speech
            const lowPassFilter = this.audioContext.createBiquadFilter();
            lowPassFilter.type = 'lowpass';
            lowPassFilter.frequency.value = 8000; // Human speech rarely goes above 8kHz
            
            // Create script processor for audio data (optimized for real-time)
            this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
            
            // Audio buffer to prevent data loss (smaller for better real-time)
            let audioBuffer = [];
            let bufferSize = 0;
            const maxBufferSize = 4096; // Send when buffer reaches this size
            
            // Function to send buffered audio data
            this.sendAudioBuffer = () => {
                if (audioBuffer.length === 0) return;
                
                // Combine all buffered audio
                const combinedLength = audioBuffer.reduce((sum, chunk) => sum + chunk.length, 0);
                const combinedData = new Float32Array(combinedLength);
                
                let offset = 0;
                for (const chunk of audioBuffer) {
                    combinedData.set(chunk, offset);
                    offset += chunk.length;
                }
                
                // Convert float32 to int16
                const int16Data = new Int16Array(combinedData.length);
                for (let i = 0; i < combinedData.length; i++) {
                    int16Data[i] = Math.max(-32768, Math.min(32767, combinedData[i] * 32768));
                }
                
                // Convert to base64 and send
                try {
                    const base64Audio = btoa(String.fromCharCode.apply(null, new Uint8Array(int16Data.buffer)));
                    window.socketClient.emit('audio_data', { audio: base64Audio });
                } catch (error) {
                    console.error('Error sending audio data:', error);
                }
                
                // Clear buffer
                audioBuffer = [];
                bufferSize = 0;
            };
            
            // Advanced voice activity detection variables
            let silenceCount = 0;
            let speechCount = 0;
            const silenceThreshold = 10; // frames of silence before considering it quiet
            let lastAudioLevel = 0;
            let audioLevelSmoothed = 0;
            
            this.processor.onaudioprocess = (event) => {
                if (this.isRecording) {
                    const inputData = event.inputBuffer.getChannelData(0);
                    
                    // Advanced audio analysis for better voice detection
                    let audioLevel = 0;
                    let rmsLevel = 0; // Root Mean Square for better level detection
                    let peakLevel = 0;
                    
                    // Calculate RMS and peak levels
                    for (let i = 0; i < inputData.length; i++) {
                        const sample = inputData[i];
                        const absLevel = Math.abs(sample);
                        peakLevel = Math.max(peakLevel, absLevel);
                        rmsLevel += sample * sample;
                    }
                    
                    rmsLevel = Math.sqrt(rmsLevel / inputData.length);
                    
                    // Smooth the audio level to reduce noise sensitivity
                    audioLevelSmoothed = 0.9 * audioLevelSmoothed + 0.1 * rmsLevel;
                    
                    // Dynamic threshold based on recent audio levels
                    const baseThreshold = 0.002; // Lower base threshold for quiet speech
                    const dynamicThreshold = Math.max(baseThreshold, audioLevelSmoothed * 0.3);
                    
                    // Improved voice activity detection
                    let hasAudio = false;
                    if (rmsLevel > dynamicThreshold && peakLevel > 0.005) {
                        hasAudio = true;
                        speechCount++;
                        silenceCount = 0;
                    } else {
                        silenceCount++;
                        if (speechCount > 0) speechCount--;
                    }
                    
                    // Only consider it actual speech if we have consistent audio
                    const hasSpeech = speechCount > 2 && silenceCount < silenceThreshold;
                    
                    // Always add to buffer
                    audioBuffer.push(new Float32Array(inputData));
                    bufferSize += inputData.length;
                    
                    // Optimized sending logic for medical conversations
                    const shouldSend = (hasSpeech && bufferSize >= 1024) ||  // Send when we detect consistent speech
                                     (hasAudio && bufferSize >= 2048) ||     // Send for any audio above threshold
                                     bufferSize >= maxBufferSize;            // Always send when buffer is full
                    
                    if (shouldSend) {
                        // Show audio indicator when transmitting (with better feedback)
                        if (hasSpeech) {
                            const audioIndicator = document.getElementById('audioIndicator');
                            audioIndicator.classList.add('active');
                            // Clear any existing timeout
                            if (this.audioIndicatorTimeout) {
                                clearTimeout(this.audioIndicatorTimeout);
                            }
                            // Set a longer timeout to prevent rapid flickering
                            this.audioIndicatorTimeout = setTimeout(() => {
                                audioIndicator.classList.remove('active');
                            }, 2000); // Even longer for medical conversations
                        }
                        this.sendAudioBuffer();
                    }
                }
            };
            
            // Send remaining buffer regularly to catch slow speech
            this.bufferInterval = setInterval(() => {
                if (this.isRecording && audioBuffer.length > 0) {
                    this.sendAudioBuffer();
                }
            }, 150); // Slightly longer interval for better slow speech capture
            
            // Connect advanced audio chain: source -> highpass -> compressor -> gain -> lowpass -> processor -> destination
            this.source.connect(highPassFilter);
            highPassFilter.connect(compressor);
            compressor.connect(gainNode);
            gainNode.connect(lowPassFilter);
            lowPassFilter.connect(this.processor);
            this.processor.connect(this.audioContext.destination);
            
            // Start transcription on server
            window.socketClient.emit('start_transcription');
            
            // Clear previous session data
            document.getElementById('transcript').innerHTML = '<div class="empty-state">Waiting for speech...</div>';
            document.getElementById('analysisContainer').style.display = 'none';
            
            // Update UI state
            this.isRecording = true;
            window.ui.updateRecordingState(true);
            
            window.ui.updateStatus('Recording started! Speak now...', false);
            
        } catch (error) {
            console.error('Error starting transcription:', error);
            window.ui.updateStatus(`Error: ${error.message}`, true);
        }
    }

    stopTranscription() {
        try {
            // Stop recording
            this.isRecording = false;
            
            // Send any remaining buffered audio
            if (this.sendAudioBuffer) {
                this.sendAudioBuffer();
            }
            
            // Clear buffer interval
            if (this.bufferInterval) {
                clearInterval(this.bufferInterval);
                this.bufferInterval = null;
            }
            
            // Clear audio indicator timeout
            if (this.audioIndicatorTimeout) {
                clearTimeout(this.audioIndicatorTimeout);
                this.audioIndicatorTimeout = null;
            }
            
            // Clean up audio resources
            if (this.processor) {
                this.processor.disconnect();
                this.processor = null;
            }
            
            if (this.source) {
                this.source.disconnect();
                this.source = null;
            }
            
            if (this.audioContext) {
                this.audioContext.close();
                this.audioContext = null;
            }
            
            // Stop transcription on server
            window.socketClient.emit('stop_transcription');
            
            // Update UI state
            window.ui.updateRecordingState(false);
            
            window.ui.updateStatus('Recording stopped', false);
            
        } catch (error) {
            console.error('Error stopping transcription:', error);
            window.ui.updateStatus(`Error stopping: ${error.message}`, true);
        }
    }
}

// Initialize audio recorder
window.audioRecorder = new AudioRecorder(); 