import requests
import re
import json

def send_to_discord_webhook(webhook_url, text):
    data = {
        "content": text
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        if len(text) > 1800:
            for i in range(0, len(text), 1800):
                data["content"] = text[i:i+1800]
                response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
                if response.status_code == 429:
                    print("Discord webhook is being rate limited.")
        else:
            response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
            if response.status_code == 429:
                print("Discord webhook is being rate limited.")
    except:
        print("Failed to send message to Discord webhook.")
        pass

print("Discord Module Loaded")