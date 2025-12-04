"""Action to view detailed information about failed GitHub Actions jobs."""

from pathlib import Path
from rich.console import Console
from github import Github, GithubException
from .base import Action
from git_maestro.state import RepoState

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class ViewFailedJobsAction(Action):
    """View detailed logs from failed GitHub Actions jobs."""

    def __init__(self):
        super().__init__()
        self.name = "View Failed Job Details"
        self.description = "Show detailed logs and steps from failed jobs"
        self.emoji = "🔍"
        self.category = "info"

    def is_applicable(self, state: RepoState) -> bool:
        """Only show if we have GitHub Actions facts and there are failures."""
        return (
            state.has_fact("github_actions_checked")
            and state.get_fact("github_actions_latest_failed_count", 0) > 0
        )

    def _get_stored_token(self) -> str | None:
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

    def execute(self, state: RepoState) -> bool:
        """Execute the action to view failed job details."""
        try:
            failed_jobs = state.get_fact("github_actions_latest_failed_jobs", [])
            if not failed_jobs:
                console.print("[yellow]No failed jobs found.[/yellow]")
                return True

            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitHub token found[/bold red]")
                return False

            # Connect to GitHub
            g = Github(token)

            for job_info in failed_jobs:
                console.print(f"\n[bold red]Failed Job: {job_info['name']}[/bold red]")
                console.print(f"[dim]Job URL: {job_info['url']}[/dim]\n")

                try:
                    # We need to get the full job object to access steps
                    # The job URL format is: https://github.com/owner/repo/actions/runs/RUN_ID/jobs/JOB_ID
                    # We need to construct the API call from the stored run_id
                    run_id = state.get_fact("github_actions_latest_run_id")
                    if not run_id:
                        console.print(
                            "[yellow]⚠ Could not retrieve job details - run ID not found[/yellow]"
                        )
                        continue

                    # Parse owner/repo from remote URL
                    import re

                    remote_url = state.remote_url
                    match = re.search(
                        r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url
                    )
                    if not match:
                        console.print("[yellow]⚠ Could not parse GitHub URL[/yellow]")
                        continue

                    owner, repo = match.group(1), match.group(2)
                    github_repo = g.get_repo(f"{owner}/{repo}")
                    run = github_repo.get_workflow_run(run_id)

                    # Find the specific job
                    jobs = list(run.jobs())
                    job = next((j for j in jobs if j.id == job_info["id"]), None)

                    if not job:
                        console.print("[yellow]⚠ Could not find job details[/yellow]")
                        continue

                    # Display failed steps
                    failed_steps = [s for s in job.steps if s.conclusion == "failure"]
                    if failed_steps:
                        for step in failed_steps:
                            console.print(f"\n[bold]Failed Step: {step.name}[/bold]")
                            console.print(f"  Status: [red]{step.conclusion}[/red]")
                            if step.started_at and step.completed_at:
                                duration = (
                                    step.completed_at - step.started_at
                                ).total_seconds()
                                console.print(f"  Duration: {int(duration)}s")

                    console.print(f"\n[dim]View full logs at: {job_info['url']}[/dim]")

                except GithubException as e:
                    error_msg = (
                        e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
                    )
                    console.print(
                        f"[yellow]⚠ Could not fetch details: {error_msg}[/yellow]"
                    )
                except Exception as e:
                    console.print(f"[yellow]⚠ Error: {e}[/yellow]")

            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return False
