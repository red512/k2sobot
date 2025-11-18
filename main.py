import json
from threading import Thread
from flask import Flask, Response, request
from slack_sdk import WebClient
from slackeventsapi import SlackEventAdapter
import slack_blocks
import logging
import k8s, handlers, shared_state as shared
from gemini_integration import chat_with_gemini, is_gemini_available
from config import SLACK_SIGNING_SECRET, SLACK_TOKEN, VERIFICATION_TOKEN

# Import specific tools for commands
from tools import get_current_time, get_random_joke

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

slack_client = WebClient(SLACK_TOKEN)
BOT_ID = slack_client.api_call("auth.test")['user_id']

shared.slack_client = slack_client

slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app
)

shared.selected_actions = {}

@slack_events_adapter.on("app_mention")
def handle_mention(event_data):
    thread = Thread(target=send_kubectl_options, kwargs={"value": event_data})
    thread.start()
    return Response(status=200)

@slack_events_adapter.on("message")
def handle_message(event_data):
    message = event_data["event"]
    
    if message.get("subtype") is not None or message.get("user") == BOT_ID:
        return Response(status=200)
    
    channel_id = message.get("channel", "")
    
    if channel_id.startswith("D"):
        thread = Thread(target=handle_direct_message, kwargs={"event_data": event_data})
        thread.start()
    
    return Response(status=200)

def handle_direct_message(event_data):
    """Handle direct messages with Gemini"""
    message = event_data["event"]
    channel_id = message["channel"]
    user_id = message.get("user")
    user_message = message.get("text", "").strip()

    if not user_message:
        return

    try:
        user_message_lower = user_message.lower()


        if not is_gemini_available():
            slack_client.chat_postMessage(
                channel=channel_id,
                text="Sorry, Gemini AI is not configured. Please contact the administrator."
            )
            return

        thinking_msg = slack_client.chat_postMessage(
            channel=channel_id,
            text="🤔 Thinking..."
        )

        response = chat_with_gemini(user_message, user_id=user_id)
        
        try:
            slack_client.chat_delete(channel=channel_id, ts=thinking_msg['ts'])
        except:
            pass
        
        slack_client.chat_postMessage(channel=channel_id, text=response)
        
        logging.info(f"✅ Responded to DM with native function calling")
        
    except Exception as e:
        logging.error(f"❌ Error handling direct message: {e}", exc_info=True)
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

@app.route('/k2sobot', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    response_message = slack_blocks.build_kubectl_options_block(user_id, shared.available_commands)
    slack_client.chat_postMessage(channel=channel_id, blocks=response_message["blocks"])
    return Response(), 200

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

    elif action_id == "argo_app_select":
        handlers.handle_argo_app_select(payload, channel_id)

    elif action_id == "argo_revision_select":
        handlers.handle_argo_revision_select(payload, channel_id)

    return Response(status=200)

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker and load balancers"""
    try:
        # Basic health checks
        status = {
            "status": "healthy",
            "service": "k2sobot",
            "version": "1.0.0",
            "gemini_available": is_gemini_available(),
            "timestamp": get_current_time()
        }
        return Response(
            response=json.dumps(status),
            status=200,
            mimetype="application/json"
        )
    except Exception as e:
        error_status = {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": get_current_time()
        }
        return Response(
            response=json.dumps(error_status),
            status=500,
            mimetype="application/json"
        )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)