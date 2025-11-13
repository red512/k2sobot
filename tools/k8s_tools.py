"""
Kubernetes tools - thin wrapper around k8s.py
"""
import logging
import subprocess
import k8s

logger = logging.getLogger(__name__)


def get_namespaces():
    """Get all Kubernetes namespaces"""
    try:
        namespaces = k8s.get_available_namespaces()
        return {"namespaces": namespaces, "count": len(namespaces)}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}


def get_pods(namespace="default"):
    """Get all pods in a namespace"""
    try:
        pods = k8s.get_available_pods(namespace)
        return {
            "namespace": namespace,
            "pods": [{"name": p} for p in pods],
            "count": len(pods)
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}


def get_deployments(namespace="default"):
    """Get all deployments in a namespace"""
    try:
        deployments = k8s.get_deployments(namespace)
        return {
            "namespace": namespace,
            "deployments": [{"name": d} for d in deployments],
            "count": len(deployments)
        }
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"error": str(e)}


def get_pod_logs(pod_name, namespace="default", lines=50):
    """Get logs from a pod"""
    try:
        cmd = ["kubectl", "logs", pod_name, "-n", namespace, "--tail", str(lines)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        return {"pod": pod_name, "namespace": namespace, "logs": result.stdout}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr}
    except Exception as e:
        return {"error": str(e)}


def describe_pod(pod_name, namespace="default"):
    """Get detailed pod information"""
    try:
        cmd = ["kubectl", "describe", "pod", pod_name, "-n", namespace]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        return {"pod": pod_name, "namespace": namespace, "description": result.stdout}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr}
    except Exception as e:
        return {"error": str(e)}