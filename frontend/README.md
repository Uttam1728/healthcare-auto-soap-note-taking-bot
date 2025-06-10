# Frontend Structure

This directory contains the modularized frontend code for the Healthcare SOAP Note Taking Bot.

## Directory Structure

```
frontend/
├── templates/
│   └── index.html          # Main HTML template
├── static/
│   ├── css/
│   │   └── styles.css      # All CSS styles
│   └── js/
│       ├── socket-client.js    # Socket.IO connection and event handling
│       ├── audio-recorder.js   # Audio recording and processing
│       ├── ui-handler.js      # UI handling and display functions
│       └── main.js           # Main initialization file
└── README.md               # This file
```

## Module Overview

### socket-client.js
- Handles Socket.IO connection to the server
- Manages all socket event listeners (connect, disconnect, transcript, analysis, etc.)
- Provides a simple interface for emitting events to the server

### audio-recorder.js
- Manages microphone access and audio recording
- Handles browser compatibility checks
- Implements advanced audio processing with filters and voice activity detection
- Optimized for medical conversation transcription

### ui-handler.js
- Handles all UI interactions and updates
- Manages transcript display with speaker identification
- Renders conversation analysis and SOAP notes
- Implements interactive tooltips for source evidence

### main.js
- Ensures proper module initialization order
- Provides startup logging and error checking
- Sets initial UI state

## Key Features

1. **Modular Architecture**: Each functionality is separated into its own module
2. **Class-based Design**: Uses ES6 classes for better organization
3. **Global Window Objects**: Modules are accessible via `window.socketClient`, `window.audioRecorder`, and `window.ui`
4. **Error Handling**: Comprehensive error handling and user feedback
5. **Cross-browser Compatibility**: Extensive browser compatibility checks
6. **Medical Optimization**: Audio processing optimized for medical conversations

## Usage

The modules are loaded in order in the HTML file:
1. Socket client (for server communication)
2. Audio recorder (for microphone handling)
3. UI handler (for display and interaction)
4. Main initialization (for startup)

All modules are automatically initialized and ready to use once the page loads. 