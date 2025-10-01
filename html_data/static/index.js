function showElementById(id) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.remove("hidden");
    }
}

function hideElementById(id) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.add("hidden");
        element.style.boxShadow = "none"; // Remove box-shadow
    }
}

document.addEventListener("DOMContentLoaded", function() {
    function updateHeaders() {
        fetch("/update-header")
            .then(response => response.text())
            .then(originalText => {
                document.getElementById("header-text").innerText = originalText;
            });

        fetch("/update-translated-header")
            .then(response => response.text())
            .then(translatedText => {
                document.getElementById("translated-header").innerText = translatedText;
            });

        fetch("/update-transcribed-header")
            .then(response => response.text())
            .then(transcribedText => {
                document.getElementById("transcribed-header").innerText = transcribedText;
            });
    }

    // Check for URL parameters
    const params = new URLSearchParams(window.location.search);
    const showOriginal = params.has("showoriginal");
    const showTranslation = params.has("showtranslation");
    const showTranscription = params.has("showtranscription");

    if (showOriginal) {
        showElementById("header-text");
    }
    if (showTranslation) {
        showElementById("translated-header");
    }
    if (showTranscription) {
        showElementById("transcribed-header");
    }
    if (!showOriginal && !showTranslation && !showTranscription) {
        showElementById("header-text");
        showElementById("translated-header");
        showElementById("transcribed-header");
    }

    // Check for dark mode parameter
    const darkModeParam = params.get("darkmode");
    if (darkModeParam && darkModeParam.toLowerCase() === "true") {
        document.body.classList.add("dark-mode");
    }

    setInterval(updateHeaders, 10);

    // Validation functions for security
    function isValidTwitchUsername(username) {
        // Twitch usernames: 3-25 characters, alphanumeric + underscore only
        const twitchPattern = /^[A-Za-z0-9_]{3,25}$/;
        return twitchPattern.test(username);
    }

    function isValidYouTubeId(videoId) {
        // YouTube video IDs are 11 characters: alphanumeric, hyphen, and underscore
        const youtubePattern = /^[a-zA-Z0-9_-]{11}$/;
        return youtubePattern.test(videoId);
    }

    // Update video frame based on URL parameters
    const videoContainer = document.getElementById("video-frame");
    const videoSource = params.get("videosource");
    const videoId = params.get("id");

    if (videoSource && videoId) {
        if (videoSource.toLowerCase() === "twitch") {
            // Validate Twitch username
            if (isValidTwitchUsername(videoId)) {
                videoContainer.src = `https://player.twitch.tv/?channel=${encodeURIComponent(videoId)}&parent=localhost`;
            } else {
                console.error("Invalid Twitch username");
            }
        } else if (videoSource.toLowerCase() === "youtube") {
            // Validate YouTube video ID
            if (isValidYouTubeId(videoId)) {
                videoContainer.src = `https://www.youtube.com/embed/${encodeURIComponent(videoId)}`;
            } else {
                console.error("Invalid YouTube video ID");
            }
        }
        showElementById("video-container");
        showElementById("video-frame");
        hideElementById("nostream"); // Corrected line
    } else {
        hideElementById("video-frame");
        hideElementById("video-container");
        showElementById("nostream"); // Corrected line
    }

    // Check for background color parameter
    const bgColorParam = params.get("bgcolor");
    if (bgColorParam) {
        // Validate and apply background color
        const colorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^[a-zA-Z]+$/;
        if (colorRegex.test(bgColorParam)) {
            document.body.style.backgroundColor = bgColorParam;
        }
    }

    // Check for font family parameter
    const fontFamilyParam = params.get("font") || params.get("fontfamily");
    if (fontFamilyParam) {
        // Apply font family to all text elements
        const headerItems = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
        headerItems.forEach(item => {
            item.style.fontFamily = fontFamilyParam;
        });
    }

    // Check for fontsize parameter
    const fontSizeParam = params.get("fontsize");
    if (fontSizeParam) {
      // Validate font size (e.g., ensure it's a number)
      const fontSize = parseFloat(fontSizeParam);
      if (!isNaN(fontSize) && fontSize > 0) {
        // Update font size of header items
        const headerItems = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
        headerItems.forEach(item => {
          item.style.fontSize = fontSize + "px";
        });
      }
    }

    // Check for caption background color parameter
    const captionBgParam = params.get("captionbg");
    const captionOpacityParam = params.get("captionopacity");
    
    if (captionBgParam || captionOpacityParam) {
        const bgColor = captionBgParam || '#000000';
        const opacity = captionOpacityParam ? parseFloat(captionOpacityParam) / 100 : 0.5;
        
        // Validate and apply caption background
        const colorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^[a-zA-Z]+$/;
        if (colorRegex.test(bgColor) && opacity >= 0 && opacity <= 1) {
            let rgbaColor;
            if (bgColor.startsWith('#')) {
                const r = parseInt(bgColor.slice(1, 3), 16);
                const g = parseInt(bgColor.slice(3, 5), 16);
                const b = parseInt(bgColor.slice(5, 7), 16);
                rgbaColor = `rgba(${r}, ${g}, ${b}, ${opacity})`;
            } else {
                // Handle named colors by creating temporary element
                const tempDiv = document.createElement('div');
                tempDiv.style.color = bgColor;
                document.body.appendChild(tempDiv);
                const computedColor = getComputedStyle(tempDiv).color;
                document.body.removeChild(tempDiv);
                
                if (computedColor.startsWith('rgb')) {
                    const values = computedColor.match(/\d+/g);
                    rgbaColor = `rgba(${values[0]}, ${values[1]}, ${values[2]}, ${opacity})`;
                } else {
                    rgbaColor = `rgba(0, 0, 0, ${opacity})`;
                }
            }
            
            // Apply to all caption elements
            const captionElements = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
            captionElements.forEach(element => {
                element.style.backgroundColor = rgbaColor;
            });
        }
    }

    // Check for text color parameter
    const textColorParam = params.get("textcolor");
    if (textColorParam) {
        // Validate and apply text color
        const colorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^[a-zA-Z]+$/;
        if (colorRegex.test(textColorParam)) {
            // Apply to all caption text elements
            const captionElements = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
            captionElements.forEach(element => {
                element.style.color = textColorParam;
            });
        }
    }

    // Help box toggle functionality
    const helpBox = document.getElementById("help-box");
    
    function toggleHelp() {
        if (helpBox.classList.contains("hidden")) {
            helpBox.classList.remove("hidden");
            // Initialize the controls with current values when opening
            initializeHelpControls();
        } else {
            helpBox.classList.add("hidden");
        }
    }

    // Helper function to get current caption opacity
    function getCurrentCaptionOpacity() {
        const headerElement = document.querySelector('#header-text');
        const bgColor = getComputedStyle(headerElement).backgroundColor;
        if (bgColor.includes('rgba')) {
            const opacity = parseFloat(bgColor.split(',')[3].replace(')', '').trim());
            return Math.round(opacity * 100);
        }
        return 50; // Default 50%
    }

    // Initialize help box controls with current page settings
    function initializeHelpControls() {
        const currentBg = document.body.style.backgroundColor || '#00FF00';
        const currentFont = document.querySelector('#header-text').style.fontFamily || 'Arial';
        const currentSize = parseInt(document.querySelector('#header-text').style.fontSize) || 18;

        // Set control values
        document.getElementById('bg-color-text').value = currentBg;
        if (currentBg.startsWith('#')) {
            document.getElementById('bg-color-picker').value = currentBg;
        }
        
        // Set font selector or custom input
        const fontSelector = document.getElementById('font-selector');
        const customFontInput = document.getElementById('custom-font');
        if ([...fontSelector.options].some(option => option.value === currentFont)) {
            fontSelector.value = currentFont;
            customFontInput.value = '';
        } else {
            fontSelector.value = '';
            customFontInput.value = currentFont;
        }
        
        document.getElementById('font-size-slider').value = currentSize;
        document.getElementById('font-size-input').value = currentSize;
        document.getElementById('font-size-display').textContent = currentSize + 'px';

        // Initialize caption background controls
        const currentCaptionBg = getComputedStyle(document.querySelector('#header-text')).backgroundColor;
        const currentOpacity = getCurrentCaptionOpacity();
        
        // Set default values if not already set
        if (currentCaptionBg === 'rgba(0, 0, 0, 0.5)' || !currentCaptionBg) {
            document.getElementById('caption-bg-picker').value = '#000000';
            document.getElementById('caption-bg-text').value = '#000000';
        }
        
        document.getElementById('caption-opacity-slider').value = currentOpacity;
        document.getElementById('caption-opacity-input').value = currentOpacity;
        document.getElementById('caption-opacity-display').textContent = currentOpacity + '%';

        // Initialize checkbox states based on current URL parameters
        const params = new URLSearchParams(window.location.search);
        const showOriginal = params.has("showoriginal");
        const showTranslation = params.has("showtranslation");
        const showTranscription = params.has("showtranscription");

        // If no parameters are set, show all by default
        if (!showOriginal && !showTranslation && !showTranscription) {
            document.getElementById('show-original').checked = true;
            document.getElementById('show-translation').checked = true;
            document.getElementById('show-transcription').checked = true;
        } else {
            document.getElementById('show-original').checked = showOriginal;
            document.getElementById('show-translation').checked = showTranslation;
            document.getElementById('show-transcription').checked = showTranscription;
        }

        updateGeneratedURL();
    }

    // Interactive control handlers
    function setupInteractiveControls() {
        const bgColorPicker = document.getElementById('bg-color-picker');
        const bgColorText = document.getElementById('bg-color-text');
        const resetBgBtn = document.getElementById('reset-bg');
        const fontSelector = document.getElementById('font-selector');
        const customFontInput = document.getElementById('custom-font');
        const fontSizeSlider = document.getElementById('font-size-slider');
        const fontSizeInput = document.getElementById('font-size-input');
        const fontSizeDisplay = document.getElementById('font-size-display');
        const copyUrlBtn = document.getElementById('copy-url');

        // Background color controls
        bgColorPicker.addEventListener('input', function() {
            const color = this.value;
            bgColorText.value = color;
            document.body.style.backgroundColor = color;
            updateGeneratedURL();
        });

        bgColorText.addEventListener('input', function() {
            const color = this.value;
            if (color.startsWith('#')) {
                bgColorPicker.value = color;
            }
            document.body.style.backgroundColor = color;
            updateGeneratedURL();
        });

        resetBgBtn.addEventListener('click', function() {
            bgColorPicker.value = '#00FF00';
            bgColorText.value = '#00FF00';
            document.body.style.backgroundColor = '#00FF00';
            updateGeneratedURL();
        });

        // Font controls
        fontSelector.addEventListener('change', function() {
            if (this.value) {
                customFontInput.value = '';
                applyFont(this.value);
            }
        });

        customFontInput.addEventListener('input', function() {
            if (this.value) {
                fontSelector.value = '';
                applyFont(this.value);
            }
        });

        function applyFont(fontFamily) {
            const headerItems = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
            headerItems.forEach(item => {
                item.style.fontFamily = fontFamily;
            });
            updateGeneratedURL();
        }

        // Font size controls
        fontSizeSlider.addEventListener('input', function() {
            const size = this.value;
            fontSizeInput.value = size;
            fontSizeDisplay.textContent = size + 'px';
            applyFontSize(size);
        });

        fontSizeInput.addEventListener('input', function() {
            const size = this.value;
            if (size >= 12 && size <= 200) {
                fontSizeSlider.value = size;
                fontSizeDisplay.textContent = size + 'px';
                applyFontSize(size);
            }
        });

        function applyFontSize(size) {
            const headerItems = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
            headerItems.forEach(item => {
                item.style.fontSize = size + 'px';
            });
            updateGeneratedURL();
        }

        // Copy URL functionality
        copyUrlBtn.addEventListener('click', function() {
            const urlInput = document.getElementById('generated-url');
            urlInput.select();
            document.execCommand('copy');
            
            // Visual feedback
            this.textContent = '✅ Copied!';
            this.classList.add('copied');
            setTimeout(() => {
                this.textContent = '📋 Copy URL';
                this.classList.remove('copied');
            }, 2000);
        });

        // Caption background controls
        const captionBgPicker = document.getElementById('caption-bg-picker');
        const captionBgText = document.getElementById('caption-bg-text');
        const resetCaptionBgBtn = document.getElementById('reset-caption-bg');
        const captionOpacitySlider = document.getElementById('caption-opacity-slider');
        const captionOpacityInput = document.getElementById('caption-opacity-input');
        const captionOpacityDisplay = document.getElementById('caption-opacity-display');

        captionBgPicker.addEventListener('input', function() {
            const color = this.value;
            captionBgText.value = color;
            applyCaptionBackground(color, captionOpacitySlider.value);
        });

        captionBgText.addEventListener('input', function() {
            const color = this.value;
            if (color.startsWith('#')) {
                captionBgPicker.value = color;
            }
            applyCaptionBackground(color, captionOpacitySlider.value);
        });

        resetCaptionBgBtn.addEventListener('click', function() {
            captionBgPicker.value = '#000000';
            captionBgText.value = '#000000';
            applyCaptionBackground('#000000', captionOpacitySlider.value);
        });

        captionOpacitySlider.addEventListener('input', function() {
            const opacity = this.value;
            captionOpacityInput.value = opacity;
            captionOpacityDisplay.textContent = opacity + '%';
            applyCaptionBackground(captionBgText.value, opacity);
        });

        captionOpacityInput.addEventListener('input', function() {
            const opacity = this.value;
            if (opacity >= 0 && opacity <= 100) {
                captionOpacitySlider.value = opacity;
                captionOpacityDisplay.textContent = opacity + '%';
                applyCaptionBackground(captionBgText.value, opacity);
            }
        });

        function applyCaptionBackground(color, opacity) {
            const opacityValue = opacity / 100;
            let rgbaColor;
            
            if (color.startsWith('#')) {
                // Convert hex to rgba
                const r = parseInt(color.slice(1, 3), 16);
                const g = parseInt(color.slice(3, 5), 16);
                const b = parseInt(color.slice(5, 7), 16);
                rgbaColor = `rgba(${r}, ${g}, ${b}, ${opacityValue})`;
            } else if (color.startsWith('rgb')) {
                // Handle existing rgb/rgba values
                if (color.includes('rgba')) {
                    rgbaColor = color.replace(/[\d\.]+\)$/g, opacityValue + ')');
                } else {
                    rgbaColor = color.replace('rgb', 'rgba').replace(')', `, ${opacityValue})`);
                }
            } else {
                // Named colors - convert via temporary element
                const tempDiv = document.createElement('div');
                tempDiv.style.color = color;
                document.body.appendChild(tempDiv);
                const computedColor = getComputedStyle(tempDiv).color;
                document.body.removeChild(tempDiv);
                
                if (computedColor.startsWith('rgb')) {
                    const values = computedColor.match(/\d+/g);
                    rgbaColor = `rgba(${values[0]}, ${values[1]}, ${values[2]}, ${opacityValue})`;
                } else {
                    rgbaColor = `rgba(0, 0, 0, ${opacityValue})`; // Fallback
                }
            }
            
            // Apply to all caption elements
            const captionElements = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
            captionElements.forEach(element => {
                element.style.backgroundColor = rgbaColor;
            });
            
            updateGeneratedURL();
        }

        // Text color controls
        const textColorPicker = document.getElementById('text-color-picker');
        const textColorText = document.getElementById('text-color-text');
        const resetTextColorBtn = document.getElementById('reset-text-color');

        textColorPicker.addEventListener('input', function() {
            const color = this.value;
            textColorText.value = color;
            applyTextColor(color);
        });

        textColorText.addEventListener('input', function() {
            const color = this.value;
            if (color.startsWith('#')) {
                textColorPicker.value = color;
            }
            applyTextColor(color);
        });

        resetTextColorBtn.addEventListener('click', function() {
            textColorPicker.value = '#FFFFFF';
            textColorText.value = '#FFFFFF';
            applyTextColor('#FFFFFF');
        });

        function applyTextColor(color) {
            // Validate color
            const colorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^[a-zA-Z]+$/;
            if (colorRegex.test(color)) {
                // Apply to all caption text elements
                const captionElements = document.querySelectorAll("#header-text, #translated-header, #transcribed-header");
                captionElements.forEach(element => {
                    element.style.color = color;
                });
                
                updateGeneratedURL();
            }
        }

        // Text display checkboxes
        const showOriginalCheckbox = document.getElementById('show-original');
        const showTranslationCheckbox = document.getElementById('show-translation');
        const showTranscriptionCheckbox = document.getElementById('show-transcription');

        showOriginalCheckbox.addEventListener('change', function() {
            toggleTextElement('header-text', this.checked);
            updateGeneratedURL();
        });

        showTranslationCheckbox.addEventListener('change', function() {
            toggleTextElement('translated-header', this.checked);
            updateGeneratedURL();
        });

        showTranscriptionCheckbox.addEventListener('change', function() {
            toggleTextElement('transcribed-header', this.checked);
            updateGeneratedURL();
        });

        function toggleTextElement(elementId, show) {
            const element = document.getElementById(elementId);
            if (element) {
                if (show) {
                    element.classList.remove('hidden');
                } else {
                    element.classList.add('hidden');
                }
            }
        }

        // Collapsible reference section
        const toggleHeader = document.querySelector('.toggle-header');
        const collapsibleSection = document.querySelector('.collapsible');
        
        toggleHeader.addEventListener('click', function() {
            collapsibleSection.classList.toggle('expanded');
        });
    }

    // Generate URL with current parameters
    function updateGeneratedURL() {
        // Only update URL if help box is visible
        const helpBox = document.getElementById("help-box");
        if (!helpBox || helpBox.classList.contains("hidden")) {
            return;
        }

        const baseUrl = window.location.origin + window.location.pathname;
        const params = new URLSearchParams();
        
        // Get current values
        const bgColor = document.body.style.backgroundColor;
        const currentFont = document.querySelector('#header-text').style.fontFamily || 'Arial';
        const currentSize = parseInt(document.querySelector('#header-text').style.fontSize) || 18;
        
        // Add parameters if they differ from defaults
        if (bgColor && bgColor !== 'rgb(0, 255, 0)' && bgColor !== '#00FF00') {
            // Convert rgb to hex if needed
            if (bgColor.startsWith('rgb')) {
                const rgb = bgColor.match(/\d+/g);
                const hex = '#' + ((1 << 24) + (parseInt(rgb[0]) << 16) + (parseInt(rgb[1]) << 8) + parseInt(rgb[2])).toString(16).slice(1);
                params.set('bgcolor', hex);
            } else {
                params.set('bgcolor', bgColor);
            }
        }
        
        if (currentFont && currentFont !== 'Arial') {
            params.set('font', currentFont.replace(/"/g, ''));
        }
        
        if (currentSize && currentSize !== 18) {
            params.set('fontsize', currentSize);
        }

        // Add text display parameters based on checkbox states
        const showOriginalChecked = document.getElementById('show-original').checked;
        const showTranslationChecked = document.getElementById('show-translation').checked;
        const showTranscriptionChecked = document.getElementById('show-transcription').checked;

        // Only add parameters if not all are checked (since showing all is default behavior)
        const allChecked = showOriginalChecked && showTranslationChecked && showTranscriptionChecked;
        if (!allChecked) {
            if (showOriginalChecked) {
                params.set('showoriginal', 'true');
            }
            if (showTranslationChecked) {
                params.set('showtranslation', 'true');
            }
            if (showTranscriptionChecked) {
                params.set('showtranscription', 'true');
            }
        }

        // Add caption background and opacity parameters
        const captionBgElement = document.querySelector('#header-text');
        if (captionBgElement) {
            const captionBgColor = getComputedStyle(captionBgElement).backgroundColor;
            const captionOpacity = document.getElementById('caption-opacity-slider').value;
            
            // Only add if different from defaults (black with 50% opacity)
            if (captionBgColor && captionBgColor !== 'rgba(0, 0, 0, 0.5)') {
                if (captionBgColor.startsWith('rgba')) {
                    const rgbaMatch = captionBgColor.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d\.]+))?\)/);
                    if (rgbaMatch) {
                        const r = rgbaMatch[1];
                        const g = rgbaMatch[2];
                        const b = rgbaMatch[3];
                        const hex = '#' + ((1 << 24) + (parseInt(r) << 16) + (parseInt(g) << 8) + parseInt(b)).toString(16).slice(1);
                        params.set('captionbg', hex);
                    }
                }
            }
            
            if (captionOpacity && captionOpacity !== '50') {
                params.set('captionopacity', captionOpacity);
            }
        }

        // Add text color parameter
        const textColorElement = document.querySelector('#header-text');
        if (textColorElement) {
            const currentTextColor = getComputedStyle(textColorElement).color;
            // Only add if different from default white (#FFFFFF or rgb(255, 255, 255))
            if (currentTextColor && 
                currentTextColor !== 'rgb(255, 255, 255)' && 
                currentTextColor !== '#FFFFFF' &&
                currentTextColor !== 'rgba(255, 255, 255, 1)') {
                
                if (currentTextColor.startsWith('rgb')) {
                    const rgbMatch = currentTextColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
                    if (rgbMatch) {
                        const r = rgbMatch[1];
                        const g = rgbMatch[2];
                        const b = rgbMatch[3];
                        const hex = '#' + ((1 << 24) + (parseInt(r) << 16) + (parseInt(g) << 8) + parseInt(b)).toString(16).slice(1);
                        params.set('textcolor', hex);
                    }
                } else {
                    params.set('textcolor', currentTextColor);
                }
            }
        }

        // Preserve other existing parameters
        const existingParams = new URLSearchParams(window.location.search);
        ['darkmode', 'videosource', 'id'].forEach(param => {
            if (existingParams.has(param)) {
                params.set(param, existingParams.get(param));
            }
        });
        
        const fullUrl = params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
        document.getElementById('generated-url').value = fullUrl;
    }

    // Initialize interactive controls
    setupInteractiveControls();

    // Add keyboard event listener for 'H' key
    document.addEventListener("keydown", function(event) {
        // Check if 'H' or 'h' key is pressed (keyCode 72 or key 'h'/'H')
        if (event.key.toLowerCase() === 'h') {
            event.preventDefault(); // Prevent any default behavior
            toggleHelp();
        }
    });

    // Also allow clicking anywhere on the help box overlay to close it
    helpBox.addEventListener("click", function(event) {
        // Only close if clicked on the overlay (not the content)
        if (event.target === helpBox) {
            helpBox.classList.add("hidden");
        }
    });
});