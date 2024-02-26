import json
import os
import subprocess
from threading import Thread
from flask import Flask, Response, request
from slack import WebClient
from slackeventsapi import SlackEventAdapter
import slack_blocks
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


app = Flask(__name__)


SLACK_SIGNING_SECRET = os.environ['SLACK_SIGNING_SECRET']
SLACK_TKEN = os.environ['SLACK_BOT_TOKEN']
VERIFICATION_TOKEN = os.environ['VERIFICATION_TOKEN']


slack_client = WebClient(SLACK_TKEN)
BOT_ID = slack_client.api_call("auth.test")['user_id']


slack_events_adapter = SlackEventAdapter(
    SLACK_SIGNING_SECRET, "/slack/events", app
)

available_commands = ["get", "describe", "logs", "rollout restart"]
available_sub_commands = {
    "get": ["pods", "nodes", "services"],
    "describe": ["pods"],
    "logs": ["pods"],
    "rollout restart": ["deployments"]
}

selected_actions = {}


def get_available_namespaces():
    try:
        command = ["kubectl", "get", "namespaces", "-o", "jsonpath='{.items[*].metadata.name}'"]
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        namespaces = result.stdout.strip("'").split()
        return namespaces
    except subprocess.CalledProcessError as e:
        logging.error("Error running kubectl command: %s", e)
        return []


def get_available_pods(namespace):
    try:
        command = ["kubectl", "get", "pods", "-n", namespace, "-o", "jsonpath='{.items[*].metadata.name}'"]
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        pods = result.stdout.strip("'").split()
        return pods
    except subprocess.CalledProcessError as e:
        logging.error("Error running kubectl command: %s", e)
        return []


def get_deployments(namespace):
    try:
        command = ["kubectl", "get", "deployments", "-n", namespace, "-o", "jsonpath='{.items[*].metadata.name}'"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        pods = result.stdout.strip("'").split()
        return pods
    except subprocess.CalledProcessError as e:
        logging.error("Error running kubectl command: %s", e)
        return []


def rollout_restart_deployment(namespace, deployment):
    try:
        command = ["kubectl", "rollout", "restart", "deployment", deployment, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stdout.strip("'").split()
        return output
    except subprocess.CalledProcessError as e:
        logging.error("Error running kubectl command: %s", e)
        return []


def run_kubectl_command(channel_id, command):
    try:
        logging.info("Running command: %s", command)
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        slack_client.chat_postMessage(channel=channel_id, text=f"```\n{output}\n```")
    except subprocess.CalledProcessError as e:
        slack_client.chat_postMessage(channel=channel_id, text=f"Error executing command:\n```\n{e.output}\n```")


@slack_events_adapter.on("app_mention")
def handle_mention(event_data):
    def send_kubectl_options(value):
        event_data = value
        message = event_data["event"]
        if message.get("subtype") is None:
            channel_id = message["channel"]
            user_id = message["user"]
            response_message = slack_blocks.build_kubectl_options_block(user_id, available_commands)
            slack_client.chat_postMessage(channel=channel_id, blocks=response_message["blocks"])

    thread = Thread(target=send_kubectl_options, kwargs={"value": event_data})
    thread.start()
    return Response(status=200)


@app.route('/k2sobot', methods=['POST'])
def message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    response_message = slack_blocks.build_kubectl_options_block(user_id, available_commands)
    slack_client.chat_postMessage(channel=channel_id, blocks=response_message["blocks"])
    return Response(), 200


@app.route("/interactions", methods=["POST"])
def handle_interactions():
    payload = json.loads(request.form.get("payload"))
    channel_id = payload["channel"]["id"]
    action_id = payload["actions"][0]["action_id"]

    if action_id == "kubectl_command_select":
        handle_kubectl_command_select(payload, channel_id)

    elif action_id == "kubectl_sub_command_select":
        handle_kubectl_sub_command_select(payload, channel_id)

    elif action_id == "kubectl_namespace_select":
        handle_kubectl_namespace_select(payload, channel_id)

    elif action_id == "kubectl_pod_select":
        handle_kubectl_pod_select(payload, channel_id)

    elif action_id == "kubectl_deployment_select":
        handle_kubectl_deployment_select(payload, channel_id)

    return Response(status=200)


def handle_kubectl_command_select(payload, channel_id):
    selected_command = payload["actions"][0]["selected_option"]["value"]
    selected_actions[channel_id] = {"command": selected_command}
    sub_command_menu = slack_blocks.build_kubectl_sub_command_block(available_sub_commands, selected_command)
    slack_client.chat_postMessage(channel=channel_id, blocks=sub_command_menu["blocks"])


def handle_kubectl_sub_command_select(payload, channel_id):
    selected_sub_command = payload["actions"][0]["selected_option"]["value"]
    if channel_id in selected_actions:
        selected_actions[channel_id]["sub_command"] = selected_sub_command
    available_namespaces = get_available_namespaces()
    namespaces_menu = slack_blocks.build_namesapces_block(available_namespaces)
    slack_client.chat_postMessage(channel=channel_id, blocks=namespaces_menu["blocks"])


def handle_kubectl_namespace_select(payload, channel_id):
    selected_namespace = payload["actions"][0]["selected_option"]["value"]
    if channel_id in selected_actions:
        selected_actions[channel_id]["namespace"] = selected_namespace

    selected_command = selected_actions.get(channel_id, {}).get("command")
    selected_sub_command = selected_actions.get(channel_id, {}).get("sub_command")

    if selected_command in ["describe", "logs"] and selected_sub_command == "pods":
        available_pods = get_available_pods(selected_namespace)
        pods_menu = slack_blocks.build_pod_command_block(available_pods)
        slack_client.chat_postMessage(channel=channel_id, blocks=pods_menu["blocks"])
    elif selected_command in ["rollout restart"] and selected_sub_command == "deployments":
        available_deployments = get_deployments(selected_namespace)
        deployments_menu = slack_blocks.build_deployments_command_block(available_deployments)
        slack_client.chat_postMessage(channel=channel_id, blocks=deployments_menu["blocks"])
    else:
        command = f"kubectl {selected_command} {selected_sub_command} -n {selected_namespace}"
        run_kubectl_command(channel_id, command)


def handle_kubectl_pod_select(payload, channel_id):
    selected_pod = payload["actions"][0]["selected_option"]["value"]
    selected_namespace = selected_actions.get(channel_id, {}).get("namespace", "")
    selected_command = selected_actions.get(channel_id, {}).get("command")
    if selected_namespace:
        if selected_command in ["logs"]:
            command = f"kubectl {selected_command} {selected_pod} -n {selected_namespace}"
        else:
            command = f"kubectl {selected_command} pod {selected_pod} -n {selected_namespace}"
        run_kubectl_command(channel_id, command)
    else:
        slack_client.chat_postMessage(channel=channel_id, text="Namespace not selected. Please start over.")


def handle_kubectl_deployment_select(payload, channel_id):
    selected_deployment = payload["actions"][0]["selected_option"]["value"]
    selected_namespace = selected_actions.get(channel_id, {}).get("namespace", "")
    selected_command = selected_actions.get(channel_id, {}).get("command")

    if selected_namespace:
        command = f"kubectl {selected_command} deployment {selected_deployment} -n {selected_namespace}"
        run_kubectl_command(channel_id, command)
    else:
        slack_client.chat_postMessage(channel=channel_id, text="Namespace not selected. Please start over.")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=3000)
