import json
import os
import subprocess
from threading import Thread
from flask import Flask, Response, request
from slack_sdk import WebClient
from slackeventsapi import SlackEventAdapter
import slack_blocks
import logging
import k8s, handlers, shared_state as shared
from gemini_integration import chat_with_gemini, is_gemini_available  # Import Gemini functions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
SLACK_TOKEN = os.environ['SLACK_BOT_TOKEN']
VERIFICATION_TOKEN = os.environ['VERIFICATION_TOKEN']

slack_client = WebClient(SLACK_TOKEN)
BOT_ID = slack_client.api_call("auth.test")['user_id']

# Share the slack_client with other modules
shared.slack_client = slack_client

slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app
)

shared.selected_actions = {}

# EXISTING: Handle mentions (preserved)
@slack_events_adapter.on("app_mention")
def handle_mention(event_data):
    thread = Thread(target=send_kubectl_options, kwargs={"value": event_data})
    thread.start()
    return Response(status=200)

# NEW: Handle direct messages
@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    
    # Ignore bot's own messages
    if message.get("subtype") == "bot_message":
        return Response(status=200)
    
    # Ignore if bot is mentioned (already handled by app_mention)
    if message.get("subtype") == "app_mention":
        return Response(status=200)
    
    # Ignore messages with subtype (edits, deletes, etc.)
    if message.get("subtype") is not None:
        return Response(status=200)
    
    # Ignore if the message is from the bot itself
    if message.get("user") == BOT_ID:
        return Response(status=200)
    
    # Check if it's a direct message (channel starts with 'D')
    channel_id = message.get("channel", "")
    if channel_id.startswith("D"):
        # It's a DM, use Gemini
        thread = Thread(target=handle_direct_message, kwargs={"event_data": event_data})
        thread.start()
    
    return Response(status=200)

def handle_direct_message(event_data):
    """Handle direct messages with Gemini"""
    message = event_data["event"]
    channel_id = message["channel"]
    user_message = message.get("text", "")
    
    if not user_message.strip():
        return
    
    try:
        # Check if Gemini is available
        if not is_gemini_available():
            slack_client.chat_postMessage(
                channel=channel_id,
                text="Sorry, Gemini AI is not configured. Please contact the administrator."
            )
            return
        
        # Send "typing" indicator
        slack_client.chat_postMessage(
            channel=channel_id,
            text="Thinking... 🤔"
        )
        
        # Get response from Gemini
        gemini_response = chat_with_gemini(user_message)
        
        # Send the response
        slack_client.chat_postMessage(
            channel=channel_id,
            text=gemini_response
        )
        
        logging.info(f"Responded to DM from user in channel {channel_id}")
        
    except Exception as e:
        logging.error(f"Error handling direct message: {e}")
        slack_client.chat_postMessage(
            channel=channel_id,
            text=f"Sorry, I encountered an error: {str(e)}"
        )

def send_kubectl_options(value):
    event_data = value
    message = event_data["event"]
    if message.get("subtype") is None:
        channel_id = message["channel"]
        user_id = message["user"]
        response_message = slack_blocks.build_kubectl_options_block(user_id, shared.available_commands)
        slack_client.chat_postMessage(channel=channel_id, blocks=response_message["blocks"])

# EXISTING: Slash command handler (preserved)
@app.route('/k2sobot', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    response_message = slack_blocks.build_kubectl_options_block(user_id, shared.available_commands)
    slack_client.chat_postMessage(channel=channel_id, blocks=response_message["blocks"])
    return Response(), 200

# EXISTING: Interactions handler (preserved)
@app.route("/interactions", methods=["POST"])
def handle_interactions():
    payload = json.loads(request.form.get("payload"))
    channel_id = payload["channel"]["id"]
    action_id = payload["actions"][0]["action_id"]

    if action_id == "kubectl_command_select":
        handlers.handle_kubectl_command_select(payload, channel_id)

    elif action_id == "kubectl_sub_command_select":
        handlers.handle_kubectl_sub_command_select(payload, channel_id)

    elif action_id == "kubectl_namespace_select":
        handlers.handle_kubectl_namespace_select(payload, channel_id)

    elif action_id == "kubectl_pod_select":
        handlers.handle_kubectl_pod_select(payload, channel_id)

    elif action_id == "kubectl_deployment_select":
        handlers.handle_kubectl_deployment_select(payload, channel_id)

    return Response(status=200)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)