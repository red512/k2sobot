"""
ArgoCD tools - thin wrapper around argo.py
"""
import logging
import subprocess
import argo

logger = logging.getLogger(__name__)


def get_applications():
    """Get all ArgoCD applications"""
    return argo.get_argo_applications()


def get_application_revisions(app_name):
    """Get available revisions for rollback"""
    return argo.get_argo_application_revisions_for_rollback(app_name)


def get_application_status(app_name):
    """Get ArgoCD application status"""
    try:
        command = ["argocd", "app", "get", app_name]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, timeout=15)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Timeout getting application status"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


def get_application_history(app_name):
    """Get ArgoCD application revision history"""
    try:
        command = ["argocd", "app", "history", app_name]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, timeout=15)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Timeout getting application history"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"


def sync_application(app_name, revision=None):
    """Sync ArgoCD application with optional revision"""
    try:
        command = ["argocd", "app", "sync", app_name]
        if revision:
            command.extend(["--revision", revision])
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True, timeout=30)
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "Error: Timeout syncing application"
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"
    except Exception as e:
        return f"Error: {str(e)}"