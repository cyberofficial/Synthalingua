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
        
        // Section redo markers
        this.markerA = null; // Start time in seconds
        this.markerB = null; // End time in seconds
        this.markerAElement = null; // DOM element for A marker
        this.markerBElement = null; // DOM element for B marker
        this.isRedoingSection = false; // Track if section redo is in progress
        
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
        
        // Waveform elements
        this.waveformContainer = document.getElementById('waveform-container');
        this.waveformCanvas = document.getElementById('waveform-canvas');
        this.waveformProgress = document.getElementById('waveform-progress');
        this.waveformLoading = document.getElementById('waveform-loading');
        this.waveformContext = null;
        this.waveformData = null;
        this.isWaveformLoaded = false;
        this.isScrubbingWaveform = false;
        
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
        this.redoSectionBtn = document.getElementById('redo-section-btn');
        this.setMarkerABtn = document.getElementById('set-marker-a-btn');
        this.setMarkerBBtn = document.getElementById('set-marker-b-btn');
        this.clearMarkersBtn = document.getElementById('clear-markers-btn');
        
        // Section redo display elements
        this.sectionRangeDisplay = document.getElementById('section-range-display');
        this.sectionRedoInfo = document.getElementById('section-redo-info');
        this.markerATimeDisplay = document.getElementById('marker-a-time');
        this.markerBTimeDisplay = document.getElementById('marker-b-time');
        this.markerDurationDisplay = document.getElementById('marker-duration');
        
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
        
        // Editor tab elements
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.tabContents = document.querySelectorAll('.tab-content');
        this.captionListContainer = document.getElementById('caption-list-container');
        this.captionListEmpty = document.getElementById('caption-list-empty');
        this.captionList = document.getElementById('caption-list');
        this.refreshCaptionsBtn = document.getElementById('refresh-captions-btn');
        this.addSectionBtn = document.getElementById('add-section-btn');
        this.exportEditedBtn = document.getElementById('export-edited-btn');
        this.clearBatchBtn = document.getElementById('clear-batch-btn');
        this.batchRedoSection = document.getElementById('batch-redo-section');
        this.batchList = document.getElementById('batch-list');
        this.startBatchBtn = document.getElementById('start-batch-btn');
        this.batchCount = document.getElementById('batch-count');
        
        // Add Section form elements
        this.addSectionForm = document.getElementById('add-section-form');
        this.sectionStartInput = document.getElementById('section-start-input');
        this.sectionEndInput = document.getElementById('section-end-input');
        this.addSectionConfirmBtn = document.getElementById('add-section-confirm-btn');
        this.addSectionCancelBtn = document.getElementById('add-section-cancel-btn');
        
        // Batch redo state
        this.batchQueue = []; // Array of {start, end, duration} objects
        this.isBatchProcessing = false;
        this.currentBatchIndex = 0;
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
        
        // Waveform interactions
        this.waveformContainer.addEventListener('click', (e) => this.handleWaveformClick(e));
        this.waveformContainer.addEventListener('mousedown', (e) => this.handleWaveformMouseDown(e));
        this.waveformContainer.addEventListener('mousemove', (e) => this.handleWaveformMouseMove(e));
        this.waveformContainer.addEventListener('mouseup', () => this.handleWaveformMouseUp());
        this.waveformContainer.addEventListener('mouseleave', () => this.handleWaveformMouseUp());
        
        // Redraw waveform on window resize
        window.addEventListener('resize', () => {
            if (this.isWaveformLoaded && this.waveformData) {
                this.drawWaveform();
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
        
        // Section redo buttons
        this.setMarkerABtn.addEventListener('click', () => this.setMarkerA());
        this.setMarkerBBtn.addEventListener('click', () => this.setMarkerB());
        this.clearMarkersBtn.addEventListener('click', () => this.clearMarkers());
        this.redoSectionBtn.addEventListener('click', () => this.redoSection());
        
        // Editor tab listeners
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        this.refreshCaptionsBtn.addEventListener('click', () => this.loadCaptions());
        this.addSectionBtn.addEventListener('click', () => this.showAddSectionForm());
        this.exportEditedBtn.addEventListener('click', () => this.exportCaptions());
        this.clearBatchBtn.addEventListener('click', () => this.clearBatchQueue());
        this.startBatchBtn.addEventListener('click', () => this.startBatchRedo());
        this.addSectionConfirmBtn.addEventListener('click', () => this.confirmAddSection());
        this.addSectionCancelBtn.addEventListener('click', () => this.cancelAddSection());
        
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
        
        this.socket.on('section_updated', (data) => {
            console.log('Section updated:', data);
            // Force caption refresh at current playback position
            this.socket.emit('update_playback', {
                session_id: this.sessionId,
                timestamp: this.videoPlayer.currentTime
            });
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
                
                // Load waveform image (it's generated during session initialization)
                // Add a small delay to allow the backend to finish initialization
                setTimeout(() => {
                    this.loadWaveform().catch(err => {
                        console.warn('Failed to load waveform after start:', err);
                    });
                }, 1000);
                
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
        // This will also trigger waveform loading now that audio exists
        this.checkVocalsAvailability();
        
        // Show upload area again so user can load a different video
        this.uploadArea.style.display = 'block';
        this.videoInfo.style.display = 'none';
        
        // Show success message
        const minutes = (data.total_time / 60).toFixed(1);
        this.showSuccess(`Processing completed in ${minutes} minutes! You can now load another video.`);
        
        // Update marker display to enable redo button if markers are set
        this.updateMarkerDisplay();
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
        
        // Try to load waveform on first buffer update if not already loaded
        // This is a fallback in case the initial load after startProcessing() failed
        if (!this.isWaveformLoaded && this.sessionId) {
            console.log('📊 First buffer update received - attempting to load waveform...');
            this.loadWaveform().catch(err => {
                console.warn('Waveform not ready yet:', err);
            });
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
        
        // Update waveform progress
        if (duration > 0) {
            const progressPercent = (current / duration) * 100;
            this.waveformProgress.style.width = `${progressPercent}%`;
        }
        
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
        // Don't handle if typing in input field or textarea
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'SELECT' || event.target.tagName === 'TEXTAREA') return;
        
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
            
            // Only load waveform if audio is actually available
            if (data.success && (data.vocals_available || data.original_available)) {
                console.log('🎵 Audio available, loading waveform...');
                await this.loadWaveform();
            } else {
                console.log('⏳ Audio not ready yet, waveform will load after processing starts');
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
    
    // Section Redo Methods
    setMarkerA() {
        this.markerA = this.videoPlayer.currentTime;
        this.setMarkerABtn.classList.add('active');
        this.updateMarkerDisplay();
        this.createTimelineMarker('A', this.markerA);
        console.log(`Marker A set at ${this.formatTime(this.markerA)}`);
    }
    
    setMarkerB() {
        this.markerB = this.videoPlayer.currentTime;
        this.setMarkerBBtn.classList.add('active');
        this.updateMarkerDisplay();
        this.createTimelineMarker('B', this.markerB);
        console.log(`Marker B set at ${this.formatTime(this.markerB)}`);
    }
    
    clearMarkers() {
        this.markerA = null;
        this.markerB = null;
        this.setMarkerABtn.classList.remove('active');
        this.setMarkerBBtn.classList.remove('active');
        this.updateMarkerDisplay();
        this.removeTimelineMarkers();
        console.log('Markers cleared');
    }
    
    createTimelineMarker(label, time) {
        // Remove existing marker if it exists
        if (label === 'A' && this.markerAElement) {
            this.markerAElement.remove();
        } else if (label === 'B' && this.markerBElement) {
            this.markerBElement.remove();
        }
        
        // Create new marker element
        const marker = document.createElement('div');
        marker.className = `timeline-marker timeline-marker-${label.toLowerCase()}`;
        marker.dataset.label = label;
        
        // Calculate position as percentage of video duration
        const duration = this.videoPlayer.duration;
        const position = (time / duration) * 100;
        marker.style.left = `${position}%`;
        
        // Add to timeline
        const timeline = document.querySelector('.timeline');
        timeline.appendChild(marker);
        
        // Store reference
        if (label === 'A') {
            this.markerAElement = marker;
        } else {
            this.markerBElement = marker;
        }
    }
    
    removeTimelineMarkers() {
        if (this.markerAElement) {
            this.markerAElement.remove();
            this.markerAElement = null;
        }
        if (this.markerBElement) {
            this.markerBElement.remove();
            this.markerBElement = null;
        }
    }
    
    updateMarkerDisplay() {
        const hasA = this.markerA !== null;
        const hasB = this.markerB !== null;
        
        if (hasA || hasB) {
            this.sectionRedoInfo.style.display = 'block';
        } else {
            this.sectionRedoInfo.style.display = 'none';
        }
        
        // Update time displays
        this.markerATimeDisplay.textContent = hasA ? this.formatTime(this.markerA) : '--:--';
        this.markerBTimeDisplay.textContent = hasB ? this.formatTime(this.markerB) : '--:--';
        
        // Update duration and range display
        if (hasA && hasB) {
            const start = Math.min(this.markerA, this.markerB);
            const end = Math.max(this.markerA, this.markerB);
            const duration = end - start;
            this.markerDurationDisplay.textContent = this.formatTime(duration);
            this.sectionRangeDisplay.textContent = `${this.formatTime(start)} → ${this.formatTime(end)}`;
            
            // Enable redo button only if processing is complete
            this.redoSectionBtn.disabled = this.isProcessing || this.isRedoingSection;
        } else {
            this.markerDurationDisplay.textContent = '--:--';
            this.sectionRangeDisplay.textContent = '';
            this.redoSectionBtn.disabled = true;
        }
    }
    
    async redoSection() {
        if (!this.sessionId || this.markerA === null || this.markerB === null) {
            this.showError('Please set both A and B markers first');
            return;
        }
        
        // Ensure A comes before B
        const startTime = Math.min(this.markerA, this.markerB);
        const endTime = Math.max(this.markerA, this.markerB);
        
        if (endTime - startTime < 0.5) {
            this.showError('Section is too short. Minimum 0.5 seconds required.');
            return;
        }
        
        this.isRedoingSection = true;
        this.redoSectionBtn.disabled = true;
        this.redoSectionBtn.textContent = '🔄 REDOING SECTION...';
        
        try {
            // Read current configuration from UI
            const modelSource = this.modelSource.value;
            const modelSize = this.modelSize.value;
            const device = this.device.value;
            const sourceLang = this.sourceLanguage.value || 'auto';
            const targetLang = 'en';
            
            // Silence detection settings
            const enableSilenceDetection = this.enableSilenceDetection.checked;
            const silenceThreshold = parseFloat(this.silenceThreshold.value);
            const minSilenceDuration = parseFloat(this.minSilenceDuration.value);
            const minSpeechDuration = parseFloat(this.minSpeechDuration.value);
            
            // Temperature settings
            const enableTemperature = this.enableTemperature.checked;
            const temperature = enableTemperature ? parseFloat(this.temperatureSlider.value) / 100 : null;
            
            // Compression ratio threshold
            const compressionRatioThreshold = parseFloat(this.compressionRatioSlider.value) / 10;
            
            console.log(`Redoing section ${this.formatTime(startTime)} → ${this.formatTime(endTime)}`);
            
            const response = await fetch(`/api/video/session/${this.sessionId}/redo_section`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start_time: startTime,
                    end_time: endTime,
                    model_source: modelSource,
                    model_size: modelSize,
                    device: device,
                    source_language: sourceLang,
                    target_language: targetLang,
                    enable_silence_detection: enableSilenceDetection,
                    silence_threshold_db: silenceThreshold,
                    min_silence_duration: minSilenceDuration,
                    min_speech_duration: minSpeechDuration,
                    enable_temperature: enableTemperature,
                    temperature: temperature,
                    compression_ratio_threshold: compressionRatioThreshold
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                const segmentsRemoved = data.segments_removed || 0;
                const segmentsAdded = data.segments_added || 0;
                this.showSuccess(
                    `Section redone successfully!\n` +
                    `Removed: ${segmentsRemoved} segments | Added: ${segmentsAdded} segments\n` +
                    `Language: ${data.language || 'unknown'}`
                );
                
                // Clear markers after successful redo
                this.clearMarkers();
                
                // Force caption refresh at current position
                this.socket.emit('update_playback', {
                    session_id: this.sessionId,
                    timestamp: this.videoPlayer.currentTime
                });
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Failed to redo section');
            }
            
        } catch (error) {
            console.error('Section redo error:', error);
            this.showError('Failed to redo section: ' + error.message);
        } finally {
            this.isRedoingSection = false;
            this.redoSectionBtn.textContent = '🔄 REDO SECTION (A→B)';
            this.updateMarkerDisplay();
        }
    }
    
    // ===== Editor Tab Methods =====
    
    switchTab(tabName) {
        // Update tab buttons
        this.tabBtns.forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Update tab content
        this.tabContents.forEach(content => {
            if (content.id === `${tabName}-tab`) {
                content.classList.add('active');
            } else {
                content.classList.remove('active');
            }
        });
        
        // Load captions when switching to editor tab
        if (tabName === 'editor' && this.sessionId) {
            this.loadCaptions();
        }
    }
    
    async loadCaptions() {
        if (!this.sessionId) {
            console.log('No session ID, cannot load captions');
            return;
        }
        
        try {
            const response = await fetch(`/api/video/session/${this.sessionId}/segments`);
            if (response.ok) {
                const data = await response.json();
                this.displayCaptions(data.segments || []);
            } else {
                console.error('Failed to load captions');
                this.displayCaptions([]);
            }
        } catch (error) {
            console.error('Error loading captions:', error);
            this.displayCaptions([]);
        }
    }
    
    displayCaptions(segments) {
        if (!segments || segments.length === 0) {
            this.captionListEmpty.style.display = 'block';
            this.captionList.style.display = 'none';
            return;
        }
        
        this.captionListEmpty.style.display = 'none';
        this.captionList.style.display = 'flex';
        this.captionList.innerHTML = '';
        
        segments.forEach((segment, index) => {
            const item = this.createCaptionItem(segment, index);
            this.captionList.appendChild(item);
        });
    }
    
    createCaptionItem(segment, index) {
        const item = document.createElement('div');
        item.className = 'caption-item';
        item.dataset.segmentId = index;
        
        const startTime = this.formatTime(segment.start);
        const endTime = this.formatTime(segment.end);
        const duration = (segment.end - segment.start).toFixed(1);
        
        item.innerHTML = `
            <div class="caption-header">
                <span class="caption-time">${startTime} → ${endTime} (${duration}s)</span>
                <div class="caption-actions">
                    <button class="caption-btn edit-btn" data-action="edit">✏️ Edit</button>
                    <button class="caption-btn redo-btn" data-action="redo">🔄 Redo</button>
                    <button class="caption-btn delete-btn" data-action="delete">🗑️ Delete</button>
                </div>
            </div>
            <div class="caption-text-label">📝 Original Text:</div>
            <div class="caption-text">${this.escapeHtml(segment.text || '')}</div>
            <div class="caption-translation-label">🌐 Translation:</div>
            <div class="caption-translation">${this.escapeHtml(segment.translation || '')}</div>
        `;
        
        // Add action listeners
        const editBtn = item.querySelector('[data-action="edit"]');
        const redoBtn = item.querySelector('[data-action="redo"]');
        const deleteBtn = item.querySelector('[data-action="delete"]');
        
        editBtn.addEventListener('click', () => this.editCaption(segment, index, item));
        redoBtn.addEventListener('click', () => this.addToBatch(segment.start, segment.end));
        deleteBtn.addEventListener('click', () => this.deleteCaption(segment, index));
        
        return item;
    }
    
    editCaption(segment, index, itemElement) {
        const textDiv = itemElement.querySelector('.caption-text');
        const translationDiv = itemElement.querySelector('.caption-translation');
        const editBtn = itemElement.querySelector('[data-action="edit"]');
        
        if (editBtn.textContent.includes('Save')) {
            // Save mode
            const textAreas = itemElement.querySelectorAll('.caption-text-editable');
            const textArea = textAreas[0];
            const translationArea = textAreas[1];
            
            const newText = textArea ? textArea.value : segment.text;
            const newTranslation = translationArea ? translationArea.value : segment.translation;
            
            // Update segment
            this.updateSegment(index, newText, newTranslation);
            
            // Restore display
            textDiv.innerHTML = this.escapeHtml(newText);
            translationDiv.innerHTML = this.escapeHtml(newTranslation);
            editBtn.textContent = '✏️ Edit';
        } else {
            // Edit mode
            const currentText = segment.text || '';
            const currentTranslation = segment.translation || '';
            
            textDiv.innerHTML = `<textarea class="caption-text-editable" placeholder="Original transcribed text...">${this.escapeHtml(currentText)}</textarea>`;
            translationDiv.innerHTML = `<textarea class="caption-text-editable" placeholder="English translation...">${this.escapeHtml(currentTranslation)}</textarea>`;
            editBtn.textContent = '💾 Save';
        }
    }
    
    async updateSegment(index, text, translation) {
        if (!this.sessionId) return;
        
        try {
            const response = await fetch(`/api/video/session/${this.sessionId}/segment/${index}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, translation })
            });
            
            if (response.ok) {
                this.showSuccess('Caption updated');
            } else {
                this.showError('Failed to update caption');
            }
        } catch (error) {
            console.error('Error updating segment:', error);
            this.showError('Error updating caption');
        }
    }
    
    async deleteCaption(segment, index) {
        if (!confirm('Delete this caption segment?')) return;
        
        try {
            const response = await fetch(`/api/video/session/${this.sessionId}/segment/${index}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showSuccess('Caption deleted');
                this.loadCaptions(); // Reload list
            } else {
                this.showError('Failed to delete caption');
            }
        } catch (error) {
            console.error('Error deleting segment:', error);
            this.showError('Error deleting caption');
        }
    }
    
    addToBatch(start, end) {
        const duration = (end - start).toFixed(1);
        this.batchQueue.push({ start, end, duration });
        this.updateBatchDisplay();
        this.showSuccess(`Added ${duration}s section to batch queue`);
    }
    
    showAddSectionForm() {
        this.addSectionForm.style.display = 'block';
        // Set default values from current video time if available
        if (this.videoPlayer && this.videoPlayer.currentTime) {
            this.sectionStartInput.value = this.videoPlayer.currentTime.toFixed(1);
            const defaultEnd = Math.min(this.videoPlayer.currentTime + 10, this.videoPlayer.duration || this.videoPlayer.currentTime + 10);
            this.sectionEndInput.value = defaultEnd.toFixed(1);
        }
        this.sectionStartInput.focus();
    }
    
    cancelAddSection() {
        this.addSectionForm.style.display = 'none';
        this.sectionStartInput.value = '';
        this.sectionEndInput.value = '';
    }
    
    confirmAddSection() {
        const startTime = parseFloat(this.sectionStartInput.value);
        const endTime = parseFloat(this.sectionEndInput.value);
        
        // Validation
        if (isNaN(startTime) || isNaN(endTime)) {
            this.showError('Please enter valid numbers for start and end times');
            return;
        }
        
        if (startTime < 0 || endTime < 0) {
            this.showError('Times must be positive numbers');
            return;
        }
        
        if (startTime >= endTime) {
            this.showError('End time must be greater than start time');
            return;
        }
        
        if (this.videoMetadata && endTime > this.videoMetadata.duration) {
            this.showError(`End time exceeds video duration (${this.videoMetadata.duration.toFixed(1)}s)`);
            return;
        }
        
        // Add to batch
        this.addToBatch(startTime, endTime);
        
        // Close form
        this.cancelAddSection();
    }
    
    updateBatchDisplay() {
        this.batchCount.textContent = this.batchQueue.length;
        
        if (this.batchQueue.length === 0) {
            this.batchRedoSection.style.display = 'none';
            return;
        }
        
        this.batchRedoSection.style.display = 'block';
        this.batchList.innerHTML = '';
        
        this.batchQueue.forEach((item, index) => {
            const batchItem = document.createElement('div');
            batchItem.className = 'batch-item';
            batchItem.innerHTML = `
                <div class="batch-item-info">
                    <div class="batch-item-time">${this.formatTime(item.start)} → ${this.formatTime(item.end)}</div>
                    <div class="batch-item-duration">Duration: ${item.duration}s</div>
                </div>
                <button class="batch-item-remove" data-index="${index}">✖️</button>
            `;
            
            const removeBtn = batchItem.querySelector('.batch-item-remove');
            removeBtn.addEventListener('click', () => this.removeFromBatch(index));
            
            this.batchList.appendChild(batchItem);
        });
    }
    
    removeFromBatch(index) {
        this.batchQueue.splice(index, 1);
        this.updateBatchDisplay();
    }
    
    clearBatchQueue() {
        if (this.batchQueue.length === 0) return;
        if (!confirm(`Clear all ${this.batchQueue.length} items from batch queue?`)) return;
        
        this.batchQueue = [];
        this.updateBatchDisplay();
        this.showSuccess('Batch queue cleared');
    }
    
    async startBatchRedo() {
        if (this.batchQueue.length === 0) {
            this.showError('Batch queue is empty');
            return;
        }
        
        if (this.isBatchProcessing) {
            this.showError('Batch processing already in progress');
            return;
        }
        
        this.isBatchProcessing = true;
        this.currentBatchIndex = 0;
        this.startBatchBtn.disabled = true;
        this.startBatchBtn.innerHTML = `⏳ Processing (0/${this.batchQueue.length})`;
        
        try {
            for (let i = 0; i < this.batchQueue.length; i++) {
                this.currentBatchIndex = i;
                const item = this.batchQueue[i];
                
                this.startBatchBtn.innerHTML = `⏳ Processing (${i + 1}/${this.batchQueue.length})`;
                
                // Call redo section API
                await this.redoSectionAPI(item.start, item.end);
                
                // Wait a bit between requests to avoid overload
                await this.sleep(500);
            }
            
            this.showSuccess(`Batch redo complete! Processed ${this.batchQueue.length} sections`);
            this.batchQueue = [];
            this.updateBatchDisplay();
            this.loadCaptions(); // Reload captions
            
        } catch (error) {
            console.error('Batch redo error:', error);
            this.showError('Batch processing failed: ' + error.message);
        } finally {
            this.isBatchProcessing = false;
            this.startBatchBtn.disabled = false;
            this.startBatchBtn.innerHTML = `🚀 START BATCH REDO (<span id="batch-count">${this.batchQueue.length}</span> sections)`;
        }
    }
    
    buildProcessingConfig() {
        // Build configuration object from current UI settings
        // This mirrors the config sent in startProcessing()
        return {
            model_source: this.modelSource.value,
            model_size: this.modelSize.value,
            device: this.device.value,
            source_language: this.sourceLanguage.value || 'auto',
            target_language: 'en',
            enable_translation: true,
            enable_silence_detection: this.enableSilenceDetection.checked,
            silence_threshold_db: parseFloat(this.silenceThreshold.value),
            min_silence_duration: parseFloat(this.minSilenceDuration.value),
            min_speech_duration: parseFloat(this.minSpeechDuration.value),
            enable_vocal_isolation: this.enableVocalIsolation.checked,
            demucs_model: this.demucsModel.value,
            demucs_jobs: parseInt(this.demucsJobs.value),
            enable_temperature: this.enableTemperature.checked,
            temperature: this.enableTemperature.checked ? parseFloat(this.temperatureSlider.value) / 100 : null,
            compression_ratio_threshold: parseFloat(this.compressionRatioSlider.value) / 10
        };
    }
    
    async redoSectionAPI(startTime, endTime) {
        const config = this.buildProcessingConfig();
        
        const response = await fetch(`/api/video/session/${this.sessionId}/redo_section`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_time: startTime,
                end_time: endTime,
                ...config  // Spread config directly into body
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to redo section');
        }
        
        return await response.json();
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showSuccess(message) {
        // Simple success notification (can be enhanced with toast library)
        console.log('SUCCESS:', message);
        // You could use the existing status bar or create a toast notification
        this.statusProcessing.textContent = message;
        this.statusProcessing.style.color = '#4CAF50';
        setTimeout(() => {
            this.statusProcessing.style.color = '';
        }, 3000);
    }
    
    // ===== Waveform Methods =====
    
    async loadWaveform() {
        if (!this.sessionId) {
            console.warn('Cannot load waveform: no session ID');
            return;
        }
        
        console.log('Loading waveform image...');
        this.waveformLoading.style.display = 'block';
        this.isWaveformLoaded = false;
        
        try {
            // Fetch the waveform PNG image from backend
            const waveformResponse = await fetch(`/api/video/session/${this.sessionId}/waveform`);
            
            if (!waveformResponse.ok) {
                throw new Error(`Failed to fetch waveform image (status: ${waveformResponse.status})`);
            }
            
            const waveformBlob = await waveformResponse.blob();
            console.log(`Waveform image blob size: ${waveformBlob.size} bytes`);
            
            // Create an image element to load the waveform
            const img = new Image();
            const imageUrl = URL.createObjectURL(waveformBlob);
            
            // Wait for image to load
            await new Promise((resolve, reject) => {
                img.onload = () => {
                    console.log(`Waveform image loaded: ${img.width}x${img.height}px`);
                    resolve();
                };
                img.onerror = () => reject(new Error('Failed to load waveform image'));
                img.src = imageUrl;
            });
            
            // Draw the image to canvas
            this.drawWaveformImage(img);
            
            // Clean up blob URL
            URL.revokeObjectURL(imageUrl);
            
            this.isWaveformLoaded = true;
            this.waveformLoading.style.display = 'none';
            console.log('✅ Waveform loaded successfully');
            
        } catch (error) {
            console.error('Error loading waveform:', error);
            this.waveformLoading.textContent = 'Waveform unavailable';
            setTimeout(() => {
                this.waveformLoading.style.display = 'none';
            }, 2000);
        }
    }
    
    drawWaveformImage(img) {
        if (!img || !this.waveformCanvas) {
            console.warn('Cannot draw waveform: missing image or canvas');
            return;
        }
        
        const canvas = this.waveformCanvas;
        const ctx = canvas.getContext('2d');
        
        // Set canvas size to match container
        const rect = this.waveformContainer.getBoundingClientRect();
        
        // If container has no size, use default dimensions
        const width = rect.width > 0 ? rect.width : 800;
        const height = rect.height > 0 ? rect.height : 60;
        
        canvas.width = width;
        canvas.height = height;
        
        console.log(`Drawing waveform image to canvas: ${canvas.width}x${canvas.height}`);
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Draw the waveform image scaled to fit canvas
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        console.log('Waveform image drawn to canvas');
    }
    
    handleWaveformClick(event) {
        if (!this.videoPlayer.duration) return;
        
        const rect = this.waveformContainer.getBoundingClientRect();
        const clickX = event.clientX - rect.left;
        const percentage = clickX / rect.width;
        const newTime = percentage * this.videoPlayer.duration;
        
        this.videoPlayer.currentTime = newTime;
        
        // Update captions immediately
        if (this.sessionId) {
            this.socket.emit('update_playback', {
                session_id: this.sessionId,
                timestamp: newTime
            });
        }
    }
    
    handleWaveformMouseDown(event) {
        this.isScrubbingWaveform = true;
        this.handleWaveformClick(event);
    }
    
    handleWaveformMouseMove(event) {
        if (!this.isScrubbingWaveform) return;
        this.handleWaveformClick(event);
    }
    
    handleWaveformMouseUp() {
        this.isScrubbingWaveform = false;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VideoTranslatorApp();
});
