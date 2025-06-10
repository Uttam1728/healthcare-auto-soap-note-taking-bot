// UI handling and display functions
class UIHandler {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
    }

    initializeElements() {
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.status = document.getElementById('status');
        this.transcript = document.getElementById('transcript');
        this.recordingIndicator = document.getElementById('recordingIndicator');
        this.audioIndicator = document.getElementById('audioIndicator');
    }

    setupEventListeners() {
        // Handle page unload
        window.addEventListener('beforeunload', () => {
            if (window.audioRecorder && window.audioRecorder.isRecording) {
                window.audioRecorder.stopTranscription();
            }
        });
        
        // Check compatibility on page load
        window.addEventListener('load', () => {
            const compatibilityError = window.audioRecorder.checkBrowserCompatibility();
            if (compatibilityError) {
                this.updateStatus(compatibilityError, true);
                this.startBtn.disabled = true;
            }
        });
    }

    updateStatus(message, isError = false) {
        this.status.textContent = message;
        this.status.className = isError ? 'status error' : 'status';
    }

    updateRecordingState(isRecording) {
        if (isRecording) {
            this.startBtn.disabled = true;
            this.startBtn.className = 'recording';
            this.startBtn.innerHTML = '<span class="mic-icon">🔴</span>Recording...';
            this.stopBtn.disabled = false;
            this.recordingIndicator.classList.add('active');
        } else {
            this.startBtn.disabled = false;
            this.startBtn.className = '';
            this.startBtn.innerHTML = '<span class="mic-icon">🎤</span>Start Recording';
            this.stopBtn.disabled = true;
            this.recordingIndicator.classList.remove('active');
            this.audioIndicator.classList.remove('active');
        }
    }

    displayTranscript(data) {
        // Handle both old format (text, isFinal) and new format (data object)
        let text, isFinal, speaker, confidence, timestamp;
        
        if (typeof data === 'string') {
            // Old format - just text and isFinal as separate params
            text = data;
            isFinal = arguments[1];
        } else {
            // New enhanced format
            text = data.text;
            isFinal = data.is_final;
            speaker = data.speaker;
            confidence = data.confidence;
            timestamp = data.timestamp;
        }
        
        if (this.transcript.querySelector('.empty-state')) {
            this.transcript.innerHTML = '';
        }
        
        if (isFinal) {
            // Remove any existing interim text
            const interimElements = this.transcript.querySelectorAll('.interim-text');
            interimElements.forEach(el => el.remove());
            
            // Add enhanced final text with speaker and confidence info
            const finalDiv = document.createElement('div');
            finalDiv.className = 'final-text';
            
            // Add speaker indicator if available
            let displayText = text;
            if (speaker) {
                const speakerSpan = document.createElement('span');
                speakerSpan.className = 'speaker-tag';
                speakerSpan.textContent = speaker;
                finalDiv.appendChild(speakerSpan);
                
                const textSpan = document.createElement('span');
                textSpan.textContent = ` ${displayText}`;
                finalDiv.appendChild(textSpan);
            } else {
                finalDiv.textContent = displayText;
            }
            
            // Add confidence indicator if available
            if (confidence && confidence < 0.8) {
                finalDiv.classList.add('low-confidence');
                finalDiv.title = `Confidence: ${Math.round(confidence * 100)}%`;
            }
            
            this.transcript.appendChild(finalDiv);
        } else {
            // Remove existing interim text and add new one
            const existingInterim = this.transcript.querySelector('.interim-text');
            if (existingInterim) {
                existingInterim.remove();
            }
            
            const interimDiv = document.createElement('div');
            interimDiv.className = 'interim-text';
            
            // Add speaker info to interim text too
            if (speaker) {
                const speakerSpan = document.createElement('span');
                speakerSpan.className = 'speaker-tag interim';
                speakerSpan.textContent = speaker;
                interimDiv.appendChild(speakerSpan);
                
                const textSpan = document.createElement('span');
                textSpan.textContent = ` ${text}`;
                interimDiv.appendChild(textSpan);
            } else {
                interimDiv.textContent = text;
            }
            
            this.transcript.appendChild(interimDiv);
        }
        
        // Scroll to bottom
        this.transcript.scrollTop = this.transcript.scrollHeight;
    }

    formatSoapContent(content) {
        if (!content) return 'Not documented';
        
        // If it's already a string, return it
        if (typeof content === 'string') {
            return content;
        }
        
        // If it's an object, try to format it nicely
        if (typeof content === 'object') {
            if (Array.isArray(content)) {
                return content.join('\n• ');
            } else {
                // Convert object to readable format
                return Object.entries(content)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join('\n');
            }
        }
        
        // Fallback: convert to string
        return String(content);
    }

    displayAnalysis(analysisData) {
        const analysisContainer = document.getElementById('analysisContainer');
        const analysisContent = document.getElementById('analysisContent');
        
        if (analysisData.error) {
            let errorContent = `
                <div class="analysis-section">
                    <h3>⚠️ Analysis Notice</h3>
                    <p style="color: #d32f2f; margin-bottom: 15px;"><strong>${analysisData.error}</strong></p>
            `;
            
            // Add reason if available
            if (analysisData.reason) {
                errorContent += `<p style="color: #666; margin-bottom: 15px;">${analysisData.reason}</p>`;
            }
            
            errorContent += `
                    <button onclick="retryAnalysis()" style="margin: 10px 5px 10px 0; padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        🔄 Retry Analysis
                    </button>
                    <button onclick="testAnalysis()" style="margin: 10px 0; padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        🧪 Test with Sample Data
                    </button>
                    ${analysisData.raw_response ? `<details style="margin-top: 15px;"><summary>Raw Response (Click to expand)</summary><pre style="white-space: pre-wrap; max-height: 300px; overflow-y: auto; background: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; font-size: 0.85em;">${analysisData.raw_response}</pre></details>` : ''}
                </div>
            `;
            
            // Still show SOAP note structure even for errors
            if (analysisData.soap_note || analysisData.soap_note_with_sources) {
                const soapData = analysisData.soap_note_with_sources || analysisData.soap_note;
                errorContent += this.displaySoapNote(soapData, analysisData.transcript_segments || []);
            }
            
            analysisContent.innerHTML = errorContent;
            analysisContainer.style.display = 'block';
            return;
        }
        
        let html = '';
        
        // Speaker Analysis
        if (analysisData.speaker_analysis) {
            const speakerData = analysisData.speaker_analysis;
            html += `
                <div class="analysis-section">
                    <h3>👥 Speaker Distribution</h3>
                    <div class="speaker-stats">
                        <div class="stat-item doctor">
                            <div class="stat-percentage">${speakerData.doctor_percentage || 50}%</div>
                            <div class="stat-label">Doctor</div>
                        </div>
                        <div class="stat-item patient">
                            <div class="stat-percentage">${speakerData.patient_percentage || 50}%</div>
                            <div class="stat-label">Patient</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Medical Topics
        if (analysisData.medical_topics && analysisData.medical_topics.length > 0) {
            html += `
                <div class="analysis-section">
                    <h3>🏥 Key Medical Topics</h3>
                    <div class="topic-tags">
                        ${analysisData.medical_topics.map(topic => `<span class="topic-tag">${topic}</span>`).join('')}
                    </div>
                </div>
            `;
        }
        
        // Conversation Segments
        if (analysisData.conversation_segments && analysisData.conversation_segments.length > 0) {
            html += `
                <div class="analysis-section">
                    <h3>💬 Conversation Segments</h3>
                    ${analysisData.conversation_segments.map(segment => `
                        <div class="conversation-segment">
                            <span class="segment-speaker">${segment.speaker || 'Unknown'}</span>
                            <span class="segment-type">${segment.type || 'General'}</span>
                            <div style="margin-top: 8px;">${segment.content || 'No content'}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        // Summary
        if (analysisData.summary) {
            html += `
                <div class="analysis-section">
                    <h3>📋 Summary</h3>
                    <div class="summary-text">${analysisData.summary}</div>
                </div>
            `;
        }
        
        // Enhanced SOAP Note with Sources
        if (analysisData.soap_note_with_sources || analysisData.soap_note) {
            const soapData = analysisData.soap_note_with_sources || analysisData.soap_note;
            html += this.displaySoapNote(soapData, analysisData.transcript_segments || []);
        }
        
        if (!html) {
            html = '<div class="analysis-section"><h3>No analysis data available</h3></div>';
        }
        
        analysisContent.innerHTML = html;
        analysisContainer.style.display = 'block';
        
        // Initialize tooltips after content is added
        this.initializeSourceTooltips();
        
        // Scroll to analysis
        analysisContainer.scrollIntoView({ behavior: 'smooth' });
    }

    displaySoapNote(soapData, transcriptSegments) {
        const hasSourceMapping = soapData.subjective && typeof soapData.subjective === 'object' && soapData.subjective.sources;
        
        let soapHtml = `
            <div class="analysis-section">
                <div class="soap-note">
                    <h3>🏥 Clinical SOAP Note ${hasSourceMapping ? '<span class="source-indicator">📍 Hover for sources</span>' : ''}</h3>
        `;
        
        const soapSections = [
            { key: 'subjective', label: 'S - Subjective', class: 'subjective' },
            { key: 'objective', label: 'O - Objective', class: 'objective' },
            { key: 'assessment', label: 'A - Assessment', class: 'assessment' },
            { key: 'plan', label: 'P - Plan', class: 'plan' }
        ];
        
        soapSections.forEach(section => {
            const sectionData = soapData[section.key];
            
            soapHtml += `<div class="soap-section ${section.class}">
                <div class="soap-header ${section.class}">${section.label}</div>
                <div class="soap-content">`;
            
            if (hasSourceMapping && sectionData && typeof sectionData === 'object') {
                // Enhanced format with source mapping
                soapHtml += this.displaySoapSectionWithSources(sectionData, transcriptSegments, section.key);
            } else {
                // Standard format
                const content = typeof sectionData === 'string' ? sectionData : (sectionData?.content || 'Not documented');
                soapHtml += this.formatSoapContent(content);
            }
            
            soapHtml += `</div></div>`;
        });
        
        soapHtml += `</div></div>`;
        return soapHtml;
    }

    displaySoapSectionWithSources(sectionData, transcriptSegments, sectionKey) {
        let html = '';
        
        // Main content with sources
        if (sectionData.content) {
            const mainSourcesHtml = this.formatSourcesForTooltip(sectionData.sources || [], transcriptSegments);
            html += `<div class="soap-content-with-sources" data-sources='${JSON.stringify(sectionData.sources || []).replace(/'/g, '&apos;')}' data-confidence="${sectionData.confidence || 0}">
                ${this.formatSoapContent(sectionData.content)}
                ${sectionData.confidence ? `<span class="confidence-badge">${sectionData.confidence}%</span>` : ''}
            </div>`;
        }
        
        // Sub-components if available
        if (sectionData.sub_components) {
            html += '<div class="soap-sub-components">';
            Object.entries(sectionData.sub_components).forEach(([key, subComponent]) => {
                if (subComponent.content) {
                    const subSourcesHtml = this.formatSourcesForTooltip(subComponent.sources || [], transcriptSegments);
                    html += `
                        <div class="soap-sub-component">
                            <div class="sub-component-label">${this.formatSubComponentLabel(key)}:</div>
                            <div class="soap-content-with-sources" data-sources='${JSON.stringify(subComponent.sources || []).replace(/'/g, '&apos;')}' data-confidence="${subComponent.confidence || 0}">
                                ${this.formatSoapContent(subComponent.content)}
                                ${subComponent.confidence ? `<small class="confidence-badge">${subComponent.confidence}%</small>` : ''}
                            </div>
                        </div>
                    `;
                }
            });
            html += '</div>';
        }
        
        return html || 'Not documented';
    }

    formatSourcesForTooltip(sources, transcriptSegments) {
        if (!sources || sources.length === 0) return '';
        
        return sources.map(source => {
            const excerpts = source.segment_ids ? 
                source.segment_ids.map(id => {
                    const segment = transcriptSegments.find(seg => seg.id === id);
                    return segment ? segment.text : `[Segment ${id}]`;
                }).join(' ... ') : source.excerpt;
            
            return `<div class="source-item">
                <div class="source-excerpt">"${excerpts}"</div>
                <div class="source-reasoning">${source.reasoning}</div>
            </div>`;
        }).join('');
    }

    formatSubComponentLabel(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    initializeSourceTooltips() {
        const elementsWithSources = document.querySelectorAll('.soap-content-with-sources');
        
        elementsWithSources.forEach(element => {
            const sources = JSON.parse(element.getAttribute('data-sources') || '[]');
            const confidence = element.getAttribute('data-confidence') || 0;
            
            if (sources.length > 0) {
                element.classList.add('has-sources');
                
                element.addEventListener('mouseenter', (e) => {
                    this.showSourceTooltip(e, sources, confidence);
                });
                
                element.addEventListener('mouseleave', (e) => {
                    this.hideSourceTooltip();
                });
                
                element.addEventListener('mousemove', (e) => {
                    this.updateTooltipPosition(e);
                });
            }
        });
    }

    showSourceTooltip(event, sources, confidence) {
        const tooltip = this.getOrCreateTooltip();
        
        let tooltipContent = `<div class="tooltip-header">Source Evidence (Confidence: ${confidence}%)</div>`;
        
        sources.forEach((source, index) => {
            tooltipContent += `
                <div class="tooltip-source">
                    <div class="tooltip-excerpt">"${source.excerpt}"</div>
                    <div class="tooltip-reasoning">${source.reasoning}</div>
                    ${source.segment_ids ? `<div class="tooltip-segments">Segments: ${source.segment_ids.join(', ')}</div>` : ''}
                </div>
            `;
        });
        
        tooltip.innerHTML = tooltipContent;
        tooltip.style.display = 'block';
        
        this.updateTooltipPosition(event);
    }

    hideSourceTooltip() {
        const tooltip = document.getElementById('source-tooltip');
        if (tooltip) {
            tooltip.style.display = 'none';
        }
    }

    updateTooltipPosition(event) {
        const tooltip = document.getElementById('source-tooltip');
        if (!tooltip || tooltip.style.display === 'none') return;
        
        // First set initial position to measure dimensions
        tooltip.style.left = '0px';
        tooltip.style.top = '0px';
        
        const tooltipRect = tooltip.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        let left = event.clientX + 12;
        let top = event.clientY + 12;
        
        // Adjust horizontal position if tooltip would go off screen
        if (left + tooltipRect.width > viewportWidth - 20) {
            left = event.clientX - tooltipRect.width - 12;
        }
        
        // Adjust vertical position if tooltip would go off screen
        if (top + tooltipRect.height > viewportHeight - 20) {
            top = event.clientY - tooltipRect.height - 12;
        }
        
        // Ensure tooltip doesn't go off the left or top edge
        left = Math.max(10, left);
        top = Math.max(10, top);
        
        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    }

    getOrCreateTooltip() {
        let tooltip = document.getElementById('source-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'source-tooltip';
            tooltip.className = 'source-tooltip';
            document.body.appendChild(tooltip);
        }
        return tooltip;
    }
}

// Initialize UI handler
window.ui = new UIHandler();

// Global functions for button handlers
function startTranscription() {
    window.audioRecorder.startTranscription();
}

function stopTranscription() {
    window.audioRecorder.stopTranscription();
}

// Retry analysis function
function retryAnalysis() {
    window.ui.updateStatus('Retrying analysis...', false);
    window.socketClient.emit('retry_analysis');
}

// Test analysis function
function testAnalysis() {
    window.ui.updateStatus('Testing with sample data...', false);
    window.socketClient.emit('test_analysis');
} 