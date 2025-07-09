# Troubleshooting & FAQ

Common issues and solutions for Synthalingua.

## Python & Environment
- **Python not recognized:** Add Python to PATH, restart, check version (must be 3.12.x, not 3.13 or 3.11 & lower.)
- **No module named 'transformers':** Run `pip install transformers` in the correct Python environment
- **Git not recognized:** Add Git to PATH, restart
- **CUDA not available:** Install CUDA (Nvidia only), or use CPU mode

## Audio & Input
- **Audio source errors:** Make sure a microphone or stream is set up
- **Microphone not detected:** Use `--list_microphones` to see available devices
- **Permission errors:** Run your terminal as administrator or check OS permissions

## Blocklist & Filtering
- **Blocklist not working:** Ensure your `--ignorelist` file is formatted with one phrase per line
- **Auto blocklist not adding phrases:** Requires both `--auto_blocklist` and `--ignorelist`

## Web & Discord
- **Web server not starting:** Make sure the port is available and not blocked by firewall
- **Discord messages not sending:** Check webhook URL and Discord permissions

## General
- **Crashes or unexpected errors:** Check the error message, consult the [GitHub Issues](https://github.com/cyberofficial/Synthalingua/issues), or ask for help

---
[Back to Index](./index.md)
