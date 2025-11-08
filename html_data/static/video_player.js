// Video Player JavaScript - Synthalingua Video Translator

class VideoTranslatorApp {
    constructor() {
        this.sessionId = null;
        this.socket = null;
        this.isProcessing = false;
        this.videoMetadata = null;
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeSocket();
        this.loadAvailableLanguages();
    }
    
    initializeElements() {
        // Video elements
        this.videoPlayer = document.getElementById('video-player');
        this.videoSource = document.getElementById('video-source');
        this.videoInput = document.getElementById('video-input');
        this.uploadArea = document.getElementById('upload-area');
        
        // Caption elements
        this.transcriptionCaption = document.getElementById('transcription-caption');
        this.translationCaption = document.getElementById('translation-caption');
        
        // Control elements
        this.playPauseBtn = document.getElementById('play-pause-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.timelineSlider = document.getElementById('timeline-slider');
        this.timeDisplay = document.getElementById('time-display');
        this.volumeBtn = document.getElementById('volume-btn');
        this.volumeSlider = document.getElementById('volume-slider');
        this.speedSelector = document.getElementById('speed-selector');
        this.fullscreenBtn = document.getElementById('fullscreen-btn');
        
        // Buffer elements
        this.bufferProgress = document.getElementById('buffer-progress');
        this.bufferText = document.getElementById('buffer-text');
        
        // Settings elements
        this.sourceLanguage = document.getElementById('source-language');
        this.targetLanguage = document.getElementById('target-language');
        this.enableTranslation = document.getElementById('enable-translation');
        this.showOriginal = document.getElementById('show-original');
        this.modelSource = document.getElementById('model-source');
        this.modelSize = document.getElementById('model-size');
        this.device = document.getElementById('device');
        this.fontSizeInput = document.getElementById('font-size');
        this.fontSizeValue = document.getElementById('font-size-value');
        this.textColor = document.getElementById('text-color');
        this.bgColor = document.getElementById('bg-color');
        this.bgOpacity = document.getElementById('bg-opacity');
        this.bgOpacityValue = document.getElementById('bg-opacity-value');
        this.captionPosition = document.getElementById('caption-position');
        
        // Silence detection elements
        this.enableSilenceDetection = document.getElementById('enable-silence-detection');
        this.silenceThreshold = document.getElementById('silence-threshold');
        this.silenceThresholdValue = document.getElementById('silence-threshold-value');
        this.minSilenceDuration = document.getElementById('min-silence-duration');
        this.minSilenceDurationValue = document.getElementById('min-silence-duration-value');
        this.minSpeechDuration = document.getElementById('min-speech-duration');
        this.minSpeechDurationValue = document.getElementById('min-speech-duration-value');
        
        // Button elements
        this.startProcessingBtn = document.getElementById('start-processing-btn');
        this.pauseProcessingBtn = document.getElementById('pause-processing-btn');
        this.exportBtn = document.getElementById('export-btn');
        
        // Status elements
        this.statusTime = document.getElementById('status-time');
        this.statusProcessing = document.getElementById('status-processing');
        this.statusLanguage = document.getElementById('status-language');
        this.statusProgress = document.getElementById('status-progress');
        
        // Other elements
        this.videoInfo = document.getElementById('video-info');
        this.loadingOverlay = document.getElementById('loading-overlay');
    }
    
    setupEventListeners() {
        // Upload
        this.uploadArea.addEventListener('click', () => this.videoInput.click());
        this.videoInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
        
        // Video player
        this.videoPlayer.addEventListener('timeupdate', () => this.updatePlaybackPosition());
        this.videoPlayer.addEventListener('loadedmetadata', () => this.onVideoLoaded());
        this.videoPlayer.addEventListener('ended', () => this.onVideoEnded());
        
        // Controls
        this.playPauseBtn.addEventListener('click', () => this.togglePlayPause());
        this.stopBtn.addEventListener('click', () => this.stopPlayback());
        this.timelineSlider.addEventListener('input', (e) => this.handleSeek(e));
        this.volumeSlider.addEventListener('input', (e) => this.handleVolumeChange(e));
        this.speedSelector.addEventListener('change', (e) => this.handleSpeedChange(e));
        this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        
        // Settings
        this.fontSizeInput.addEventListener('input', (e) => this.updateCaptionStyle());
        this.textColor.addEventListener('input', (e) => this.updateCaptionStyle());
        this.bgColor.addEventListener('input', (e) => this.updateCaptionStyle());
        this.bgOpacity.addEventListener('input', (e) => this.updateCaptionStyle());
        this.captionPosition.addEventListener('change', (e) => this.updateCaptionStyle());
        this.showOriginal.addEventListener('change', (e) => this.updateCaptionVisibility());
        
        // Silence detection sliders
        this.silenceThreshold.addEventListener('input', (e) => {
            this.silenceThresholdValue.textContent = `${e.target.value} dB`;
        });
        this.minSilenceDuration.addEventListener('input', (e) => {
            this.minSilenceDurationValue.textContent = `${e.target.value} s`;
        });
        this.minSpeechDuration.addEventListener('input', (e) => {
            this.minSpeechDurationValue.textContent = `${e.target.value} s`;
        });
        
        // Buttons
        this.startProcessingBtn.addEventListener('click', () => this.startProcessing());
        this.pauseProcessingBtn.addEventListener('click', () => this.togglePauseProcessing());
        this.exportBtn.addEventListener('click', () => this.exportCaptions());
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
        });
        
        this.socket.on('caption_update', (data) => {
            console.log('Caption update received:', data);
            this.updateCaptions(data);
        });
        
        this.socket.on('error', (data) => {
            console.error('Socket error:', data);
            this.showError(data.message);
        });
    }
    
    async loadAvailableLanguages() {
        try {
            const response = await fetch('/api/video/languages');
            const data = await response.json();
            
            if (data.success && data.languages) {
                this.populateLanguageDropdowns(data.languages);
            } else {
                console.error('Failed to load languages:', data);
            }
        } catch (error) {
            console.error('Error loading languages:', error);
        }
    }
    
    populateLanguageDropdowns(languages) {
        // Clear existing options except placeholders
        this.sourceLanguage.innerHTML = '';
        this.targetLanguage.innerHTML = '';
        
        // Populate source language (includes Auto-detect)
        languages.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.code;
            option.textContent = lang.name;
            this.sourceLanguage.appendChild(option);
        });
        
        // Populate target language (exclude Auto-detect)
        languages.forEach(lang => {
            if (lang.code !== 'auto') {
                const option = document.createElement('option');
                option.value = lang.code;
                option.textContent = lang.name;
                // Set English as default target
                if (lang.code === 'en') {
                    option.selected = true;
                }
                this.targetLanguage.appendChild(option);
            }
        });
        
        console.log(`Loaded ${languages.length} languages`);
    }
    
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        await this.uploadVideo(file);
    }
    
    handleDragOver(event) {
        event.preventDefault();
        this.uploadArea.style.borderColor = '#00D4FF';
    }
    
    async handleFileDrop(event) {
        event.preventDefault();
        this.uploadArea.style.borderColor = 'rgba(0, 212, 255, 0.5)';
        
        const file = event.dataTransfer.files[0];
        if (!file) return;
        
        await this.uploadVideo(file);
    }
    
    async uploadVideo(file) {
        this.showLoading('Uploading video...');
        
        try {
            const formData = new FormData();
            formData.append('video', file);
            
            const response = await fetch('/api/video/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.sessionId = data.session_id;
                this.videoMetadata = data.metadata;
                
                // Join WebSocket room
                this.socket.emit('join_video_session', { session_id: this.sessionId });
                
                // Set video source
                this.videoSource.src = `/api/video/session/${this.sessionId}/video`;
                this.videoPlayer.load();
                
                // Update UI
                this.displayVideoInfo(data);
                this.startProcessingBtn.disabled = false;
                this.exportBtn.disabled = false;
                
                this.statusProcessing.textContent = 'Configure settings and click Start Processing';
                
                this.hideLoading();
            } else {
                throw new Error(data.error || 'Upload failed');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Failed to upload video: ' + error.message);
            this.hideLoading();
        }
    }
    
    displayVideoInfo(data) {
        document.getElementById('info-filename').textContent = data.filename;
        document.getElementById('info-duration').textContent = this.formatTime(data.metadata.duration);
        document.getElementById('info-resolution').textContent = 
            `${data.metadata.width}x${data.metadata.height}`;
        document.getElementById('info-fps').textContent = 
            data.metadata.fps ? `${data.metadata.fps} fps` : 'Unknown';
        
        this.videoInfo.style.display = 'block';
        this.uploadArea.style.display = 'none';
    }
    
    displayConfiguration() {
        const configSection = document.getElementById('current-config-section');
        const modelText = `${this.currentConfig.model_source}/${this.currentConfig.model_size}`;
        const langText = this.currentConfig.source_language === 'auto' ? 
            `Auto → ${this.currentConfig.target_language}` : 
            `${this.currentConfig.source_language} → ${this.currentConfig.target_language}`;
        
        document.getElementById('config-model').textContent = modelText;
        document.getElementById('config-device').textContent = this.currentConfig.device;
        document.getElementById('config-languages').textContent = langText;
        document.getElementById('config-buffer').textContent = `${this.currentConfig.buffer_seconds}s`;
        
        configSection.style.display = 'block';
    }
    
    async startProcessing() {
        if (!this.sessionId) return;
        
        try {
            // Read current configuration from UI
            const modelSource = this.modelSource.value;
            const modelSize = this.modelSize.value;
            const device = this.device.value;
            const sourceLang = this.sourceLanguage.value || 'auto';
            const targetLang = this.targetLanguage.value;
            const enableTranslation = this.enableTranslation.checked;
            const bufferSize = document.querySelector('input[name="buffer"]:checked').value;
            
            // Silence detection settings
            const enableSilenceDetection = this.enableSilenceDetection.checked;
            const silenceThreshold = parseFloat(this.silenceThreshold.value);
            const minSilenceDuration = parseFloat(this.minSilenceDuration.value);
            const minSpeechDuration = parseFloat(this.minSpeechDuration.value);
            
            // Debug: Log configuration being sent
            console.log('📋 Starting processing with configuration:', {
                model_source: modelSource,
                model_size: modelSize,
                device: device,
                source_language: sourceLang,
                target_language: targetLang,
                enable_translation: enableTranslation,
                buffer_seconds: bufferSize,
                silence_detection: {
                    enabled: enableSilenceDetection,
                    threshold_db: silenceThreshold,
                    min_silence_duration: minSilenceDuration,
                    min_speech_duration: minSpeechDuration
                }
            });
            
            // Store configuration for display
            this.currentConfig = {
                model_source: modelSource,
                model_size: modelSize,
                device: device,
                source_language: sourceLang,
                target_language: targetLang,
                buffer_seconds: bufferSize
            };
            
            // Send configuration with start request
            const response = await fetch(`/api/video/session/${this.sessionId}/start`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model_source: modelSource,
                    model_size: modelSize,
                    device: device,
                    source_language: sourceLang,
                    target_language: targetLang,
                    enable_translation: enableTranslation,
                    buffer_seconds: parseInt(bufferSize),
                    enable_silence_detection: enableSilenceDetection,
                    silence_threshold_db: silenceThreshold,
                    min_silence_duration: minSilenceDuration,
                    min_speech_duration: minSpeechDuration
                })
            });
            
            if (response.ok) {
                this.isProcessing = true;
                this.startProcessingBtn.disabled = true;
                this.pauseProcessingBtn.disabled = false;
                this.statusProcessing.textContent = 'Processing...';
                
                // Display configuration
                this.displayConfiguration();
                
                // Start polling for status updates
                this.startStatusPolling();
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Failed to start processing');
            }
            
        } catch (error) {
            console.error('Start processing error:', error);
            this.showError('Failed to start processing: ' + error.message);
        }
    }
    
    async togglePauseProcessing() {
        if (!this.sessionId) return;
        
        try {
            const endpoint = this.isProcessing ? 'pause' : 'resume';
            const response = await fetch(`/api/video/session/${this.sessionId}/${endpoint}`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.isProcessing = !this.isProcessing;
                this.pauseProcessingBtn.textContent = this.isProcessing ? '⏸️ PAUSE' : '▶️ RESUME';
                this.statusProcessing.textContent = this.isProcessing ? 'Processing...' : 'Paused';
            }
            
        } catch (error) {
            console.error('Toggle pause error:', error);
        }
    }
    
    startStatusPolling() {
        this.statusInterval = setInterval(async () => {
            if (!this.sessionId) return;
            
            try {
                const response = await fetch(`/api/video/session/${this.sessionId}/status`);
                const status = await response.json();
                
                this.updateStatus(status);
                
            } catch (error) {
                console.error('Status polling error:', error);
            }
        }, 1000);
    }
    
    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }
    
    updateStatus(status) {
        // Update progress
        if (status.progress) {
            this.statusProgress.textContent = `${status.progress.progress_pct}%`;
        }
        
        // Update buffer
        if (status.buffer && status.buffer.buffer_status) {
            const bufferStatus = status.buffer.buffer_status;
            this.bufferProgress.style.width = `${bufferStatus.buffer_pct}%`;
            this.bufferText.textContent = `Buffer: ${bufferStatus.seconds_buffered}s ahead`;
        }
        
        // Update language indicator
        if (status.transcription_stats) {
            const lang = status.transcription_stats.model_source;
            this.statusLanguage.textContent = `${lang} → ${this.targetLanguage.value}`;
        }
    }
    
    onVideoLoaded() {
        if (this.videoPlayer.duration) {
            this.timelineSlider.max = this.videoPlayer.duration;
        }
    }
    
    togglePlayPause() {
        if (this.videoPlayer.paused) {
            this.videoPlayer.play();
            this.playPauseBtn.querySelector('.icon').textContent = '⏸';
        } else {
            this.videoPlayer.pause();
            this.playPauseBtn.querySelector('.icon').textContent = '▶';
        }
    }
    
    stopPlayback() {
        this.videoPlayer.pause();
        this.videoPlayer.currentTime = 0;
        this.playPauseBtn.querySelector('.icon').textContent = '▶';
    }
    
    updatePlaybackPosition() {
        const current = this.videoPlayer.currentTime;
        const duration = this.videoPlayer.duration;
        
        // Update timeline
        this.timelineSlider.value = current;
        this.timeDisplay.textContent = `${this.formatTime(current)} / ${this.formatTime(duration)}`;
        this.statusTime.textContent = this.timeDisplay.textContent;
        
        // Update captions via WebSocket
        if (this.sessionId) {
            this.socket.emit('update_playback', {
                session_id: this.sessionId,
                timestamp: current
            });
        }
    }
    
    handleSeek(event) {
        const newTime = parseFloat(event.target.value);
        this.videoPlayer.currentTime = newTime;
        
        // Notify backend about seek
        if (this.sessionId) {
            fetch(`/api/video/session/${this.sessionId}/seek`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ timestamp: newTime })
            });
        }
    }
    
    handleVolumeChange(event) {
        this.videoPlayer.volume = event.target.value / 100;
    }
    
    handleSpeedChange(event) {
        this.videoPlayer.playbackRate = parseFloat(event.target.value);
    }
    
    toggleFullscreen() {
        const container = document.getElementById('video-container');
        
        if (!document.fullscreenElement) {
            container.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }
    
    updateCaptions(data) {
        console.log('Updating captions:', data);
        
        // Handle empty captions during silence periods
        const hasTranscription = data.transcription && data.transcription.trim() !== '';
        const hasTranslation = data.translation && data.translation.trim() !== '';
        
        // Update transcription caption
        if (hasTranscription) {
            this.transcriptionCaption.textContent = data.transcription;
            this.transcriptionCaption.style.display = this.showOriginal.checked ? 'block' : 'none';
        } else {
            // Clear transcription during silence
            this.transcriptionCaption.textContent = '';
            this.transcriptionCaption.style.display = 'none';
        }
        
        // Update translation caption
        if (hasTranslation && this.enableTranslation.checked) {
            // Show translation when available and enabled
            this.translationCaption.textContent = data.translation;
            this.translationCaption.style.display = 'block';
        } else if (hasTranscription && !this.enableTranslation.checked) {
            // Show transcription if translation is disabled but we have text
            this.translationCaption.textContent = data.transcription;
            this.translationCaption.style.display = 'block';
        } else {
            // Clear translation during silence or when no text available
            this.translationCaption.textContent = '';
            this.translationCaption.style.display = 'none';
        }
    }
    
    updateCaptionStyle() {
        const fontSize = this.fontSizeInput.value + 'px';
        const textColor = this.textColor.value;
        const bgColor = this.bgColor.value;
        const bgOpacity = this.bgOpacity.value / 100;
        
        // Convert hex to rgba
        const r = parseInt(bgColor.slice(1, 3), 16);
        const g = parseInt(bgColor.slice(3, 5), 16);
        const b = parseInt(bgColor.slice(5, 7), 16);
        const bgColorRgba = `rgba(${r}, ${g}, ${b}, ${bgOpacity})`;
        
        // Apply styles
        const captions = document.querySelectorAll('.caption');
        captions.forEach(caption => {
            caption.style.fontSize = fontSize;
            caption.style.color = textColor;
            caption.style.background = bgColorRgba;
        });
        
        // Update position
        const position = this.captionPosition.value;
        const overlay = document.querySelector('.caption-overlay');
        
        if (position === 'top') {
            overlay.style.bottom = 'auto';
            overlay.style.top = '80px';
        } else if (position === 'middle') {
            overlay.style.bottom = '50%';
            overlay.style.top = 'auto';
            overlay.style.transform = 'translate(-50%, 50%)';
        } else {
            overlay.style.top = 'auto';
            overlay.style.bottom = '80px';
            overlay.style.transform = 'translateX(-50%)';
        }
        
        // Update value displays
        this.fontSizeValue.textContent = fontSize;
        this.bgOpacityValue.textContent = Math.round(bgOpacity * 100) + '%';
    }
    
    updateCaptionVisibility() {
        this.transcriptionCaption.style.display = this.showOriginal.checked ? 'block' : 'none';
    }
    
    async exportCaptions() {
        if (!this.sessionId) return;
        
        const format = 'srt'; // Could add format selection
        
        try {
            window.location.href = `/api/video/session/${this.sessionId}/export?format=${format}`;
        } catch (error) {
            console.error('Export error:', error);
            this.showError('Failed to export captions');
        }
    }
    
    handleKeyPress(event) {
        // Don't handle if typing in input field
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'SELECT') return;
        
        switch(event.key) {
            case ' ':
                event.preventDefault();
                this.togglePlayPause();
                break;
            case 'f':
            case 'F':
                this.toggleFullscreen();
                break;
            case 'm':
            case 'M':
                this.videoPlayer.muted = !this.videoPlayer.muted;
                break;
            case 'ArrowLeft':
                this.videoPlayer.currentTime -= 5;
                break;
            case 'ArrowRight':
                this.videoPlayer.currentTime += 5;
                break;
            case 'ArrowUp':
                this.videoPlayer.volume = Math.min(1, this.videoPlayer.volume + 0.1);
                break;
            case 'ArrowDown':
                this.videoPlayer.volume = Math.max(0, this.videoPlayer.volume - 0.1);
                break;
        }
    }
    
    onVideoEnded() {
        this.playPauseBtn.querySelector('.icon').textContent = '▶';
        this.statusProcessing.textContent = 'Video ended';
    }
    
    formatTime(seconds) {
        if (!seconds || isNaN(seconds)) return '0:00';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    showLoading(message = 'Loading...') {
        this.loadingOverlay.querySelector('.loading-text').textContent = message;
        this.loadingOverlay.style.display = 'flex';
    }
    
    hideLoading() {
        this.loadingOverlay.style.display = 'none';
    }
    
    showError(message) {
        alert('Error: ' + message); // TODO: Better error display
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VideoTranslatorApp();
});
