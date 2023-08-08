document.addEventListener("DOMContentLoaded", function() {
    function updateHeader() {
        fetch("/update-header")
            .then(response => response.text())
            .then(text => {
                document.getElementById("header-text").innerText = text;
            });
    }

    setInterval(updateHeader, 100); // Update every 3 seconds (adjust as needed)
});