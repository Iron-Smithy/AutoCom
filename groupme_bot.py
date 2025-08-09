import os
import requests

# Read bot ID from environment variable
BOT_ID = os.environ.get("GROUPME_BOT_ID")

def send_groupme_message(text: str, bot_id: str = BOT_ID):
    """
    Sends a message to a GroupMe group via bot.
    
    Parameters:
        text (str): The message to send.
        bot_id (str): Your GroupMe bot ID from GitHub Secrets.
    """
    if not bot_id:
        raise ValueError("GROUPME_BOT_ID is not set in environment variables.")

    url = "https://api.groupme.com/v3/bots/post"
    payload = {"bot_id": bot_id, "text": text}
    response = requests.post(url, json=payload)

    if response.status_code == 202:
        print("Message sent successfully.")
    else:
        print("Failed to send message:", response.status_code, response.text)

if __name__ == "__main__":
    msg = input("Enter the message to send to GroupMe: ")
    send_groupme_message(msg)
