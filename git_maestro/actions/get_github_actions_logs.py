"""Action to fetch GitHub Actions logs from specific runs."""

import re
from pathlib import Path
from typing import Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from github import Github, GithubException
from .base import Action
from git_maestro.state import RepoState

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class GetGithubActionsLogsAction(Action):
    """Fetch logs from specific GitHub Actions runs and jobs."""

    def __init__(self):
        super().__init__()
        self.name = "View GitHub Actions Run History and Logs"
        self.description = "Browse and download logs from specific GitHub Actions runs"
        self.emoji = "📋"
        self.category = "info"
        self.storage_dir = "traces"  # Will create .git-maestro/traces/

    def is_applicable(self, state: RepoState) -> bool:
        """Only show if we have a GitHub remote with GitHub Actions history."""
        return (
            state.has_fact("github_actions_checked")
            and state.get_fact("github_actions_has_runs", False)
        )

    def _get_stored_token(self) -> Optional[str]:
        """Get stored GitHub token."""
        if not CONFIG_FILE.exists():
            return None
        try:
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    if line.startswith("github="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            return None
        return None

    def _parse_github_url(self, remote_url: str) -> Optional[tuple[str, str]]:
        """Parse GitHub URL to extract owner and repo name."""
        match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
        if match:
            return match.group(1), match.group(2)
        return None

    def _get_github_client(self, token: str) -> Optional[Github]:
        """Get authenticated GitHub client."""
        try:
            return Github(token)
        except Exception:
            return None

    def execute(self, state: RepoState) -> bool:
        """Execute the action to list recent runs."""
        runs = self.list_recent_runs(state, count=15)
        if runs is None:
            return False
        return len(runs) > 0

    def list_recent_runs(self, state: RepoState, count: int = 10) -> Optional[list[dict[str, Any]]]:
        """List recent workflow runs.

        Args:
            state: Repository state
            count: Number of recent runs to return

        Returns:
            List of run info dicts with keys: run_id, status, conclusion, duration, created_at, branch, commit_sha, name
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitHub token found[/bold red]")
                return None

            # Parse GitHub URL
            parsed = self._parse_github_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse GitHub URL from remote[/bold red]"
                )
                return None

            owner, repo = parsed

            # Connect to GitHub
            g = Github(token)
            github_repo = g.get_repo(f"{owner}/{repo}")

            # Get workflow runs for current branch
            current_branch = state.branch_name or "main"
            runs = github_repo.get_workflow_runs(branch=current_branch)
            run_list = list(runs[:count])

            if not run_list:
                console.print(
                    f"[bold yellow]No workflow runs found for branch '{current_branch}'[/bold yellow]"
                )
                return []

            # Format run info
            runs_info = []
            for run in run_list:
                # Calculate duration
                if run.status == "completed" and run.created_at and run.updated_at:
                    duration = (run.updated_at - run.created_at).total_seconds()
                    duration_str = self._format_duration(int(duration))
                else:
                    duration_str = "—"

                created_str = (
                    run.created_at.strftime("%Y-%m-%d %H:%M") if run.created_at else "—"
                )
                status_text = (
                    run.conclusion if run.status == "completed" else run.status
                )
                commit_sha = run.head_sha[:7] if run.head_sha else "—"

                runs_info.append(
                    {
                        "run_id": run.id,
                        "status": run.status,
                        "conclusion": run.conclusion,
                        "duration": duration_str,
                        "created_at": created_str,
                        "branch": current_branch,
                        "commit_sha": commit_sha,
                        "name": run.name or "—",
                        "url": run.html_url,
                    }
                )

                # Display in console
                console.print(
                    f"  [{created_str}] {status_text:10s} | {commit_sha} | {run.name or '—'} (ID: {run.id})"
                )

            return runs_info

        except GithubException as e:
            error_msg = e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
            console.print(f"[bold red]✗ GitHub API error: {error_msg}[/bold red]")
            return None
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

    def get_run_jobs(self, state: RepoState, run_id: int) -> Optional[list[dict[str, Any]]]:
        """Get detailed job information for a specific run.

        Args:
            state: Repository state
            run_id: GitHub Actions run ID

        Returns:
            List of job info dicts with keys: job_id, name, status, conclusion, duration, url
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitHub token found[/bold red]")
                return None

            # Parse GitHub URL
            parsed = self._parse_github_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse GitHub URL from remote[/bold red]"
                )
                return None

            owner, repo = parsed

            # Connect to GitHub
            g = Github(token)
            github_repo = g.get_repo(f"{owner}/{repo}")
            run = github_repo.get_workflow_run(run_id)

            # Get all jobs
            jobs = list(run.jobs())

            if not jobs:
                console.print(f"[yellow]No jobs found in run {run_id}[/yellow]")
                return []

            # Format job info
            jobs_info = []
            for job in jobs:
                # Calculate duration
                if job.status == "completed" and job.started_at and job.completed_at:
                    duration = (job.completed_at - job.started_at).total_seconds()
                    duration_str = self._format_duration(int(duration))
                else:
                    duration_str = "—"

                status_text = job.conclusion if job.status == "completed" else job.status

                jobs_info.append(
                    {
                        "job_id": job.id,
                        "name": job.name or "—",
                        "status": job.status,
                        "conclusion": job.conclusion,
                        "duration": duration_str,
                        "url": job.html_url,
                    }
                )

            return jobs_info

        except GithubException as e:
            error_msg = e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
            console.print(f"[bold red]✗ GitHub API error: {error_msg}[/bold red]")
            return None
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return None

    def check_job_status(
        self, state: RepoState, run_id: int, job_id: Optional[int] = None
    ) -> Optional[dict[str, Any]]:
        """Check the status of a job or run without downloading logs.

        Args:
            state: Repository state
            run_id: GitHub Actions run ID
            job_id: Optional specific job ID. If not provided, returns run status.

        Returns:
            Dict with status info, or None if error:
            For run: {run_id, status, conclusion, created_at, updated_at, duration}
            For job: {job_id, name, status, conclusion, started_at, completed_at, duration}
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                return None

            # Parse GitHub URL
            parsed = self._parse_github_url(state.remote_url)
            if not parsed:
                return None

            owner, repo = parsed

            # Connect to GitHub
            g = Github(token)
            github_repo = g.get_repo(f"{owner}/{repo}")
            run = github_repo.get_workflow_run(run_id)

            # If job_id specified, return job status
            if job_id:
                jobs = list(run.jobs())
                job = next((j for j in jobs if j.id == job_id), None)

                if not job:
                    return None

                # Calculate duration if completed
                duration_str = None
                if job.status == "completed" and job.started_at and job.completed_at:
                    duration = (job.completed_at - job.started_at).total_seconds()
                    duration_str = self._format_duration(int(duration))

                return {
                    "job_id": job.id,
                    "name": job.name,
                    "status": job.status,
                    "conclusion": job.conclusion,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "duration": duration_str,
                    "url": job.html_url,
                }
            else:
                # Return run status
                # Calculate duration if completed
                duration_str = None
                if run.status == "completed" and run.created_at and run.updated_at:
                    duration = (run.updated_at - run.created_at).total_seconds()
                    duration_str = self._format_duration(int(duration))

                return {
                    "run_id": run.id,
                    "status": run.status,
                    "conclusion": run.conclusion,
                    "created_at": run.created_at.isoformat() if run.created_at else None,
                    "updated_at": run.updated_at.isoformat() if run.updated_at else None,
                    "duration": duration_str,
                    "url": run.html_url,
                }

        except GithubException:
            return None
        except Exception:
            return None

    def download_job_logs(
        self, state: RepoState, run_id: int, job_id: int
    ) -> str | None:
        """Download logs for a specific job in a run.

        Args:
            state: Repository state
            run_id: GitHub Actions run ID
            job_id: Specific job ID to download

        Returns:
            Path to downloaded log file, or None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitHub token found[/bold red]")
                return None

            # Parse GitHub URL
            parsed = self._parse_github_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse GitHub URL from remote[/bold red]"
                )
                return None

            owner, repo = parsed

            # Connect to GitHub
            g = Github(token)
            github_repo = g.get_repo(f"{owner}/{repo}")

            # Get the workflow run
            run = github_repo.get_workflow_run(run_id)

            # Create storage directory with run ID
            storage_path = self.get_storage_path(state)
            run_dir = storage_path / f"run-{run_id}"
            run_dir.mkdir(parents=True, exist_ok=True)

            # Get the specific job
            jobs = list(run.jobs())
            job = next((j for j in jobs if j.id == job_id), None)

            if not job:
                console.print(f"[bold red]✗ Job {job_id} not found in run {run_id}[/bold red]")
                return None

            console.print(
                f"\n[bold cyan]Downloading logs for job '{job.name}' (ID: {job_id})...[/bold cyan]\n"
            )

            try:
                import requests

                logs_url = job.logs_url()

                # Fetch logs from signed URL (no auth needed)
                response = requests.get(logs_url)

                if response.status_code == 200:
                    # Create safe filename from job name
                    safe_name = re.sub(r"[^\w\-.]", "_", job.name)
                    log_file = run_dir / f"job-{job.id}-{safe_name}.log"

                    # Write logs to file
                    log_file.write_text(response.text)

                    console.print(
                        f"[bold green]✓ Downloaded job logs[/bold green]"
                    )
                    console.print(f"[dim]Location: {log_file}[/dim]")

                    return str(log_file)
                else:
                    console.print(
                        f"[bold red]✗ Failed to download logs (HTTP {response.status_code})[/bold red]"
                    )
                    return None

            except Exception as e:
                console.print(f"[bold red]✗ Error downloading logs: {str(e)}[/bold red]")
                return None

        except GithubException as e:
            error_msg = e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
            console.print(f"[bold red]✗ GitHub API error: {error_msg}[/bold red]")
            return None
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return None
