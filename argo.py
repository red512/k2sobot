import subprocess
import logging
import shared_state as shared


def get_argo_applications():
    try:
        command = ["argocd", "app", "list", "-o", "name"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        applications = [app.strip() for app in result.stdout.strip().split('\n') if app.strip()]
        return applications
    except subprocess.CalledProcessError as e:
        logging.error("Error running argocd command: %s", e)
        return []


def get_argo_application_status(channel_id, app_name):
    try:
        command = ["argocd", "app", "get", app_name]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stdout.strip()
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"```\n{output}\n```")
    except subprocess.CalledProcessError as e:
        logging.error("Error running argocd command: %s", e)
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"Error executing command:\n```\n{e.stderr}\n```")


def get_argo_application_revisions(channel_id, app_name):
    try:
        command = ["argocd", "app", "history", app_name]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        output = result.stdout.strip()
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"```\n{output}\n```")
    except subprocess.CalledProcessError as e:
        logging.error("Error running argocd history command: %s", e)
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"Error executing command:\n```\n{e.stderr}\n```")


def get_argo_application_revisions_for_rollback(app_name):
    try:
        command = ["argocd", "app", "history", app_name, "-o", "id"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        revisions = [rev.strip() for rev in result.stdout.strip().split('\n') if rev.strip()]
        return revisions
    except subprocess.CalledProcessError as e:
        logging.error("Error getting revisions for rollback: %s", e)
        return []


def rollback_argo_application(channel_id, app_name, revision):
    try:
        command = ["argocd", "app", "rollback", app_name, revision]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

        # Extract key information from the output
        output = result.stdout.strip()
        lines = output.split('\n')

        # Find the summary section (usually starts with "Name:")
        summary_start = -1
        for i, line in enumerate(lines):
            if line.startswith('Name:'):
                summary_start = i
                break

        if summary_start != -1:
            # Get the summary section
            summary_lines = []
            for line in lines[summary_start:]:
                if line.startswith(('Name:', 'Project:', 'Sync Status:', 'Health Status:', 'Sync Revision:', 'Phase:', 'Duration:', 'Message:')):
                    summary_lines.append(line)
                elif line.startswith('GROUP') or not line.strip():
                    break

            summary = '\n'.join(summary_lines)
            shared.slack_client.chat_postMessage(
                channel=channel_id,
                text=f"✅ **Rollback completed for `{app_name}` to revision `{revision}`**\n```\n{summary}\n```"
            )
        else:
            # Fallback to a simple success message
            shared.slack_client.chat_postMessage(
                channel=channel_id,
                text=f"✅ **Rollback completed successfully**\nApplication: `{app_name}`\nRevision: `{revision}`"
            )

    except subprocess.CalledProcessError as e:
        logging.error("Error rolling back application: %s", e)
        error_message = e.stderr.strip()

        # Check for specific auto-sync error
        if "auto-sync is enabled" in error_message:
            shared.slack_client.chat_postMessage(
                channel=channel_id,
                text=f"⚠️ **Rollback blocked**: Auto-sync is enabled for `{app_name}`\n\n"
                     f"**Options to resolve:**\n"
                     f"• Disable auto-sync: `argocd app set {app_name} --sync-policy=none`\n"
                     f"• Use manual sync instead: `argocd app sync {app_name} --revision {revision}`\n"
                     f"• Or rollback via Git repository\n\n"
                     f"```\n{error_message}\n```"
            )
        else:
            shared.slack_client.chat_postMessage(channel=channel_id, text=f"❌ Rollback failed:\n```\n{error_message}\n```")


def run_argo_command(channel_id, command):
    try:
        logging.info("Running command: %s", command)
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"```\n{output}\n```")
    except subprocess.CalledProcessError as e:
        shared.slack_client.chat_postMessage(channel=channel_id, text=f"Error executing command:\n```\n{e.output}\n```")