"""
Discord webhook integration module for message forwarding.

This module provides functionality to send messages to Discord channels through
webhooks with enhanced formatting. It handles message chunking for long texts,
implements rate limit handling, and provides beautiful Discord-formatted messages
with emojis, embeds, and proper styling.
"""

import requests
import json
from colorama import Fore, Style, init

# Initialize colorama for console output
init(autoreset=True)

def send_to_discord_webhook(webhook_url, text, message_type="info"):
    """
    Send a beautifully formatted message to a Discord channel through a webhook.

    Handles long messages by automatically chunking them into smaller pieces
    to comply with Discord's message length limits. Includes enhanced formatting
    with emojis and proper Discord markdown.

    Args:
        webhook_url (str): The Discord webhook URL to send messages to
        text (str): The message text to send
        message_type (str): Type of message for formatting ("info", "success", "warning", "error", "transcription", "translation")

    Note:
        - Messages longer than 1800 characters are automatically split into chunks
        - Uses Discord markdown for enhanced formatting
        - Includes appropriate emojis based on message type
        - Proper error handling with styled console output

    Example:
        send_to_discord_webhook("https://discord.com/api/webhooks/...", "Hello World!", "success")
    """
    
    # Format message based on type
    formatted_text = format_discord_message(text, message_type)
    
    data = {}  # Initialize as empty dict
    headers = {"Content-Type": "application/json"}
    
    try:
        chunks = [formatted_text[i:i+1800] for i in range(0, len(formatted_text), 1800)]
        for chunk in chunks:
            data["content"] = chunk
            response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
            
            if response.status_code == 429:
                print(f"{Fore.YELLOW}⚠️ [WARNING]{Style.RESET_ALL} Discord webhook is being rate limited")
            elif not response.ok:
                print(f"{Fore.RED}❌ [ERROR]{Style.RESET_ALL} Failed to send message to Discord: {response.status_code} {response.text}")
            else:
                print(f"{Fore.GREEN}✅ [SUCCESS]{Style.RESET_ALL} Message sent to Discord webhook")
                
    except Exception as ex:
        print(f"{Fore.RED}❌ [ERROR]{Style.RESET_ALL} Failed to send Discord webhook message: {ex}")

def format_discord_message(text, message_type="info"):
    """
    Format message with Discord markdown and emojis based on message type.
    
    Args:
        text (str): The message text to format
        message_type (str): Type of message for appropriate formatting
        
    Returns:
        str: Formatted message with Discord markdown and emojis
    """
    
    if message_type == "transcription":
        # Format transcription messages
        if "Original" in text:
            return f"🗣️ **Original Transcription**\n\n{text.replace('Stream', '').replace('Original:', '').strip()}\n"
        elif "Transcription" in text:
            return f"📝 **Transcription**\n\n{text.replace('Stream', '').replace('Transcription:', '').strip()}\n"
        else:
            return f"🎤 **Audio Transcription**\n\n{text}\n"
    
    elif message_type == "translation":
        return f"🌐 **Translation**\n\n{text.replace('Stream EN Translation:', '').strip()}\n"
    
    elif message_type == "success":
        return f"✅ **Success** | {text}"
    
    elif message_type == "warning":
        return f"⚠️ **Warning** | {text}"
    
    elif message_type == "error":
        return f"❌ **Error** | {text}"
        
    elif message_type == "startup":
        return f"🚀 **Synthalingua Started**\n{text}"
        
    elif message_type == "shutdown":
        return f"🛑 **Service Stopped**\n{text}"
        
    elif message_type == "info":
        return f"ℹ️ **Info** | {text}"
    
    else:
        # Default formatting
        return f"💬 {text}"

def send_transcription_to_discord(webhook_url, language, content, result_type="Original"):
    """
    Send a transcription result to Discord with beautiful formatting.
    
    Args:
        webhook_url (str): Discord webhook URL
        language (str): Language of the transcription
        content (str): Transcribed text content
        result_type (str): Type of result ("Original", "Translation", "Transcription")
    """
    if result_type == "Translation":
        icon = "🌐"
        title = f"**{language} Translation**"
        message_type = "translation"
    elif result_type == "Transcription":
        icon = "📝"
        title = f"**{language} Transcription**"
        message_type = "transcription"
    else:
        icon = "🗣️"
        title = f"**{language} Original**"
        message_type = "transcription"
    
    formatted_message = f"{icon} {title}\n```\n{content.strip()}\n```"
    send_to_discord_webhook(webhook_url, formatted_message, message_type)

def send_startup_notification(webhook_url, model_info, translation_enabled=False):
    """
    Send a beautifully formatted startup notification to Discord.
    
    Args:
        webhook_url (str): Discord webhook URL
        model_info (str): Information about the model being used
        translation_enabled (bool): Whether translation is enabled
    """
    translation_status = "🌐 **Translation: Enabled**" if translation_enabled else "🚫 **Translation: Disabled**"
    message = f"🚀 **Synthalingua Service Started**\n\n🤖 **Model:** {model_info}\n{translation_status}\n\n📡 Ready to process audio streams!"
    send_to_discord_webhook(webhook_url, message, "startup")

def send_shutdown_notification(webhook_url):
    """
    Send a beautifully formatted shutdown notification to Discord.
    
    Args:
        webhook_url (str): Discord webhook URL
    """
    message = "🛑 **Synthalingua Service Stopped**\n\n✨ All processing complete. Service is now offline."
    send_to_discord_webhook(webhook_url, message, "shutdown")

def send_error_notification(webhook_url, error_message):
    """
    Send a beautifully formatted error notification to Discord.
    
    Args:
        webhook_url (str): Discord webhook URL
        error_message (str): Error message to send
    """
    formatted_message = f"💥 **System Error Occurred**\n```\n{error_message}\n```\n\n🔧 Please check the logs for more details."
    send_to_discord_webhook(webhook_url, formatted_message, "error")

print(f"{Fore.GREEN}✅ [SUCCESS]{Style.RESET_ALL} Discord Module Loaded with Enhanced Formatting")