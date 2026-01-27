"""Azure DevOps integration module for git-maestro."""

import re
import requests
from typing import Optional, Tuple


def parse_azure_url(url: str) -> Optional[Tuple[str, str, str]]:
    """Parse Azure DevOps URL to extract organization, project, and repository name.

    Supports both HTTPS and SSH URL formats:
    - HTTPS: https://dev.azure.com/{org}/{project}/_git/{repo}
    - SSH: git@ssh.dev.azure.com:v3/{org}/{project}/{repo}

    Args:
        url: Remote URL from git config

    Returns:
        Tuple of (org, project, repo) or None if URL doesn't match Azure DevOps format
    """
    if not url:
        return None

    # Try HTTPS format: https://dev.azure.com/{org}/{project}/_git/{repo}
    https_match = re.match(
        r"https?://dev\.azure\.com/([^/]+)/([^/]+)/_git/([^/]+?)(?:\.git)?/?$",
        url,
    )
    if https_match:
        org, project, repo = https_match.groups()
        return (org, project, repo)

    # Try SSH format: git@ssh.dev.azure.com:v3/{org}/{project}/{repo}
    ssh_match = re.match(
        r"git@ssh\.dev\.azure\.com:v3/([^/]+)/([^/]+)/([^/]+?)(?:\.git)?/?$",
        url,
    )
    if ssh_match:
        org, project, repo = ssh_match.groups()
        return (org, project, repo)

    # Try visualstudio.com format (legacy): https://{org}.visualstudio.com/{project}/_git/{repo}
    visualstudio_match = re.match(
        r"https?://([^.]+)\.visualstudio\.com/([^/]+)/_git/([^/]+?)(?:\.git)?/?$",
        url,
    )
    if visualstudio_match:
        org, project, repo = visualstudio_match.groups()
        return (org, project, repo)

    return None


def get_org_project_from_url(url: str) -> Optional[Tuple[str, str]]:
    """Extract organization and project from Azure DevOps URL.

    Args:
        url: Remote URL from git config

    Returns:
        Tuple of (org, project) or None if URL doesn't match Azure DevOps format
    """
    parsed = parse_azure_url(url)
    if parsed:
        org, project, _ = parsed
        return (org, project)
    return None


class AzureClient:
    """Azure DevOps API client wrapper."""

    def __init__(self, organization: str, project: str, personal_access_token: str):
        """Initialize Azure DevOps client.

        Args:
            organization: Azure DevOps organization name
            project: Project name within the organization
            personal_access_token: PAT for authentication
        """
        self.organization = organization
        self.project = project
        self.token = personal_access_token
        self.base_url = f"https://dev.azure.com/{organization}"

        # Import here to avoid hard dependency if azure-devops not installed
        try:
            from azure.devops.connection import Connection
            from msrest.authentication import BasicAuthentication

            self.Connection = Connection
            self.BasicAuthentication = BasicAuthentication
        except ImportError:
            self.Connection = None
            self.BasicAuthentication = None

    def _get_connection(self):
        """Get authenticated Azure DevOps connection."""
        if not self.Connection:
            raise ImportError(
                "azure-devops package not installed. Install with: pip install azure-devops"
            )

        # Create basic auth
        credentials = self.BasicAuthentication("", self.token)

        # Create connection
        connection = self.Connection(
            base_url=self.base_url,
            creds=credentials,
        )

        return connection

    def get_pipelines(self) -> list:
        """Get list of pipelines in the project.

        Returns:
            List of pipeline definitions
        """
        connection = self._get_connection()
        pipelines_client = connection.clients.get_pipelines_client()

        pipelines = pipelines_client.list_pipelines(self.project)
        return list(pipelines) if pipelines else []

    def get_pipeline_runs(self, pipeline_id: int, top: int = 10) -> list:
        """Get recent runs for a pipeline.

        Args:
            pipeline_id: Pipeline ID
            top: Number of recent runs to return

        Returns:
            List of pipeline runs
        """
        connection = self._get_connection()
        pipelines_client = connection.clients.get_pipelines_client()

        try:
            # Try with top parameter first (newer SDK versions)
            runs = pipelines_client.list_runs(
                self.project,
                pipeline_id=pipeline_id,
                top=top,
            )
        except TypeError:
            # Fall back to no top parameter (older SDK versions)
            runs = pipelines_client.list_runs(
                self.project,
                pipeline_id=pipeline_id,
            )

        # Convert to list and limit if necessary
        run_list = list(runs) if runs else []
        return run_list[:top] if run_list else []

    def get_run(self, pipeline_id: int, run_id: int):
        """Get details for a specific pipeline run.

        Args:
            pipeline_id: Pipeline ID
            run_id: Run ID

        Returns:
            Run object with details
        """
        connection = self._get_connection()
        pipelines_client = connection.clients.get_pipelines_client()

        run = pipelines_client.get_run(
            self.project,
            pipeline_id=pipeline_id,
            run_id=run_id,
        )
        return run

    def get_run_logs(self, pipeline_id: int, run_id: int) -> bytes:
        """Get logs for a pipeline run.

        Args:
            pipeline_id: Pipeline ID
            run_id: Run ID

        Returns:
            Log content as bytes
        """
        connection = self._get_connection()
        pipelines_client = connection.clients.get_pipelines_client()

        logs = pipelines_client.get_log(
            self.project,
            pipeline_id=pipeline_id,
            run_id=run_id,
        )
        return logs

    def list_run_logs(self, pipeline_id: int, run_id: int) -> list:
        """Get list of available logs for a pipeline run.

        Args:
            pipeline_id: Pipeline ID
            run_id: Run ID

        Returns:
            List of log objects with id, url, line_count, etc.
        """
        connection = self._get_connection()
        pipelines_client = connection.clients.get_pipelines_client()

        log_collection = pipelines_client.list_logs(self.project, pipeline_id, run_id)
        return (
            list(log_collection.logs) if log_collection and log_collection.logs else []
        )

    def get_logs_for_stage(
        self, pipeline_id: int, run_id: int, stage_id: str
    ) -> Optional[bytes]:
        """Get logs for a specific stage in a pipeline run.

        Args:
            pipeline_id: Pipeline ID
            run_id: Run ID
            stage_id: Stage ID (log ID)

        Returns:
            Log content as bytes, or None if error
        """
        connection = self._get_connection()
        pipelines_client = connection.clients.get_pipelines_client()

        try:
            # Get log object with expand=1 to get signed content URL
            log_obj = pipelines_client.get_log(
                self.project,
                pipeline_id=pipeline_id,
                run_id=run_id,
                log_id=int(stage_id),
                expand=1,  # Expand to get signed_content with temporary auth URL
            )

            # Download content from the signed URL (no auth needed)
            if log_obj and log_obj.signed_content and log_obj.signed_content.url:
                response = requests.get(log_obj.signed_content.url)
                if response.status_code == 200:
                    return response.content

            return None
        except Exception:
            # If stage-specific logs not available, try full run logs
            try:
                return self.get_run_logs(pipeline_id, run_id)
            except Exception:
                return None

    def get_build_timeline(self, build_id: int):
        """Get timeline with all jobs, tasks, and steps for a build.

        Note: In Azure DevOps, Pipeline run_id == Build build_id

        Args:
            build_id: Build ID (same as pipeline run_id)

        Returns:
            Timeline object with records array, or None if error
        """
        try:
            connection = self._get_connection()
            build_client = connection.clients.get_build_client()

            timeline = build_client.get_build_timeline(
                project=self.project, build_id=build_id
            )
            return timeline
        except Exception:
            return None

    def get_build_log_content(self, build_id: int, log_id: int) -> Optional[str]:
        """Get actual log content for a specific task/step.

        Args:
            build_id: Build ID (same as pipeline run_id)
            log_id: Log ID from timeline record's log.id field

        Returns:
            Log content as string, or None if error
        """
        try:
            connection = self._get_connection()
            build_client = connection.clients.get_build_client()

            log_content = build_client.get_build_log(
                project=self.project, build_id=build_id, log_id=log_id
            )

            # The response might be a generator/stream - read it properly
            if log_content:
                if isinstance(log_content, str):
                    return log_content
                else:
                    # Handle generator - try to iterate and collect chunks
                    try:
                        chunks = []
                        for chunk in log_content:
                            if isinstance(chunk, bytes):
                                chunks.append(chunk.decode("utf-8", errors="replace"))
                            else:
                                chunks.append(str(chunk))
                        content = "".join(chunks)
                        return content if content else None
                    except TypeError:
                        # Not iterable, just convert to string
                        return str(log_content) if log_content else None
            return None
        except Exception:
            return None

    def get_complete_execution_logs(self, build_id: int) -> dict:
        """Get complete logs with task structure for AI debugging.

        This retrieves the full execution logs including Python setup, dependency
        installation, and test output - everything needed for AI-assisted debugging.

        Also extracts timeline diagnostic issues (errors/warnings that occur before
        task execution, like parallelism quota errors).

        Args:
            build_id: Build ID (same as pipeline run_id)

        Returns:
            Dict with timeline structure and all logs:
            {
                'build_id': int,
                'timeline_id': str,
                'jobs': [
                    {
                        'id': str,
                        'name': str,
                        'type': str,
                        'state': str,
                        'result': str,
                        'start_time': str (ISO format),
                        'finish_time': str (ISO format),
                        'error_count': int,
                        'warning_count': int,
                        'issues': [{'message': str, 'type': str}],  # Diagnostic messages
                        'log_content': str,
                        'tasks': [
                            {
                                'id': str,
                                'name': str,
                                'type': str,
                                'state': str,
                                'result': str,
                                'start_time': str,
                                'finish_time': str,
                                'error_count': int,
                                'warning_count': int,
                                'issues': [{'message': str, 'type': str}],
                                'log_content': str
                            }
                        ]
                    }
                ]
            }
        """
        timeline = self.get_build_timeline(build_id)

        result = {
            "build_id": build_id,
            "timeline_id": timeline.id if timeline else None,
            "jobs": [],
        }

        if not timeline or not timeline.records:
            return result

        # Organize records by ID for easy lookup
        records_by_id = {r.id: r for r in timeline.records}

        for record in timeline.records:
            # Skip nested records - we'll nest them under their parent
            if record.parent_id and record.parent_id in records_by_id:
                continue

            job_info = {
                "id": record.id,
                "name": record.name,
                "type": record.type,
                "state": record.state,
                "result": getattr(record, "result", None),
                "start_time": (
                    record.start_time.isoformat()
                    if hasattr(record, "start_time") and record.start_time
                    else None
                ),
                "finish_time": (
                    record.finish_time.isoformat()
                    if hasattr(record, "finish_time") and record.finish_time
                    else None
                ),
                "error_count": getattr(record, "error_count", 0),
                "warning_count": getattr(record, "warning_count", 0),
                "issues": self._extract_issues(record),
                "log_content": None,
                "tasks": [],
            }

            # Get log content if available
            if hasattr(record, "log") and record.log and hasattr(record.log, "id"):
                log_content = self.get_build_log_content(build_id, record.log.id)
                if log_content:
                    job_info["log_content"] = log_content

            # Find and add child tasks
            for child in timeline.records:
                if child.parent_id == record.id:
                    task_info = {
                        "id": child.id,
                        "name": child.name,
                        "type": child.type,
                        "state": child.state,
                        "result": getattr(child, "result", None),
                        "start_time": (
                            child.start_time.isoformat()
                            if hasattr(child, "start_time") and child.start_time
                            else None
                        ),
                        "finish_time": (
                            child.finish_time.isoformat()
                            if hasattr(child, "finish_time") and child.finish_time
                            else None
                        ),
                        "error_count": getattr(child, "error_count", 0),
                        "warning_count": getattr(child, "warning_count", 0),
                        "issues": self._extract_issues(child),
                        "log_content": None,
                    }

                    # Collect issues from grandchildren (e.g., Job records under Phase records)
                    for grandchild in timeline.records:
                        if grandchild.parent_id == child.id:
                            grandchild_issues = self._extract_issues(grandchild)
                            task_info["issues"].extend(grandchild_issues)

                    # Get task log content
                    if hasattr(child, "log") and child.log and hasattr(child.log, "id"):
                        task_log = self.get_build_log_content(build_id, child.log.id)
                        if task_log:
                            task_info["log_content"] = task_log

                    job_info["tasks"].append(task_info)

            result["jobs"].append(job_info)

        return result

    def _extract_issues(self, record) -> list:
        """Extract diagnostic issues from a timeline record.

        Args:
            record: Timeline record object

        Returns:
            List of issue dicts with 'message' and 'type' keys
        """
        issues = []
        if hasattr(record, "issues") and record.issues:
            for issue in record.issues:
                issue_dict = {
                    "message": getattr(issue, "message", str(issue)),
                    "type": getattr(issue, "type", "unknown"),
                }
                issues.append(issue_dict)
        return issues
