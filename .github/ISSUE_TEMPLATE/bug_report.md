---
name: Bug report
about: Create a report to help us improve
title: Bug report [replace full title with short description]
labels: needs review
assignees: cyberofficial

---

###  Prerequisites

Before submitting a bug report, please ensure you have completed the following steps. This helps us resolve issues much faster!

- [ ] I have searched the [existing issues](https://github.com/cyberofficial/Synthalingua/issues) to make sure this bug has not already been reported.
- [ ] I am using the **latest version** of the script from the `master` branch.
     - If you are using a pre-release branch, you can still make a report, but please make sure you are at the latest release of the branch release.
- [ ] I have read the [documentation](https://github.com/cyberofficial/Synthalingua/blob/refactor/information/index.md) for the feature I am using.

---

###  Bug Description

A clear and concise description of what the bug is.
*<!-- For example: "When using --isolate_vocals with a .wav file, the program crashes with a 'demucs not found' error even though it is installed." -->*

---

###  Command to Reproduce

This is the **most important** piece of information. Please provide the **exact command** you ran in your terminal that caused the issue.

*<!-- 
IMPORTANT: Please replace placeholder paths like "C:/path/to/video.mp4" with your actual file paths.
If the command includes sensitive information like a stream key, please redact it like this: --remote_hls_password [REDACTED]
-->*

```bash
# PASTE THE FULL COMMAND YOU RAN HERE
python transcribe_audio.py ...
```

---

###  Full Console Output

Please paste the **entire, unedited console output** from the moment you ran the command until it finished or crashed. This is much more helpful than a screenshot.

```
PASTE THE ENTIRE CONSOLE LOG HERE
```

---

###  Expected Behavior

A clear and concise description of what you **expected** to happen.
*<!-- For example: "I expected the script to generate an SRT file in the output folder." -->*

---

###  System Environment

Providing this information is crucial for us to reproduce and solve the bug.

- **Operating System:** [e.g., Windows 11, Ubuntu 22.04, macOS Sonoma]
- **Python Version:** [e.g., 3.12.8 (run `python --version` to find out)]
- **GPU:** [e.g., NVIDIA RTX 3080, AMD RX 6700 XT, or "CPU only"]
- **Installation Method:** [e.g., `pip`, `conda`, or "Used `set_up_env.py`"]
- **Synthalingua Version:** [e.g., v1.1.1 (run `transcribe_audio --about` if possible)]

---

###  Additional information

Add any other context about the problem here.
- If the issue is with a specific audio/video file, can you describe it? (e.g., "It's a 1-hour long 1080p MP4 file with background music.")
- If you can share the problematic file or a similar public one (like a YouTube link) that reproduces the issue, please include it here.
- Did this command work in a previous version of Synthalingua? If so, which one?
```
