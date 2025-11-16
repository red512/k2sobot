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


def get_pod_logs(pod_name, namespace="default", lines=50):
    """Get logs from a pod"""
    try:
        cmd = ["kubectl", "logs", pod_name, "-n", namespace, "--tail", str(lines)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Timeout getting logs"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


def describe_pod(pod_name, namespace="default"):
    """Get detailed pod information"""
    try:
        cmd = ["kubectl", "describe", "pod", pod_name, "-n", namespace]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Timeout describing pod"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"
