import json
import os
import subprocess
from threading import Thread
from flask import Flask, Response, request
from slack_sdk import WebClient
from slackeventsapi import SlackEventAdapter
import slack_blocks
import logging
import k8s, argo, shared_state as shared



def handle_kubectl_command_select(payload, channel_id):
    selected_command = payload["actions"][0]["selected_option"]["value"]
    shared.selected_actions[channel_id] = {"command": selected_command}
    sub_command_menu = slack_blocks.build_kubectl_sub_command_block(shared.available_sub_commands, selected_command)
    shared.slack_client.chat_postMessage(channel=channel_id, blocks=sub_command_menu["blocks"])


def handle_kubectl_sub_command_select(payload, channel_id):
    selected_sub_command = payload["actions"][0]["selected_option"]["value"]
    if channel_id in shared.selected_actions:
        shared.selected_actions[channel_id]["sub_command"] = selected_sub_command

    selected_command = shared.selected_actions.get(channel_id, {}).get("command")

    if selected_command == "argo":
        handle_argo_sub_command_select(payload, channel_id)
    else:
        available_namespaces = k8s.get_available_namespaces()
        namespaces_menu = slack_blocks.build_namesapces_block(available_namespaces)
        shared.slack_client.chat_postMessage(channel=channel_id, blocks=namespaces_menu["blocks"])


def handle_kubectl_namespace_select(payload, channel_id):
    selected_namespace = payload["actions"][0]["selected_option"]["value"]
    if channel_id in shared.selected_actions:
        shared.selected_actions[channel_id]["namespace"] = selected_namespace

    selected_command = shared.selected_actions.get(channel_id, {}).get("command")
    selected_sub_command = shared.selected_actions.get(channel_id, {}).get("sub_command")

    if selected_command in ["describe", "logs"] and selected_sub_command == "pods":
        available_pods = k8s.get_available_pods(selected_namespace)
        pods_menu = slack_blocks.build_pod_command_block(available_pods)
        shared.slack_client.chat_postMessage(channel=channel_id, blocks=pods_menu["blocks"])
    elif selected_command in ["rollout restart"] and selected_sub_command == "deployments":
        available_deployments = k8s.get_deployments(selected_namespace)
        deployments_menu = slack_blocks.build_deployments_command_block(available_deployments)
        shared.slack_client.chat_postMessage(channel=channel_id, blocks=deployments_menu["blocks"])
    else:
        command = f"kubectl {selected_command} {selected_sub_command} -n {selected_namespace}"
        k8s.run_kubectl_command(channel_id, command)


def handle_kubectl_pod_select(payload, channel_id):
    selected_pod = payload["actions"][0]["selected_option"]["value"]
    selected_namespace = shared.selected_actions.get(channel_id, {}).get("namespace", "")
    selected_command = shared.selected_actions.get(channel_id, {}).get("command")
    if selected_namespace:
        if selected_command in ["logs"]:
            command = f"kubectl {selected_command} {selected_pod} -n {selected_namespace}"
        else:
            command = f"kubectl {selected_command} pod {selected_pod} -n {selected_namespace}"
        k8s.run_kubectl_command(channel_id, command)
    else:
        shared.slack_client.chat_postMessage(channel=channel_id, text="Namespace not selected. Please start over.")


def handle_kubectl_deployment_select(payload, channel_id):
    selected_deployment = payload["actions"][0]["selected_option"]["value"]
    selected_namespace = shared.selected_actions.get(channel_id, {}).get("namespace", "")
    selected_command = shared.selected_actions.get(channel_id, {}).get("command")

    if selected_namespace:
        command = f"kubectl {selected_command} deployment {selected_deployment} -n {selected_namespace}"
        k8s.run_kubectl_command(channel_id, command)
    else:
        shared.slack_client.chat_postMessage(channel=channel_id, text="Namespace not selected. Please start over.")


def handle_argo_sub_command_select(payload, channel_id):
    selected_sub_command = payload["actions"][0]["selected_option"]["value"]
    if channel_id in shared.selected_actions:
        shared.selected_actions[channel_id]["sub_command"] = selected_sub_command

    if selected_sub_command in ["status", "revisions", "rollback"]:
        available_applications = argo.get_argo_applications()
        if available_applications:
            applications_menu = slack_blocks.build_argo_applications_block(available_applications)
            shared.slack_client.chat_postMessage(channel=channel_id, blocks=applications_menu["blocks"])
        else:
            shared.slack_client.chat_postMessage(channel=channel_id, text="❌ No ArgoCD applications found or error connecting to ArgoCD.")


def handle_argo_app_select(payload, channel_id):
    selected_app = payload["actions"][0]["selected_option"]["value"]
    selected_command = shared.selected_actions.get(channel_id, {}).get("command")
    selected_sub_command = shared.selected_actions.get(channel_id, {}).get("sub_command")

    if channel_id in shared.selected_actions:
        shared.selected_actions[channel_id]["app"] = selected_app

    if selected_command == "argo" and selected_sub_command == "status":
        argo.get_argo_application_status(channel_id, selected_app)
    elif selected_command == "argo" and selected_sub_command == "revisions":
        argo.get_argo_application_revisions(channel_id, selected_app)
    elif selected_command == "argo" and selected_sub_command == "rollback":
        available_revisions = argo.get_argo_application_revisions_for_rollback(selected_app)
        if available_revisions:
            revisions_menu = slack_blocks.build_argo_revisions_block(available_revisions)
            shared.slack_client.chat_postMessage(channel=channel_id, blocks=revisions_menu["blocks"])
        else:
            shared.slack_client.chat_postMessage(channel=channel_id, text="❌ No revisions found for this application or error fetching revisions.")
    else:
        shared.slack_client.chat_postMessage(channel=channel_id, text="Invalid command sequence. Please start over.")


def handle_argo_revision_select(payload, channel_id):
    selected_revision = payload["actions"][0]["selected_option"]["value"]
    selected_app = shared.selected_actions.get(channel_id, {}).get("app")
    selected_command = shared.selected_actions.get(channel_id, {}).get("command")
    selected_sub_command = shared.selected_actions.get(channel_id, {}).get("sub_command")

    if selected_command == "argo" and selected_sub_command == "rollback" and selected_app:
        # Send immediate acknowledgment
        shared.slack_client.chat_postMessage(
            channel=channel_id,
            text=f"🔄 Initiating rollback for `{selected_app}` to revision `{selected_revision}`...\nPlease wait, this may take a few moments."
        )

        # Perform rollback in a separate thread to avoid Slack timeout
        thread = Thread(target=argo.rollback_argo_application, args=(channel_id, selected_app, selected_revision))
        thread.start()
    else:
        shared.slack_client.chat_postMessage(channel=channel_id, text="Invalid rollback sequence. Please start over.")
