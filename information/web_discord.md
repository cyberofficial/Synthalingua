# Web & Discord Integration

These arguments control integration with Discord and the built-in web server.

## Arguments
| Flag                    | Description                                                      |
|-------------------------|------------------------------------------------------------------|
| `--portnumber`          | Port number for the local web server.                             |
| `--discord_webhook`     | Discord webhook URL for notifications and results.                |
| `--remote_hls_password_id` | Password ID for the webserver.                                 |
| `--remote_hls_password` | Password for the HLS webserver.                                   |

## Details & Examples

### `--portnumber`
Launches a local Flask web server to view real-time subtitles in your browser. Example:
```
python transcribe_audio.py --portnumber 8080
```

### `--discord_webhook`
Sends results and notifications to a Discord channel. Example:
```
python transcribe_audio.py --discord_webhook "https://discord.com/api/webhooks/1234567890/1234567890"
```

### `--remote_hls_password_id` & `--remote_hls_password`
Set password protection for the web server (for remote HLS streaming).

---
[Back to Index](./index.md)
