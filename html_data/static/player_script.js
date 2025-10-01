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

document.body.style.overflow = 'hidden';

document.addEventListener("DOMContentLoaded", function() {
    function updateHeaders() {
        fetch("/update-header")
            .then(response => response.text())
            .then(originalText => {
                document.getElementById("header-text").innerText = originalText;
                document.getElementById("header-text-1").innerText = originalText;
            });

        fetch("/update-translated-header")
            .then(response => response.text())
            .then(translatedText => {
                document.getElementById("translated-header").innerText = translatedText;
                document.getElementById("translated-header-1").innerText = translatedText;
            });

        fetch("/update-transcribed-header")
            .then(response => response.text())
            .then(transcribedText => {
                document.getElementById("transcribed-header").innerText = transcribedText;
                document.getElementById("transcribed-header-1").innerText = transcribedText;
            });
    }

    // Check for URL parameters
    const params = new URLSearchParams(window.location.search);
    const showOriginal = params.has("showoriginal");
    const showTranslation = params.has("showtranslation");
    const showTranscription = params.has("showtranscription");

    if (showOriginal) {
        showElementById("header-text");
        showElementById("header-text-1");
    }
    if (showTranslation) {
        showElementById("translated-header");
        showElementById("translated-header-1");
    }
    if (showTranscription) {
        showElementById("transcribed-header");
        showElementById("transcribed-header-1");
    }
    if (!showOriginal && !showTranslation && !showTranscription) {
        showElementById("header-text");
        showElementById("header-text-1");
        showElementById("translated-header");
        showElementById("translated-header-1");
        showElementById("transcribed-header");
        showElementById("transcribed-header-1");
    }

    // Check for dark mode parameter
    const darkModeParam = params.get("darkmode");
    if (darkModeParam && darkModeParam.toLowerCase() === "true") {
        document.body.classList.add("dark-mode");
    }

    setInterval(updateHeaders, 10);

    // Update video frame based on URL parameters
    const videoContainer = document.getElementById("video-frame");
    const videoSource = params.get("videosource");
    const videoId = params.get("id");
    let parent;

    // Function to extract domain from URL
    function extractDomain(url) {
        let domain;
        // find & remove protocol (http, ftp, etc.) and get domain
        if (url.indexOf("://") > -1) {
            domain = url.split("/")[2];
        } else {
            domain = url.split("/")[0];
        }
        // find & remove port number
        domain = domain.split(":")[0];
        // find & remove "?"
        domain = domain.split("?")[0];

        return domain;
    }

    // Get parent domain from current URL
    const currentUrl = window.location.href;
    parent = extractDomain(currentUrl);

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

    function isValidDomain(domain) {
        // Basic domain validation: alphanumeric, dots, hyphens
        const domainPattern = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        return domainPattern.test(domain);
    }

    if (videoSource && videoId) {
        if (videoSource.toLowerCase() === "twitch") {
            // Validate Twitch username and parent domain
            if (isValidTwitchUsername(videoId) && isValidDomain(parent)) {
                videoContainer.src = `https://player.twitch.tv/?channel=${encodeURIComponent(videoId)}&parent=${encodeURIComponent(parent)}`;
            } else {
                console.error("Invalid Twitch username or parent domain");
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
        // No video provided: prompt user for a URL or username and configure player
        const input = window.prompt("Enter a YouTube URL/video ID or Twitch URL/username:", "");
        if (input && input.trim().length > 0) {
            const trimmed = input.trim();

            // Helpers to extract IDs
            const extractYouTubeId = (urlOrId) => {
                // Direct 11-char ID
                const idPattern = /^[a-zA-Z0-9_-]{11}$/;
                if (idPattern.test(urlOrId)) return urlOrId;

                try {
                    const u = new URL(urlOrId);
                    // youtu.be/{id}
                    if (u.hostname.includes('youtu.be')) {
                        const pathId = u.pathname.split('/').filter(Boolean)[0];
                        if (pathId && idPattern.test(pathId)) return pathId;
                    }
                    // youtube.com/watch?v={id}
                    if (u.hostname.includes('youtube.com')) {
                        const v = u.searchParams.get('v');
                        if (v && idPattern.test(v)) return v;
                        // Shorts form: /shorts/{id}
                        const parts = u.pathname.split('/').filter(Boolean);
                        const shortsIdx = parts.findIndex(p => p.toLowerCase() === 'shorts');
                        if (shortsIdx !== -1 && parts[shortsIdx + 1] && idPattern.test(parts[shortsIdx + 1])) {
                            return parts[shortsIdx + 1];
                        }
                    }
                } catch (_) { /* not a URL; ignore */ }
                return null;
            };

            const extractTwitchChannel = (urlOrUser) => {
                // If looks like a URL, parse path
                try {
                    const u = new URL(urlOrUser);
                    if (u.hostname.includes('twitch.tv')) {
                        const seg = u.pathname.split('/').filter(Boolean)[0];
                        return seg || null;
                    }
                } catch (_) {
                    // Not a URL, treat as username (alphanumeric + underscore)
                    const userPattern = /^[A-Za-z0-9_]{3,25}$/;
                    if (userPattern.test(urlOrUser)) return urlOrUser;
                }
                return null;
            };

            let resolvedSource = null;
            let resolvedId = null;

            // Try YouTube first
            const yid = extractYouTubeId(trimmed);
            if (yid) {
                resolvedSource = 'youtube';
                resolvedId = yid;
            } else {
                // Try Twitch
                const tid = extractTwitchChannel(trimmed);
                if (tid) {
                    resolvedSource = 'twitch';
                    resolvedId = tid;
                }
            }

            if (resolvedSource && resolvedId) {
                // Update iframe with validated and encoded parameters
                if (resolvedSource === 'twitch') {
                    if (isValidTwitchUsername(resolvedId) && isValidDomain(parent)) {
                        videoContainer.src = `https://player.twitch.tv/?channel=${encodeURIComponent(resolvedId)}&parent=${encodeURIComponent(parent)}`;
                    } else {
                        console.error("Invalid Twitch username or parent domain");
                        hideElementById("video-frame");
                        hideElementById("video-container");
                        showElementById("nostream");
                        return;
                    }
                } else {
                    if (isValidYouTubeId(resolvedId)) {
                        videoContainer.src = `https://www.youtube.com/embed/${encodeURIComponent(resolvedId)}`;
                    } else {
                        console.error("Invalid YouTube video ID");
                        hideElementById("video-frame");
                        hideElementById("video-container");
                        showElementById("nostream");
                        return;
                    }
                }

                // Update URL params without reload
                const newParams = new URLSearchParams(window.location.search);
                newParams.set('videosource', resolvedSource);
                newParams.set('id', resolvedId);
                const newUrl = `${window.location.pathname}?${newParams.toString()}`;
                window.history.replaceState({}, '', newUrl);

                showElementById("video-container");
                showElementById("video-frame");
                hideElementById("nostream");
            } else {
                // Could not parse input, keep no-stream state
                hideElementById("video-frame");
                hideElementById("video-container");
                showElementById("nostream");
            }
        } else {
            hideElementById("video-frame");
            hideElementById("video-container");
            showElementById("nostream"); // Corrected line
        }
    }

    // Apply URL parameter styling
    const headerItems = document.querySelectorAll(".header-item");
    
    // Check for fontsize parameter
    const fontSizeParam = params.get("fontsize");
    if (fontSizeParam) {
        const fontSize = parseFloat(fontSizeParam);
        if (!isNaN(fontSize)) {
            headerItems.forEach(item => {
                item.style.fontSize = fontSize + "px";
            });
        }
    }

    // Check for font family parameter
    const fontFamilyParam = params.get("font") || params.get("fontfamily");
    if (fontFamilyParam) {
        headerItems.forEach(item => {
            item.style.fontFamily = fontFamilyParam;
        });
    }

    // Check for text color parameter
    const textColorParam = params.get("textcolor");
    if (textColorParam) {
        const colorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^[a-zA-Z]+$/;
        if (colorRegex.test(textColorParam)) {
            headerItems.forEach(item => {
                item.style.color = textColorParam;
            });
        }
    }

    // Check for caption background and opacity parameters
    const captionBgParam = params.get("captionbg");
    const captionOpacityParam = params.get("captionopacity");
    
    if (captionBgParam || captionOpacityParam) {
        const bgColor = captionBgParam || '#000000';
        const opacity = captionOpacityParam ? parseFloat(captionOpacityParam) / 100 : 0.7;
        
        const colorRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$|^[a-zA-Z]+$/;
        if (colorRegex.test(bgColor) && opacity >= 0 && opacity <= 1) {
            let gradientColor;
            if (bgColor.startsWith('#')) {
                const r = parseInt(bgColor.slice(1, 3), 16);
                const g = parseInt(bgColor.slice(3, 5), 16);
                const b = parseInt(bgColor.slice(5, 7), 16);
                const rgbaColor = `rgba(${r}, ${g}, ${b}, ${opacity})`;
                gradientColor = `linear-gradient(145deg, ${rgbaColor}, rgba(${Math.min(255, r+20)}, ${Math.min(255, g+20)}, ${Math.min(255, b+20)}, ${Math.max(0, opacity-0.1)}))`;
            } else {
                const rgbaColor = `rgba(0, 0, 0, ${opacity})`;
                gradientColor = `linear-gradient(145deg, ${rgbaColor}, rgba(20, 20, 20, ${Math.max(0, opacity-0.1)}))`;
            }
            
            headerItems.forEach(item => {
                item.style.background = gradientColor;
            });
        }
    }

    // Check for caption position parameter
    const captionPositionParam = params.get("captionposition");
    if (captionPositionParam) {
        const position = parseFloat(captionPositionParam);
        if (!isNaN(position) && position >= 0) {
            headerItems.forEach(item => {
                item.style.bottom = position + "px";
            });
        }
    }

    // Check for caption width parameter
    const captionWidthParam = params.get("captionwidth");
    if (captionWidthParam) {
        const width = parseFloat(captionWidthParam);
        if (!isNaN(width) && width > 0 && width <= 100) {
            headerItems.forEach(item => {
                item.style.width = width + "%";
            });
        }
    }

    // Check for viewport fit parameter
    const viewportFitParam = params.get("viewportfit");
    if (viewportFitParam && viewportFitParam.toLowerCase() === "true") {
        const videoContainerElement = document.getElementById("video-container");
        if (videoContainerElement) {
            videoContainerElement.classList.add("viewport-fit");
        }
    }
});