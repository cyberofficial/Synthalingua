// Video Player JavaScript - Synthalingua Video Translator

class VideoTranslatorApp {
    constructor() {
        this.sessionId = null;
        this.socket = null;
        this.isProcessing = false;
        this.videoMetadata = null;
        this.lastCaptionUpdate = 0; // Throttle caption updates
        this.currentAudioSource = 'original'; // 'original' or 'vocals'
        this.vocalsAvailable = false; // Track if vocals audio exists
        this.vocalsAudioElement = null; // Separate audio element for vocals WAV
        this.audioSourceInfo = null; // Will be set in initializeElements
        this.audioSourceLabel = null; // Will be set in initializeElements
        
        // Word highlighting (karaoke effect)
        this.currentCaptionData = null; // Stores current caption with timing
        this.captionStartTime = null; // When current caption started
        this.highlightUpdateInterval = null; // Interval for updating word highlights
        
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
        this.audioSourceToggle = document.getElementById('audio-source-toggle');
        
        // Buffer elements
        this.bufferProgress = document.getElementById('buffer-progress');
        this.bufferText = document.getElementById('buffer-text');
        this.timelineBuffered = document.getElementById('timeline-buffered');
        
        // Settings elements
        this.sourceLanguage = document.getElementById('source-language');
        // Target language is always English (hardcoded)
        // Translation is always enabled (no toggle)
        this.modelSource = document.getElementById('model-source');
        this.modelSize = document.getElementById('model-size');
        this.device = document.getElementById('device');
        this.fontSizeInput = document.getElementById('font-size');
        this.fontSizeValue = document.getElementById('font-size-value');
        this.textColor = document.getElementById('text-color');
        this.bgColor = document.getElementById('bg-color');
        this.bgOpacity = document.getElementById('bg-opacity');
        this.bgOpacityValue = document.getElementById('bg-opacity-value');
        this.highlightColor = document.getElementById('highlight-color');
        this.captionPosition = document.getElementById('caption-position');
        
        // Silence detection elements
        this.enableSilenceDetection = document.getElementById('enable-silence-detection');
        this.silenceThreshold = document.getElementById('silence-threshold');
        this.silenceThresholdValue = document.getElementById('silence-threshold-value');
        this.minSilenceDuration = document.getElementById('min-silence-duration');
        this.minSilenceDurationValue = document.getElementById('min-silence-duration-value');
        this.minSpeechDuration = document.getElementById('min-speech-duration');
        this.minSpeechDurationValue = document.getElementById('min-speech-duration-value');
        
        // Vocal isolation elements (Demucs)
        this.enableVocalIsolation = document.getElementById('enable-vocal-isolation');
        this.demucsModel = document.getElementById('demucs-model');
        this.demucsJobs = document.getElementById('demucs-jobs');
        
        // Temperature control elements
        this.enableTemperature = document.getElementById('enable-temperature');
        this.temperatureSlider = document.getElementById('temperature-slider');
        this.temperatureValue = document.getElementById('temperature-value');
        
        // Compression ratio control elements
        this.compressionRatioSlider = document.getElementById('compression-ratio-slider');
        this.compressionRatioValue = document.getElementById('compression-ratio-value');
        this.compressionRatioWarning = document.getElementById('compression-ratio-warning');
        this.compressionRatioWarningText = document.getElementById('compression-ratio-warning-text');
        this.modelSize = document.getElementById('model-size');
        
        // Button elements
        this.startProcessingBtn = document.getElementById('start-processing-btn');
        this.exportBtn = document.getElementById('export-btn');
        
        // Status elements
        this.statusTime = document.getElementById('status-time');
        this.statusProcessing = document.getElementById('status-processing');
        this.statusLanguage = document.getElementById('status-language');
        this.statusSegments = document.getElementById('status-segments');
        this.statusProgress = document.getElementById('status-progress');
        
        // Other elements
        this.videoInfo = document.getElementById('video-info');
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.audioSourceInfo = document.getElementById('audio-source-info');
        this.audioSourceLabel = document.getElementById('audio-source-label');
    }
    
    setupEventListeners() {
        // Upload
        this.uploadArea.addEventListener('click', () => this.videoInput.click());
        this.videoInput.addEventListener('change', (e) => this.handleFileUpload(e));
        this.uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
        
        // Change Video button (allows re-uploading after initial upload)
        const changeVideoBtn = document.getElementById('change-video-btn');
        if (changeVideoBtn) {
            changeVideoBtn.addEventListener('click', () => {
                this.videoInput.click();
            });
        }
        
        // Video player
        this.videoPlayer.addEventListener('timeupdate', () => this.updatePlaybackPosition());
        this.videoPlayer.addEventListener('loadedmetadata', () => this.onVideoLoaded());
        this.videoPlayer.addEventListener('ended', () => this.onVideoEnded());
        this.videoPlayer.addEventListener('seeked', () => this.onSeeked());
        
        // Controls
        this.playPauseBtn.addEventListener('click', () => this.togglePlayPause());
        this.stopBtn.addEventListener('click', () => this.stopPlayback());
        this.timelineSlider.addEventListener('input', (e) => this.handleSeek(e));
        this.volumeSlider.addEventListener('input', (e) => this.handleVolumeChange(e));
        this.speedSelector.addEventListener('change', (e) => this.handleSpeedChange(e));
        this.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        this.audioSourceToggle.addEventListener('click', () => this.toggleAudioSource());
        
        // Sync vocals audio with video playback
        this.videoPlayer.addEventListener('play', () => {
            if (this.currentAudioSource === 'vocals' && this.vocalsAudioElement) {
                this.vocalsAudioElement.play();
            }
        });
        
        this.videoPlayer.addEventListener('pause', () => {
            if (this.vocalsAudioElement) {
                this.vocalsAudioElement.pause();
            }
        });
        
        this.videoPlayer.addEventListener('seeked', () => {
            if (this.vocalsAudioElement) {
                this.vocalsAudioElement.currentTime = this.videoPlayer.currentTime;
            }
        });
        
        this.videoPlayer.addEventListener('ratechange', () => {
            if (this.vocalsAudioElement) {
                this.vocalsAudioElement.playbackRate = this.videoPlayer.playbackRate;
            }
        });
        
        this.volumeSlider.addEventListener('input', () => {
            if (this.vocalsAudioElement) {
                this.vocalsAudioElement.volume = this.videoPlayer.volume;
            }
        });
        
        // Settings
        this.fontSizeInput.addEventListener('input', (e) => this.updateCaptionStyle());
        this.textColor.addEventListener('input', (e) => this.updateCaptionStyle());
        this.bgColor.addEventListener('input', (e) => this.updateCaptionStyle());
        this.bgOpacity.addEventListener('input', (e) => this.updateCaptionStyle());
        this.highlightColor.addEventListener('input', (e) => this.updateCaptionStyle());
        this.captionPosition.addEventListener('change', (e) => this.updateCaptionStyle());
        
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
        
        // Temperature slider
        this.temperatureSlider.addEventListener('input', (e) => {
            const tempValue = (parseInt(e.target.value) / 100).toFixed(2);
            this.temperatureValue.textContent = tempValue;
        });
        
        // Compression ratio slider
        this.compressionRatioSlider.addEventListener('input', (e) => {
            const ratioValue = (parseFloat(e.target.value) / 10).toFixed(1);
            this.compressionRatioValue.textContent = ratioValue;
            this.updateCompressionRatioWarning(parseFloat(ratioValue));
            this.updatePresetButtonStates(parseFloat(ratioValue));
        });
        
        // Compression ratio preset buttons
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const ratio = parseFloat(e.target.dataset.ratio);
                this.compressionRatioSlider.value = ratio * 10;
                this.compressionRatioValue.textContent = ratio.toFixed(1);
                this.updateCompressionRatioWarning(ratio);
                this.updatePresetButtonStates(ratio);
            });
        });
        
        // Model size change listener for compression ratio tips
        this.modelSize.addEventListener('change', () => {
            const currentRatio = parseFloat(this.compressionRatioValue.textContent);
            this.updateCompressionRatioWarning(currentRatio);
        });
        
        // Buttons
        this.startProcessingBtn.addEventListener('click', () => this.startProcessing());
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
        
        this.socket.on('buffer_update', (data) => {
            console.log('Buffer update:', data);
            this.updateBufferStatus(data);
        });
        
        this.socket.on('processing_complete', (data) => {
            console.log('Processing complete:', data);
            this.onProcessingComplete(data);
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
        
        // Populate source language (includes Auto-detect)
        languages.forEach(lang => {
            const option = document.createElement('option');
            option.value = lang.code;
            option.textContent = lang.name;
            this.sourceLanguage.appendChild(option);
        });
        
        // Target language is always English (no dropdown needed)
        
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
        this.showLoading('Processing video, this may take a little bit of time...');
        
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
                // Keep export button disabled until processing is complete
                this.exportBtn.disabled = true;
                
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
        
        // Check if vocals audio is available after upload completes processing
        this.checkVocalsAvailability();
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
            const targetLang = 'en';  // Always translate to English
            const enableTranslation = true;  // Translation always enabled
            
            // Silence detection settings
            const enableSilenceDetection = this.enableSilenceDetection.checked;
            const silenceThreshold = parseFloat(this.silenceThreshold.value);
            const minSilenceDuration = parseFloat(this.minSilenceDuration.value);
            const minSpeechDuration = parseFloat(this.minSpeechDuration.value);
            
            // Vocal isolation settings (Demucs)
            const enableVocalIsolation = this.enableVocalIsolation.checked;
            const demucsModel = this.demucsModel.value;
            const demucsJobs = parseInt(this.demucsJobs.value);
            
            // Temperature settings
            const enableTemperature = this.enableTemperature.checked;
            const temperature = enableTemperature ? parseFloat(this.temperatureSlider.value) / 100 : null;
            
            // Compression ratio threshold
            const compressionRatioThreshold = parseFloat(this.compressionRatioSlider.value) / 10;
            
            // Debug: Log configuration being sent
            console.log(' Starting processing with configuration:', {
                model_source: modelSource,
                model_size: modelSize,
                device: device,
                source_language: sourceLang,
                target_language: targetLang,
                enable_translation: enableTranslation,
                buffer_seconds: 60, // Fixed buffer size (display only)
                silence_detection: {
                    enabled: enableSilenceDetection,
                    threshold_db: silenceThreshold,
                    min_silence_duration: minSilenceDuration,
                    min_speech_duration: minSpeechDuration
                },
                vocal_isolation: {
                    enabled: enableVocalIsolation,
                    model: demucsModel,
                    jobs: demucsJobs
                }
            });
            
            // Store configuration for display
            this.currentConfig = {
                model_source: modelSource,
                model_size: modelSize,
                device: device,
                source_language: sourceLang,
                target_language: targetLang,
                buffer_seconds: 60
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
                    buffer_seconds: 60,
                    enable_silence_detection: enableSilenceDetection,
                    silence_threshold_db: silenceThreshold,
                    min_silence_duration: minSilenceDuration,
                    min_speech_duration: minSpeechDuration,
                    enable_vocal_isolation: enableVocalIsolation,
                    demucs_model: demucsModel,
                    demucs_jobs: demucsJobs,
                    enable_temperature: enableTemperature,
                    temperature: temperature,
                    compression_ratio_threshold: compressionRatioThreshold
                })
            });
            
            if (response.ok) {
                this.isProcessing = true;
                this.startProcessingBtn.disabled = true;
                this.exportBtn.disabled = true;  // Disable export during processing
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
    
    onProcessingComplete(data) {
        console.log('All processing complete:', data);
        
        // Stop polling
        this.stopStatusPolling();
        
        // Update status
        this.isProcessing = false;
        this.statusProcessing.textContent = `Complete (${data.processed_chunks}/${data.total_chunks} chunks)`;
        this.statusProgress.textContent = '100%';
        
        // Update segment count to show final total
        if (data.total_segments !== undefined && data.total_segments !== null) {
            this.statusSegments.textContent = `${data.total_segments}/${data.total_segments} segments`;
        }
        
        // Re-enable the start button so user can process another video
        this.startProcessingBtn.disabled = false;
        this.startProcessingBtn.textContent = '🎬 PROCESS ANOTHER VIDEO';
        
        // Enable export button now that processing is complete
        this.exportBtn.disabled = false;
        
        // Check if vocals audio is available (after Demucs processing)
        this.checkVocalsAvailability();
        
        // Show upload area again so user can load a different video
        this.uploadArea.style.display = 'block';
        this.videoInfo.style.display = 'none';
        
        // Show success message
        const minutes = (data.total_time / 60).toFixed(1);
        this.showSuccess(`Processing completed in ${minutes} minutes! You can now load another video.`);
    }
    
    updateStatus(status) {
        // Update progress
        if (status.progress) {
            this.statusProgress.textContent = `${status.progress.progress_pct}%`;
            
            // Fallback: If we reach 100% and processing flag is still true, re-enable button
            // This handles cases where WebSocket processing_complete event might not fire
            if (status.progress.progress_pct >= 100 && this.isProcessing) {
                console.log('Detected 100% completion via status polling - re-enabling button');
                this.isProcessing = false;
                this.startProcessingBtn.disabled = false;
                this.startProcessingBtn.textContent = '🎬 PROCESS ANOTHER VIDEO';
                
                // Enable export button now that processing is complete
                this.exportBtn.disabled = false;
                
                // Show upload area again so user can load a different video
                this.uploadArea.style.display = 'block';
                this.videoInfo.style.display = 'none';
                
                this.stopStatusPolling();
            }
        }
        
        // Update buffer
        if (status.buffer && status.buffer.buffer_status) {
            const bufferStatus = status.buffer.buffer_status;
            this.bufferProgress.style.width = `${bufferStatus.buffer_pct}%`;
            this.bufferText.textContent = `Buffer: ${bufferStatus.seconds_buffered}s ahead`;
            
            // Update timeline buffered bar (green) to show buffered portion
            if (this.timelineBuffered) {
                this.timelineBuffered.style.width = `${bufferStatus.buffer_pct}%`;
            }
        }
        
        // Update language indicator
        if (status.transcription_stats) {
            const lang = status.transcription_stats.model_source;
            this.statusLanguage.textContent = `${lang} → en`;
        }
        
        // Don't update segment count here - let WebSocket buffer_update events handle it
        // (Status polling doesn't have total_segments info, so it would show incomplete data)
    }
    
    updateBufferStatus(data) {
        // Update buffer display with real-time segment info
        if (data.buffer_status) {
            const bufferStatus = data.buffer_status;
            this.bufferProgress.style.width = `${bufferStatus.buffer_pct}%`;
            this.bufferText.textContent = `Buffer: ${bufferStatus.seconds_buffered.toFixed(1)}s ahead`;
            
            // Update timeline buffered bar (green) to show buffered portion
            if (this.timelineBuffered) {
                this.timelineBuffered.style.width = `${bufferStatus.buffer_pct}%`;
            }
        }
        
        // Update segment counter in status bar
        // During processing: show current count without total (e.g., "42 segments")
        // At completion: show final count with total (e.g., "42/42 segments")
        if (data.segment_num !== undefined && data.segment_num !== null) {
            if (data.total_segments && data.total_segments > 0) {
                // Final update with known total
                this.statusSegments.textContent = `${data.segment_num}/${data.total_segments} segments`;
            } else {
                // Progressive update during processing (don't know final count yet)
                this.statusSegments.textContent = `${data.segment_num} segments`;
            }
        }
    }
    
    onVideoLoaded() {
        if (this.videoPlayer.duration) {
            this.timelineSlider.max = this.videoPlayer.duration;
        }
    }
    
    onSeeked() {
        // Called when seeking completes (user releases slider or clicks timeline)
        // Force caption update even if video is paused
        const current = this.videoPlayer.currentTime;
        if (this.sessionId) {
            console.log(`Seeked to ${current.toFixed(2)}s - requesting captions`);
            this.socket.emit('update_playback', {
                session_id: this.sessionId,
                timestamp: current
            });
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
        
        // Update captions via WebSocket (throttled to avoid spam)
        const now = Date.now();
        if (this.sessionId && (!this.lastCaptionUpdate || now - this.lastCaptionUpdate > 100)) {
            this.lastCaptionUpdate = now;
            this.socket.emit('update_playback', {
                session_id: this.sessionId,
                timestamp: current
            });
        }
    }
    
    handleSeek(event) {
        const newTime = parseFloat(event.target.value);
        this.videoPlayer.currentTime = newTime;
        
        // Immediately request captions for the new position
        if (this.sessionId) {
            this.socket.emit('update_playback', {
                session_id: this.sessionId,
                timestamp: newTime
            });
            
            // Also notify backend about seek for potential priority processing
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
        
        // ALWAYS clear captions first to prevent showing stale content
        if (!hasTranscription && !hasTranslation) {
            // During silence: hide both captions immediately
            this.transcriptionCaption.textContent = '';
            this.transcriptionCaption.style.display = 'none';
            this.translationCaption.innerHTML = '';
            this.translationCaption.style.display = 'none';
            this.currentCaptionData = null;
            this.captionStartTime = null;
            if (this.highlightUpdateInterval) {
                clearInterval(this.highlightUpdateInterval);
                this.highlightUpdateInterval = null;
            }
            return; // Exit early during silence
        }
        
        // Hide transcription caption (we only show English translation)
        this.transcriptionCaption.textContent = '';
        this.transcriptionCaption.style.display = 'none';
        
        // Show translation caption (English only) with word-by-word highlighting
        // Translation is always enabled and target is always English
        const textToShow = hasTranslation ? data.translation : (hasTranscription ? data.transcription : '');
        
        if (textToShow) {
            // Check if this is a NEW caption (different text) or same caption updating
            const isNewCaption = !this.currentCaptionData || this.currentCaptionData.text !== textToShow;
            
            if (isNewCaption) {
                // New caption - reset timing and store data
                this.currentCaptionData = {
                    text: textToShow,
                    duration: data.duration || 3.0  // Default 3 seconds if not provided
                };
                this.captionStartTime = this.videoPlayer.currentTime;
                
                // Initial render
                this.renderCaptionWithHighlight();
                
                // Start highlight update interval
                if (this.highlightUpdateInterval) {
                    clearInterval(this.highlightUpdateInterval);
                }
                this.highlightUpdateInterval = setInterval(() => this.renderCaptionWithHighlight(), 50);
            }
            // If same caption, don't reset timing - let highlight continue naturally
            
            this.translationCaption.style.display = 'block';
        } else {
            // No content available
            this.translationCaption.innerHTML = '';
            this.translationCaption.style.display = 'none';
            this.currentCaptionData = null;
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
    
    renderCaptionWithHighlight() {
        if (!this.currentCaptionData) return;
        
        const text = this.currentCaptionData.text;
        const duration = this.currentCaptionData.duration;
        let elapsedTime = this.videoPlayer.currentTime - this.captionStartTime;
        
        // Clamp elapsed time to valid range [0, duration]
        // This prevents negative values or exceeding caption duration
        elapsedTime = Math.max(0, Math.min(elapsedTime, duration));
        
        // Split text into words (exclude punctuation from word count)
        const words = text.split(/\s+/);
        const wordCount = words.filter(word => word.replace(/[^a-zA-Z0-9]/g, '').length > 0).length;
        
        if (wordCount === 0) {
            this.translationCaption.innerHTML = text;
            return;
        }
        
        // Calculate time per word
        const timePerWord = duration / wordCount;
        
        // Determine which word should be highlighted (clamp to valid range)
        let currentWordIndex = Math.floor(elapsedTime / timePerWord);
        currentWordIndex = Math.max(0, Math.min(currentWordIndex, wordCount - 1));
        
        // Build HTML with highlighted word
        const highlightColor = this.highlightColor.value;
        let html = '';
        let actualWordIndex = -1;
        
        for (let i = 0; i < words.length; i++) {
            const word = words[i];
            const hasLetters = word.replace(/[^a-zA-Z0-9]/g, '').length > 0;
            
            if (hasLetters) {
                actualWordIndex++;
            }
            
            if (hasLetters && actualWordIndex === currentWordIndex) {
                // Highlight current word
                html += `<span style="color: ${highlightColor}; font-weight: bold;">${word}</span>`;
            } else {
                html += word;
            }
            
            // Add space after word (except last word)
            if (i < words.length - 1) {
                html += ' ';
            }
        }
        
        this.translationCaption.innerHTML = html;
    }
    
    updateCaptionVisibility() {
        // Always show only the translation caption (English)
        // Original text is not displayed as we translate directly
        this.transcriptionCaption.style.display = 'none';
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
    
    async checkVocalsAvailability() {
        if (!this.sessionId) return;
        
        console.log(`Checking vocals availability for session: ${this.sessionId}`);
        
        try {
            const response = await fetch(`/api/video/session/${this.sessionId}/audio-sources`);
            const data = await response.json();
            
            console.log('Audio sources response:', data);
            
            if (data.success && data.vocals_available) {
                this.vocalsAvailable = true;
                console.log('✅ Vocals audio available - toggle ready');
            } else {
                this.vocalsAvailable = false;
                console.log('❌ Vocals audio not available - using video audio only');
            }
        } catch (error) {
            console.error('Error checking vocals availability:', error);
            this.vocalsAvailable = false;
        }
    }
    
    async toggleAudioSource() {
        if (!this.sessionId) return;
        
        // Toggle between original (video audio) and vocals (WAV file)
        const newSource = this.currentAudioSource === 'original' ? 'vocals' : 'original';
        
        try {
            // Always check vocals availability fresh when switching to vocals (don't rely on cached flag)
            if (newSource === 'vocals') {
                console.log('🔍 Checking vocals availability before toggle...');
                const response = await fetch(`/api/video/session/${this.sessionId}/audio-sources`);
                const data = await response.json();
                
                if (!data.success || !data.vocals_available) {
                    console.log('❌ Vocals not available yet');
                    alert('Vocals audio not available. Make sure "Enable Vocal Isolation" is checked and processing is complete.');
                    return;
                }
                
                console.log('✅ Vocals available - proceeding with toggle');
            }
            
            // Save current playback state
            const currentTime = this.videoPlayer.currentTime;
            const wasPlaying = !this.videoPlayer.paused;
            
            if (newSource === 'vocals') {
                // Switch to vocals WAV file
                const response = await fetch(`/api/video/session/${this.sessionId}/audio/vocals`);
                
                if (response.ok) {
                    const audioBlob = await response.blob();
                    const audioUrl = URL.createObjectURL(audioBlob);
                    
                    // Create audio element if it doesn't exist
                    if (!this.vocalsAudioElement) {
                        this.vocalsAudioElement = document.createElement('audio');
                        document.body.appendChild(this.vocalsAudioElement);
                    }
                    
                    // Set up vocals audio
                    this.vocalsAudioElement.src = audioUrl;
                    this.vocalsAudioElement.currentTime = currentTime;
                    this.vocalsAudioElement.volume = this.videoPlayer.volume;
                    this.vocalsAudioElement.playbackRate = this.videoPlayer.playbackRate;
                    
                    // Mute video, unmute vocals
                    this.videoPlayer.muted = true;
                    this.vocalsAudioElement.muted = false;
                    
                    // Resume playback if it was playing
                    if (wasPlaying) {
                        await this.videoPlayer.play();
                        await this.vocalsAudioElement.play();
                    }
                    
                    this.currentAudioSource = 'vocals';
                    console.log('Switched to vocals audio');
                } else {
                    console.error('Failed to fetch vocals audio:', response.status);
                }
            } else {
                // Switch back to original video audio
                if (this.vocalsAudioElement) {
                    this.vocalsAudioElement.pause();
                    this.vocalsAudioElement.currentTime = 0;
                }
                
                this.videoPlayer.muted = false;
                this.currentAudioSource = 'original';
                console.log('Switched to original video audio');
            }
            
            this.updateAudioSourceUI();
            
        } catch (error) {
            console.error('Error toggling audio source:', error);
        }
    }
    
    updateAudioSourceUI() {
        // Update button icon and tooltip
        const icon = this.currentAudioSource === 'original' ? '🎵' : '🎶';
        const tooltip = this.currentAudioSource === 'original' ? 
            'Switch to isolated vocals' : 'Switch to original audio';
        
        this.audioSourceToggle.querySelector('.icon').textContent = icon;
        this.audioSourceToggle.title = tooltip;
        
        // Update label
        const label = this.currentAudioSource === 'original' ? 'Original' : 'Vocals Only';
        this.audioSourceLabel.textContent = label;
        
        // Highlight button when using vocals
        if (this.currentAudioSource === 'vocals') {
            this.audioSourceToggle.style.backgroundColor = '#00D4FF';
            this.audioSourceToggle.style.color = '#000';
        } else {
            this.audioSourceToggle.style.backgroundColor = '';
            this.audioSourceToggle.style.color = '';
        }
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
    
    showSuccess(message) {
        // TODO: Better success notification (toast, etc.)
        // For now, use console and could add a success alert if needed
        console.log('Success:', message);
        
        // Optionally show an alert for now
        alert('✅ ' + message);
    }
    
    updateCompressionRatioWarning(ratio) {
        const modelSize = this.modelSize.value;
        let warning = '';
        let showWarning = false;
        
        // Model-specific warnings based on the guide
        if ((modelSize === 'medium' || modelSize === 'large-v2' || modelSize === 'large-v3') && ratio > 2.3) {
            warning = 'Larger models (medium/large) may produce repetitive text with higher thresholds. Consider 2.0-2.2 for non-speech content.';
            showWarning = true;
        } else if ((modelSize === 'tiny' || modelSize === 'base') && ratio < 2.0) {
            warning = 'Smaller models work well with default 2.4. Very low thresholds may reject valid speech.';
            showWarning = true;
        } else if (ratio < 1.9) {
            warning = 'Very strict filtering. May reject valid transcriptions. Use only for music/non-speech content.';
            showWarning = true;
        } else if (ratio > 3.5) {
            warning = 'Very lenient filtering. May allow repetitive hallucinations. Use only for highly technical content.';
            showWarning = true;
        }
        
        if (showWarning) {
            this.compressionRatioWarningText.textContent = warning;
            this.compressionRatioWarning.style.display = 'block';
        } else {
            this.compressionRatioWarning.style.display = 'none';
        }
    }
    
    updatePresetButtonStates(currentRatio) {
        document.querySelectorAll('.preset-btn').forEach(btn => {
            const btnRatio = parseFloat(btn.dataset.ratio);
            if (Math.abs(btnRatio - currentRatio) < 0.05) {
                btn.classList.add('preset-active');
            } else {
                btn.classList.remove('preset-active');
            }
        });
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VideoTranslatorApp();
});
