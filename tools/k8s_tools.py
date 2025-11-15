"""
Kubernetes tools - thin wrapper around k8s.py
"""
import logging
import subprocess
import k8s

logger = logging.getLogger(__name__)


def get_namespaces():
    """Get all Kubernetes namespaces"""
    return k8s.get_available_namespaces()


def get_pods(namespace="default"):
    """Get all pods in a namespace"""
    return k8s.get_available_pods(namespace)


def get_deployments(namespace="default"):
    """Get all deployments in a namespace"""
    return k8s.get_deployments(namespace)
