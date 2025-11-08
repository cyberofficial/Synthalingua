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
            
            // Add configuration
            formData.append('model_source', this.modelSource.value);
            formData.append('model_size', this.modelSize.value);
            formData.append('device', this.device.value);
            formData.append('source_language', this.sourceLanguage.value);
            formData.append('target_language', this.targetLanguage.value);
            formData.append('enable_translation', this.enableTranslation.checked);
            
            const bufferSize = document.querySelector('input[name="buffer"]:checked').value;
            formData.append('buffer_seconds', bufferSize);
            
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
                
                this.statusProcessing.textContent = 'Ready to process';
                
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
    
    async startProcessing() {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/api/video/session/${this.sessionId}/start`, {
                method: 'POST'
            });
            
            if (response.ok) {
                this.isProcessing = true;
                this.startProcessingBtn.disabled = true;
                this.pauseProcessingBtn.disabled = false;
                this.statusProcessing.textContent = 'Processing...';
                
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
        
        // Update transcription caption
        if (data.transcription) {
            this.transcriptionCaption.textContent = data.transcription;
            this.transcriptionCaption.style.display = this.showOriginal.checked ? 'block' : 'none';
        } else {
            // Clear transcription if empty
            this.transcriptionCaption.textContent = '';
            this.transcriptionCaption.style.display = 'none';
        }
        
        // Update translation caption
        if (data.translation && this.enableTranslation.checked) {
            this.translationCaption.textContent = data.translation;
            this.translationCaption.style.display = 'block';
        } else if (data.transcription && !this.enableTranslation.checked) {
            // Show transcription if translation is disabled
            this.translationCaption.textContent = data.transcription;
            this.translationCaption.style.display = 'block';
        } else {
            // Clear translation if empty
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
