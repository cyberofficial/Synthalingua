document.addEventListener("DOMContentLoaded", function() {
    function updateHeaders() {
        fetch("/update-header")
            .then(response => response.text())
            .then(originalText => {
                document.getElementById("header-text").innerText = "Detected: " + originalText;
            });
            
        fetch("/update-translated-header")
            .then(response => response.text())
            .then(translatedText => {
                document.getElementById("translated-header").innerText = "Translated: " + translatedText;
            });
            
        fetch("/update-transcribed-header")
            .then(response => response.text())
            .then(transcribedText => {
                document.getElementById("transcribed-header").innerText = "Transcribed: " + transcribedText;
            });
    }

    setInterval(updateHeaders, 100);
});