# Shared state between modules
selected_actions = {}
slack_client = None
available_commands = ["get", "describe", "logs", "rollout restart"]
available_sub_commands = {
    "get": ["pods", "nodes", "services"],
    "describe": ["pods"],
    "logs": ["pods"],
    "rollout restart": ["deployments"]
}