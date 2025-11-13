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
from gemini_integration import chat_with_gemini, chat_with_mcp, is_gemini_available
from mcp_client import setup_mcp_servers, get_mcp_client

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

# Initialize MCP servers
try:
    setup_mcp_servers()
    logging.info("✅ MCP servers initialized")
except Exception as e:
    logging.error(f"❌ Failed to initialize MCP servers: {e}")

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
    
    # Ignore bot's own messages and subtypes
    if message.get("subtype") is not None or message.get("user") == BOT_ID:
        return Response(status=200)
    
    channel_id = message.get("channel", "")
    
    # Handle DMs with Gemini + MCP
    if channel_id.startswith("D"):
        thread = Thread(target=handle_direct_message, kwargs={"event_data": event_data})
        thread.start()
    
    return Response(status=200)

def handle_direct_message(event_data):
    """Handle direct messages with Gemini + MCP"""
    message = event_data["event"]
    channel_id = message["channel"]
    user_message = message.get("text", "").strip()
    
    if not user_message:
        return
    
    try:
        # Check for MCP commands FIRST (before sending to Gemini)
        user_message_lower = user_message.lower().strip()
        # Remove quotes if present (Slack sometimes adds them)
        user_message_clean = user_message_lower.strip('"\'')

        logging.info(f"🔍 Processing message: '{user_message}' (cleaned: '{user_message_clean}')")

        # Handle MCP list command
        if user_message_clean == "/mcp list":
            logging.info("📋 Handling /mcp list command")
            mcp = get_mcp_client()
            all_tools = mcp.list_all_tools()

            response = "🔧 **Available MCP Servers & Tools:**\n\n"
            for server, tools in all_tools.items():
                response += f"**{server}:**\n"
                for tool in tools:
                    response += f"  • `{tool['name']}`: {tool['description'][:100]}...\n"

            slack_client.chat_postMessage(channel=channel_id, text=response)
            logging.info("✅ Sent MCP list response")
            return

        # Handle MCP status command
        if user_message_clean == "/mcp status":
            logging.info("📊 Handling /mcp status command")
            mcp = get_mcp_client()
            servers = mcp.list_servers()
            all_tools = mcp.list_all_tools()

            response = "📊 **MCP Status:**\n\n"
            response += f"**Registered Servers:** {len(servers)}\n"
            for server in servers:
                tools = all_tools.get(server, [])
                status_icon = "✅" if tools else "❌"
                response += f"  {status_icon} `{server}`: {len(tools)} tools available\n"

            response += "\n💡 **Available Commands:**\n"
            response += "  • `/mcp list` - See all tools\n"
            response += "  • `/mcp status` - Check server status\n"
            response += "  • `/mcp help` - Show help\n"
            response += "\n_Tool invocations are shown at the bottom of responses_"

            slack_client.chat_postMessage(channel=channel_id, text=response)
            logging.info("✅ Sent MCP status response")
            return

        # Handle MCP help command
        if user_message_clean in ["/mcp help", "/mcp", "help mcp"]:
            logging.info("❓ Handling /mcp help command")
            response = """🔧 **MCP (Model Context Protocol) Help**

**Available Commands:**
- `/mcp status` - Check MCP server status
- `/mcp list` - List all available tools
- `/mcp help` - Show this help message

**What is MCP?**
MCP allows me to use external tools to help you better. When I use a tool, you'll see it noted at the bottom of my response.

**Available Tools:**
- **Time Server** - Get current time and timestamps
- **Joke Server** - Get programming jokes

**Examples:**
- "What time is it?" → I'll use the time tool 🕐
- "Tell me a joke" → I'll use the joke tool 😄

Try asking me something! 😊"""

            slack_client.chat_postMessage(channel=channel_id, text=response)
            logging.info("✅ Sent MCP help response")
            return
        
        # If we reach here, it's not an MCP command - send to Gemini
        logging.info(f"🤖 Sending to Gemini: '{user_message}'")

        # Now check if Gemini is available
        if not is_gemini_available():
            slack_client.chat_postMessage(
                channel=channel_id,
                text="Sorry, Gemini AI is not configured. Please contact the administrator."
            )
            return
        
        # Send thinking indicator (only if not a command)
        thinking_msg = slack_client.chat_postMessage(
            channel=channel_id,
            text="🤔 Thinking..."
        )
        
        # Use MCP-enhanced chat
        response = chat_with_mcp(user_message)
        
        # Delete thinking message
        try:
            slack_client.chat_delete(channel=channel_id, ts=thinking_msg['ts'])
        except:
            pass
        
        # Send response
        slack_client.chat_postMessage(channel=channel_id, text=response)
        
        logging.info(f"✅ Responded to DM with MCP support")
        
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