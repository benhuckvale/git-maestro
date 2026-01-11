"""Action to fetch GitLab Pipelines logs from specific runs."""

from pathlib import Path
from typing import Optional, Any
from rich.console import Console
from .base import Action
from git_maestro.state import RepoState

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class GetGitlabPipelinesAction(Action):
    """Fetch logs from specific GitLab Pipelines runs and jobs."""

    def __init__(self):
        super().__init__()
        self.name = "View GitLab Pipelines Run History and Logs"
        self.description = "Browse and download logs from specific GitLab Pipelines runs"
        self.emoji = "📋"
        self.category = "info"
        self.storage_dir = "traces"  # Will create .git-maestro/traces/

    def is_applicable(self, state: RepoState) -> bool:
        """Only show if we have a GitLab remote with GitLab Pipelines history."""
        return (
            state.has_fact("gitlab_pipelines_checked")
            and state.get_fact("gitlab_pipelines_has_runs", False)
        )

    def _get_stored_token(self) -> Optional[str]:
        """Get stored GitLab token."""
        if not CONFIG_FILE.exists():
            return None
        try:
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    if line.startswith("gitlab="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            return None
        return None

    def _get_gitlab_client(self, remote_url: str, token: str):
        """Get authenticated GitLab client."""
        try:
            from git_maestro.gitlab import GitLabClient
            return GitLabClient(remote_url, token)
        except Exception:
            return None

    def execute(self, state: RepoState) -> bool:
        """Execute the action to list recent pipelines."""
        pipelines = self.list_recent_runs(state, count=15)
        if pipelines is None:
            return False
        return len(pipelines) > 0

    def list_recent_runs(
        self, state: RepoState, count: int = 10
    ) -> Optional[list[dict[str, Any]]]:
        """List recent pipeline runs.

        Args:
            state: Repository state
            count: Number of recent runs to return

        Returns:
            List of pipeline info dicts with keys: pipeline_id, status, ref, commit_sha, duration, created_at, web_url
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitLab token found[/bold red]")
                return None

            # Connect to GitLab
            client = self._get_gitlab_client(state.remote_url, token)
            if not client:
                console.print("[bold red]✗ Could not connect to GitLab[/bold red]")
                return None

            # Get recent pipelines
            pipelines = client.get_pipelines(per_page=count)

            if not pipelines:
                console.print("[bold yellow]No pipelines found[/bold yellow]")
                return []

            # Format pipeline info
            pipelines_info = []
            for pipeline in pipelines:
                # Calculate duration
                if pipeline.duration:
                    duration_str = self._format_duration(int(pipeline.duration))
                else:
                    duration_str = "—"

                created_str = pipeline.created_at[:16] if pipeline.created_at else "—"
                commit_sha = pipeline.sha[:8] if pipeline.sha else "—"

                pipelines_info.append(
                    {
                        "pipeline_id": pipeline.id,
                        "status": pipeline.status,
                        "ref": pipeline.ref or "—",
                        "commit_sha": commit_sha,
                        "duration": duration_str,
                        "created_at": created_str,
                        "web_url": pipeline.web_url,
                    }
                )

                # Display in console
                console.print(
                    f"  [{created_str}] {pipeline.status:10s} | {commit_sha} | {pipeline.ref} (ID: {pipeline.id})"
                )

            return pipelines_info

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return None

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable format."""
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if minutes < 60:
            return f"{minutes}m {remaining_seconds}s"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes}m"

    def get_run_jobs(
        self, state: RepoState, pipeline_id: int
    ) -> Optional[list[dict[str, Any]]]:
        """Get detailed job information for a specific pipeline.

        Args:
            state: Repository state
            pipeline_id: GitLab pipeline ID

        Returns:
            List of job info dicts with keys: job_id, name, stage, status, duration, web_url, failure_reason
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitLab token found[/bold red]")
                return None

            # Connect to GitLab
            client = self._get_gitlab_client(state.remote_url, token)
            if not client:
                console.print("[bold red]✗ Could not connect to GitLab[/bold red]")
                return None

            # Get all jobs for the pipeline
            jobs = client.get_pipeline_jobs(pipeline_id)

            if not jobs:
                console.print(f"[yellow]No jobs found in pipeline {pipeline_id}[/yellow]")
                return []

            # Format job info
            jobs_info = []
            for job in jobs:
                # Calculate duration
                if job.duration:
                    duration_str = self._format_duration(int(job.duration))
                else:
                    duration_str = "—"

                jobs_info.append(
                    {
                        "job_id": job.id,
                        "name": job.name or "—",
                        "stage": job.stage or "—",
                        "status": job.status,
                        "duration": duration_str,
                        "web_url": job.web_url,
                        "failure_reason": getattr(job, "failure_reason", None),
                    }
                )

            return jobs_info

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return None

    def check_job_status(
        self, state: RepoState, pipeline_id: int, job_id: Optional[int] = None
    ) -> Optional[dict[str, Any]]:
        """Check the status of a job or pipeline without downloading logs.

        Args:
            state: Repository state
            pipeline_id: GitLab pipeline ID
            job_id: Optional specific job ID. If not provided, returns pipeline status.

        Returns:
            Dict with status info, or None if error:
            For pipeline: {pipeline_id, status, ref, sha, created_at, updated_at, web_url}
            For job: {job_id, name, stage, status, created_at, started_at, finished_at, web_url, failure_reason}
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                return None

            # Connect to GitLab
            client = self._get_gitlab_client(state.remote_url, token)
            if not client:
                return None

            # If job_id specified, return job status
            if job_id:
                job_status = client.get_job_status(job_id)
                return job_status
            else:
                # Return pipeline status
                pipeline_status = client.get_pipeline_status(pipeline_id)
                return {
                    "pipeline_id": pipeline_id,
                    **pipeline_status,
                }

        except Exception:
            return None

    def download_job_logs(
        self, state: RepoState, pipeline_id: int, job_id: int
    ) -> str | None:
        """Download logs for a specific job in a pipeline.

        Args:
            state: Repository state
            pipeline_id: GitLab pipeline ID
            job_id: Specific job ID to download

        Returns:
            Path to downloaded log file, or None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitLab token found[/bold red]")
                return None

            # Connect to GitLab
            client = self._get_gitlab_client(state.remote_url, token)
            if not client:
                console.print("[bold red]✗ Could not connect to GitLab[/bold red]")
                return None

            # Get the job
            job = client.get_job(job_id)

            console.print(
                f"\n[bold cyan]Downloading logs for job '{job.name}' (ID: {job_id})...[/bold cyan]\n"
            )

            # Create storage directory with pipeline ID
            storage_path = self.get_storage_path(state)
            pipeline_dir = storage_path / f"pipeline-{pipeline_id}"
            pipeline_dir.mkdir(parents=True, exist_ok=True)

            # Download log to file
            import re
            safe_name = re.sub(r"[^\w\-.]", "_", job.name)
            log_file = pipeline_dir / f"job-{job.id}-{safe_name}.log"

            if client.download_job_log(job_id, log_file):
                console.print(f"[bold green]✓ Downloaded job logs[/bold green]")
                console.print(f"[dim]Location: {log_file}[/dim]")
                return str(log_file)
            else:
                console.print(f"[bold red]✗ Failed to download logs[/bold red]")
                return None

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return None
