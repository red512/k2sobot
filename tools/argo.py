"""
ArgoCD tools for application management
Provides functionality to list apps, check status, manage revisions, and perform rollouts
"""
import subprocess
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def _run_argocd_command(cmd: List[str], timeout: int = 30) -> Dict[str, Any]:
    """Helper function to run ArgoCD CLI commands"""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            check=True
        )
        return {
            "success": True,
            "output": result.stdout.strip(),
            "error": None
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"ArgoCD command failed: {' '.join(cmd)} - {e.stderr}")
        return {
            "success": False,
            "output": None,
            "error": e.stderr.strip() if e.stderr else str(e)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "output": None,
            "error": f"Command timed out after {timeout} seconds"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "output": None,
            "error": "ArgoCD CLI not found. Please install 'argocd' CLI tool."
        }

def list_applications() -> Dict[str, Any]:
    """
    List all ArgoCD applications
    
    Returns:
        Dict containing list of applications with their basic info
        
    Example:
        >>> list_applications()
        {
            'applications': [
                {'name': 'app1', 'namespace': 'argocd', 'server': 'https://kubernetes.default.svc'},
                {'name': 'app2', 'namespace': 'argocd', 'server': 'https://kubernetes.default.svc'}
            ],
            'count': 2
        }
    """
    result = _run_argocd_command(["argocd", "app", "list", "-o", "json"])
    
    if not result["success"]:
        return {
            "error": f"Failed to list applications: {result['error']}",
            "applications": [],
            "count": 0
        }
    
    try:
        if not result["output"]:
            return {
                "applications": [],
                "count": 0,
                "message": "No applications found"
            }
            
        apps_data = json.loads(result["output"])
        applications = []
        
        for app in apps_data:
            applications.append({
                "name": app.get("metadata", {}).get("name", "unknown"),
                "namespace": app.get("metadata", {}).get("namespace", "unknown"),
                "server": app.get("spec", {}).get("destination", {}).get("server", "unknown"),
                "sync_status": app.get("status", {}).get("sync", {}).get("status", "unknown"),
                "health_status": app.get("status", {}).get("health", {}).get("status", "unknown")
            })
        
        return {
            "applications": applications,
            "count": len(applications),
            "formatted": f"🚀 **ArgoCD Applications ({len(applications)}):**\n" + 
                        "\n".join([
                            f"• `{app['name']}` - Sync: {app['sync_status']} | Health: {app['health_status']}"
                            for app in applications
                        ])
        }
        
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse ArgoCD response: {str(e)}",
            "applications": [],
            "count": 0
        }

def get_application_status(app_name: str) -> Dict[str, Any]:
    """
    Get detailed status of a specific ArgoCD application
    
    Args:
        app_name (str): Name of the application
        
    Returns:
        Dict containing detailed application status
        
    Example:
        >>> get_application_status("my-app")
        {
            'name': 'my-app',
            'sync_status': 'Synced',
            'health_status': 'Healthy',
            'revision': 'abc123'
        }
    """
    result = _run_argocd_command(["argocd", "app", "get", app_name, "-o", "json"])
    
    if not result["success"]:
        return {
            "error": f"Failed to get application status: {result['error']}",
            "name": app_name
        }
    
    try:
        app_data = json.loads(result["output"])
        status = app_data.get("status", {})
        spec = app_data.get("spec", {})
        
        sync_info = status.get("sync", {})
        health_info = status.get("health", {})
        
        return {
            "name": app_name,
            "sync_status": sync_info.get("status", "Unknown"),
            "health_status": health_info.get("status", "Unknown"),
            "current_revision": sync_info.get("revision", "Unknown"),
            "target_revision": spec.get("source", {}).get("targetRevision", "Unknown"),
            "repo_url": spec.get("source", {}).get("repoURL", "Unknown"),
            "path": spec.get("source", {}).get("path", "Unknown"),
            "namespace": spec.get("destination", {}).get("namespace", "Unknown"),
            "server": spec.get("destination", {}).get("server", "Unknown"),
            "formatted": f"📱 **Application: `{app_name}`**\n" + 
                        f"🔄 Sync Status: {sync_info.get('status', 'Unknown')}\n" +
                        f"❤️ Health Status: {health_info.get('status', 'Unknown')}\n" +
                        f"📝 Current Revision: `{sync_info.get('revision', 'Unknown')[:8]}...`\n" +
                        f"🎯 Target Revision: `{spec.get('source', {}).get('targetRevision', 'Unknown')}`\n" +
                        f"📂 Repository: {spec.get('source', {}).get('repoURL', 'Unknown')}\n" +
                        f"📁 Path: {spec.get('source', {}).get('path', 'Unknown')}"
        }
        
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse application status: {str(e)}",
            "name": app_name
        }

def get_application_revisions(app_name: str, limit: int = 10) -> Dict[str, Any]:
    """
    Get revision history of a specific ArgoCD application
    
    Args:
        app_name (str): Name of the application
        limit (int): Number of revisions to retrieve (default: 10)
        
    Returns:
        Dict containing revision history
        
    Example:
        >>> get_application_revisions("my-app", 5)
        {
            'name': 'my-app',
            'revisions': [
                {'id': 1, 'revision': 'abc123', 'deployed_at': '2023-01-01T10:00:00Z'},
                {'id': 2, 'revision': 'def456', 'deployed_at': '2023-01-01T11:00:00Z'}
            ]
        }
    """
    result = _run_argocd_command(["argocd", "app", "history", app_name, "-o", "json"])
    
    if not result["success"]:
        return {
            "error": f"Failed to get application revisions: {result['error']}",
            "name": app_name,
            "revisions": []
        }
    
    try:
        if not result["output"]:
            return {
                "name": app_name,
                "revisions": [],
                "message": "No revision history found"
            }
            
        revisions_data = json.loads(result["output"])
        revisions = []
        
        # Sort by deployment date (newest first) and limit
        sorted_revisions = sorted(
            revisions_data, 
            key=lambda x: x.get("deployedAt", ""), 
            reverse=True
        )[:limit]
        
        for rev in sorted_revisions:
            revisions.append({
                "id": rev.get("id", "unknown"),
                "revision": rev.get("revision", "unknown"),
                "deployed_at": rev.get("deployedAt", "unknown"),
                "deployed_by": rev.get("deployStartedAt", "unknown"),
                "source": rev.get("source", {})
            })
        
        return {
            "name": app_name,
            "revisions": revisions,
            "count": len(revisions),
            "formatted": f"📚 **Revision History for `{app_name}` (last {len(revisions)}):**\n" + 
                        "\n".join([
                            f"• **#{rev['id']}** `{rev['revision'][:8]}...` - {rev['deployed_at']}"
                            for rev in revisions
                        ])
        }
        
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse revision history: {str(e)}",
            "name": app_name,
            "revisions": []
        }

def prepare_rollback(app_name: str, revision_id: int) -> Dict[str, Any]:
    """
    Prepare rollback information (confirmation step before actual rollback)
    
    Args:
        app_name (str): Name of the application
        revision_id (int): Revision ID to rollback to
        
    Returns:
        Dict containing rollback preparation info and confirmation message
        
    Example:
        >>> prepare_rollback("my-app", 5)
        {
            'app_name': 'my-app',
            'revision_id': 5,
            'confirmation_required': True,
            'message': 'Ready to rollback my-app to revision #5...'
        }
    """
    # First, get current status
    current_status = get_application_status(app_name)
    if "error" in current_status:
        return current_status
    
    # Get revision history to validate the target revision
    revisions = get_application_revisions(app_name, 20)  # Get more revisions to find the target
    if "error" in revisions:
        return revisions
    
    # Find the target revision
    target_revision = None
    for rev in revisions["revisions"]:
        if rev["id"] == revision_id:
            target_revision = rev
            break
    
    if not target_revision:
        return {
            "error": f"Revision #{revision_id} not found for application {app_name}",
            "app_name": app_name,
            "revision_id": revision_id
        }
    
    return {
        "app_name": app_name,
        "revision_id": revision_id,
        "target_revision": target_revision,
        "current_revision": current_status.get("current_revision", "unknown"),
        "confirmation_required": True,
        "formatted": f"⚠️ **Rollback Confirmation Required**\n\n" +
                    f"🚀 **Application:** `{app_name}`\n" +
                    f"📝 **Current Revision:** `{current_status.get('current_revision', 'unknown')[:8]}...`\n" +
                    f"🎯 **Target Revision:** `{target_revision['revision'][:8]}...` (#{revision_id})\n" +
                    f"📅 **Target Deployed:** {target_revision['deployed_at']}\n\n" +
                    f"❓ **Are you sure you want to proceed with this rollback?**\n" +
                    f"💡 To confirm, say: `rollback {app_name} to revision {revision_id} confirmed`"
    }

def execute_rollback(app_name: str, revision_id: int, confirmed: bool = False) -> Dict[str, Any]:
    """
    Execute rollback to a specific revision (requires confirmation)
    
    Args:
        app_name (str): Name of the application
        revision_id (int): Revision ID to rollback to
        confirmed (bool): Whether the rollback is confirmed
        
    Returns:
        Dict containing rollback execution result
        
    Example:
        >>> execute_rollback("my-app", 5, confirmed=True)
        {
            'app_name': 'my-app',
            'revision_id': 5,
            'success': True,
            'message': 'Rollback initiated successfully'
        }
    """
    if not confirmed:
        return prepare_rollback(app_name, revision_id)
    
    result = _run_argocd_command([
        "argocd", "app", "rollback", app_name, str(revision_id)
    ])
    
    if not result["success"]:
        return {
            "error": f"Failed to execute rollback: {result['error']}",
            "app_name": app_name,
            "revision_id": revision_id,
            "success": False
        }
    
    return {
        "app_name": app_name,
        "revision_id": revision_id,
        "success": True,
        "message": result["output"],
        "formatted": f"✅ **Rollback Initiated Successfully**\n\n" +
                    f"🚀 **Application:** `{app_name}`\n" +
                    f"🎯 **Rolled back to revision:** #{revision_id}\n" +
                    f"📝 **Status:** {result['output']}\n\n" +
                    f"💡 Use `get application status {app_name}` to check rollback progress"
    }

def sync_application(app_name: str) -> Dict[str, Any]:
    """
    Trigger sync for a specific ArgoCD application
    
    Args:
        app_name (str): Name of the application
        
    Returns:
        Dict containing sync operation result
        
    Example:
        >>> sync_application("my-app")
        {
            'app_name': 'my-app',
            'success': True,
            'message': 'Sync operation initiated'
        }
    """
    result = _run_argocd_command(["argocd", "app", "sync", app_name])
    
    if not result["success"]:
        return {
            "error": f"Failed to sync application: {result['error']}",
            "app_name": app_name,
            "success": False
        }
    
    return {
        "app_name": app_name,
        "success": True,
        "message": result["output"],
        "formatted": f"🔄 **Sync Initiated for `{app_name}`**\n\n" +
                    f"📝 **Status:** {result['output']}\n\n" +
                    f"💡 Use `get application status {app_name}` to check sync progress"
    }
