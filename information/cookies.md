# Using Cookies with Synthalingua Streams

Some streams (especially Twitch and YouTube) require authentication via cookies to access private or region-locked content. Synthalingua supports Netscape/Mozilla-style cookies files for this purpose.

> **Security Note:**
> Storing cookies on your PC can be risky if your system is not secure. Treat your cookies file like a password: keep it private, and delete it after you are done using Synthalingua to be extra safe. While cookies do expire automatically, it’s best to remove them yourself when finished, especially if you share your computer or are concerned about account security.

## What Are Netscape-Style Cookies?
These are plain text files containing your browser's cookies in a standard format. They are often called "cookies.txt" and are compatible with many tools (like yt-dlp, youtube-dl, and Synthalingua).

---

## How to Export Cookies from Your Browser

### Chrome/Edge/Brave/Chromium
1. Install the [Cookie-Editor Extension](https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm?utm_campaign=github) from the Chrome Web Store.
2. Go to the website (e.g., twitch.tv or youtube.com) and log in.
3. Click the Cookie-Editor extension icon.
4. Click "Export".
5. In the export dialog, select the "Netscape" format.
6. Copy the exported text.
7. Open Notepad (or any text editor), paste the contents, and save as `cookies.txt`.
8. Place the file in the `cookies/` folder in your Synthalingua directory (e.g., `cookies/twitch.txt`).

### Firefox
1. Install the [Cookie-Editor Extension for Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/?utm_campaign=external-github-readme).
2. Log in to the site you want cookies for.
3. Click the Cookie-Editor extension icon.
4. Click "Export".
5. In the export dialog, select the "Netscape" format.
6. Copy the exported text.
7. Open Notepad (or any text editor), paste the contents, and save as `cookies.txt`.
8. Place the file in the `cookies/` folder.

### Opera
- Opera is Chromium-based, so you can use the same Chrome extension as above.

---

## Using Cookies in Synthalingua
- Place your cookies file in the `cookies/` folder (e.g., `cookies/twitch.txt` or `cookies/youtube.txt`).
- Use the `--cookies` argument (without the `.txt` extension):
  ```sh
  python transcribe_audio.py --stream https://www.twitch.tv/somestreamerhere --cookies twitch
  ```
- For YouTube:
  ```sh
  python transcribe_audio.py --stream https://www.youtube.com/watch?v=abc123 --cookies youtube
  ```

---

## Tips
- Always export cookies while logged in to the site you want to access.
- If you change your password or log out, you may need to re-export cookies.
- Never share your cookies file with others—it can be used to access your account!

---
[Back to Index](./index.md)
