document.addEventListener("DOMContentLoaded", function() {
    function updateHeaders() {
        fetch("/update-header")
            .then(response => response.text())
            .then(originalText => {
                /*Detected: */
                document.getElementById("header-text").innerText = "" + originalText;
            });
            
        fetch("/update-translated-header")
            .then(response => response.text())
            .then(translatedText => {
                /*Translated: */
                document.getElementById("translated-header").innerText = "" + translatedText;
            });
            
        fetch("/update-transcribed-header")
            .then(response => response.text())
            .then(transcribedText => {
                /*Transcribed: */
                document.getElementById("transcribed-header").innerText = "" + transcribedText;
            });
    }

    setInterval(updateHeaders, 500);
});