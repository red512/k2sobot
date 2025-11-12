import json
import os
import subprocess
from threading import Thread
from flask import Flask, Response, request
from slack_sdk import WebClient
from slackeventsapi import SlackEventAdapter
import slack_blocks
import logging
import k8s, shared_state as shared

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
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"```\n{output}\n```")
    except subprocess.CalledProcessError as e:
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"Error executing command:\n```\n{e.output}\n```")