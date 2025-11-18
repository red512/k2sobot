# Shared state between modules
from collections import defaultdict, deque

selected_actions = {}
slack_client = None
available_commands = ["get", "describe", "logs", "rollout restart", "argo"]
available_sub_commands = {
    "get": ["pods", "nodes", "services"],
    "describe": ["pods"],
    "logs": ["pods"],
    "rollout restart": ["deployments"],
    "argo": ["status", "revisions", "rollback"]
}

# Conversation history management - keep last 10 messages per user
conversation_histories = defaultdict(lambda: deque(maxlen=10))

def add_to_conversation_history(user_id, role, content):
    """Add a message to user's conversation history"""
    conversation_histories[user_id].append({
        "role": role,  # "user" or "model"
        "parts": [{"text": content}]
    })

def get_conversation_history(user_id):
    """Get conversation history for a user"""
    return list(conversation_histories[user_id])