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
   }
}

document.addEventListener("DOMContentLoaded", function () {
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


   // Show/hide headers based on URL parameters
   if (!showOriginal && !showTranslation && !showTranscription) {
      showElementById("header-text");
      showElementById("header-text-1");
      showElementById("translated-header");
      showElementById("translated-header-1");
      showElementById("transcribed-header");
      showElementById("transcribed-header-1");
   } else {
      if (!showOriginal) hideElementById("header-text");
      if (!showOriginal) hideElementById("header-text-1");
      if (!showTranslation) hideElementById("translated-header");
      if (!showTranslation) hideElementById("translated-header-1");
      if (!showTranscription) hideElementById("transcribed-header");
      if (!showTranscription) hideElementById("transcribed-header-1");
   }

   // Check for dark mode parameter
   const darkModeParam = params.get("darkmode");
   if (darkModeParam && darkModeParam.toLowerCase() === "true") {
      document.body.classList.add("dark-mode");
   }

   setInterval(updateHeaders, 50);

   // Update video frame based on URL parameters
   const videoContainer = document.getElementById("video-frame");
   const videoSource = params.get("videosource");
   const videoId = params.get("id");

   if (videoSource && videoId) {
      if (videoSource.toLowerCase() === "twitch") {
         videoContainer.src = `https://player.twitch.tv/?channel=${videoId}&parent=localhost`;
      } else if (videoSource.toLowerCase() === "youtube") {
         videoContainer.src = `https://www.youtube.com/embed/${videoId}`;
      }
      showElementById("video-frame");
      hideElementById("nostream"); // Corrected line
   } else {
      hideElementById("video-frame");
      showElementById("nostream"); // Corrected line
   }
});