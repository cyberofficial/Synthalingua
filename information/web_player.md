# Web Player (html_data)

The Synthalingua Web Player provides a real-time, browser-based interface for viewing live transcriptions, translations, and original subtitles from streams or microphone input. It is served automatically when you launch Synthalingua with the `--portnumber` argument.

---

## Features
- **Live subtitle, translation, and transcription display**
- **Dark mode** and font size customization via URL parameters
- **Responsive video player** with overlayed headers
- **Supports Twitch, YouTube, and custom HLS streams**
- **Easy browser access on local network**

---

## How to Use

### 1. Start the Web Server
Run Synthalingua with the `--portnumber` argument:

    python transcribe_audio.py --stream <stream_url> --stream_language <lang> --stream_translate --portnumber 8080

Then open your browser and go to `http://localhost:8080` (or your server's IP address).

### 2. Web Player Layout
- **Video Frame**: Embedded stream or video
- **Headers**: Three overlayed text bars for original, translated, and transcribed text
- **Dark Mode**: Toggle with `?darkmode=true` in the URL
- **Font Size**: Adjust with `?fontsize=24` (any px value)

### 3. URL Parameters
- `showoriginal` – Show original detected text
- `showtranslation` – Show translated text
- `showtranscription` – Show transcribed text
- `darkmode` – Enable dark mode (`true`/`false`)
- `fontsize` – Set header font size (e.g., `fontsize=28`)
- `videosource` – Set video source (Twitch, YouTube, HLS)
- `id` – Video ID for supported platforms

Example:

    http://localhost:8080/player.html?showoriginal&showtranslation&darkmode=true&fontsize=28

### 4. Customization
- **Dark Mode**: Changes background and header colors for low-light viewing
- **Font Size**: Makes headers easier to read from a distance
- **Header Visibility**: Show/hide any combination of original, translated, or transcribed text

---

## File Structure
- `html_data/index.html` – Main landing page
- `html_data/player.html` – Main web player UI
- `html_data/static/index.js` – JS for index page
- `html_data/static/player_script.js` – JS for player page (handles URL params, header updates, video embedding)
- `html_data/static/styles.css` – Styling for all web UI

---

## Advanced: Embedding and Remote Access
- You can embed the player in OBS or other tools using the local URL
- For remote access, open the port in your firewall and use your server's IP
- Password protection is available via `--remote_hls_password_id` and `--remote_hls_password`

---

## Troubleshooting
- If the web player does not load, ensure the server is running and the port is open
- For custom video sources, check the `videosource` and `id` URL parameters
- For more help, see [web_discord.md](./web_discord.md) or [troubleshooting.md](./troubleshooting.md)

---

[Back to Index](./index.md)
