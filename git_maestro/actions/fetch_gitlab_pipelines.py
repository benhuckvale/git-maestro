"""Action to fetch GitLab Pipelines results."""

from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from .base import Action
from git_maestro.state import RepoState

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class FetchGitlabPipelinesAction(Action):
    """Fetch GitLab Pipelines results."""

    def __init__(self):
        super().__init__()
        self.name = "Check GitLab Pipelines Status"
        self.description = "Gather pipeline run information from GitLab"
        self.emoji = "⚙️"
        self.category = "info"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the repo has a GitLab remote and facts not yet gathered."""
        if not state.is_git_repo or not state.has_remote:
            return False
        if state.get_remote_type() != "gitlab":
            return False
        # Only show if we haven't checked GitLab Pipelines yet
        return not state.has_fact("gitlab_pipelines_checked")

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

    def _get_status_color(self, status: str) -> str:
        """Get color for status display."""
        if status == "success":
            return "green"
        elif status in ("failed", "failure"):
            return "red"
        elif status in ("canceled", "cancelled"):
            return "yellow"
        elif status == "running":
            return "blue"
        elif status in ("pending", "created", "waiting_for_resource", "preparing"):
            return "cyan"
        elif status == "skipped":
            return "dim"
        else:
            return "dim"

    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status."""
        if status == "success":
            return "✓"
        elif status in ("failed", "failure"):
            return "✗"
        elif status in ("canceled", "cancelled"):
            return "⊘"
        elif status == "running":
            return "⟳"
        elif status in ("pending", "created", "waiting_for_resource", "preparing"):
            return "⋯"
        elif status == "skipped":
            return "⊘"
        elif status == "manual":
            return "⊙"
        else:
            return "•"

    def execute(self, state: RepoState) -> bool:
        """Execute the action to fetch GitLab Pipelines results."""
        try:
            from git_maestro.gitlab import GitLabClient

            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold yellow]⚠ No GitLab token found[/bold yellow]")
                console.print("You need a GitLab token to fetch pipeline results.")
                console.print(
                    "Please set your GitLab token in ~/.config/git-maestro/tokens.conf"
                )
                console.print('Add a line: gitlab=YOUR_TOKEN')
                return False

            # Connect to GitLab
            console.print(
                f"[bold cyan]Fetching pipelines for {state.remote_url}...[/bold cyan]"
            )
            client = GitLabClient(state.remote_url, token)

            # Get recent pipelines
            pipelines = client.get_pipelines(per_page=10)

            if not pipelines:
                console.print(
                    "[bold yellow]No pipelines found[/bold yellow]"
                )
                # Store facts even if no pipelines
                state.set_facts(
                    {
                        "gitlab_pipelines_checked": True,
                        "gitlab_pipelines_has_runs": False,
                    }
                )
                return True

            # Store basic facts
            latest_pipeline = pipelines[0]
            state.set_facts(
                {
                    "gitlab_pipelines_checked": True,
                    "gitlab_pipelines_has_runs": True,
                    "gitlab_pipelines_latest_id": latest_pipeline.id,
                    "gitlab_pipelines_latest_status": latest_pipeline.status,
                    "gitlab_pipelines_latest_ref": latest_pipeline.ref,
                    "gitlab_pipelines_latest_url": latest_pipeline.web_url,
                }
            )

            # Create summary table
            table = Table(
                title="GitLab Pipelines - Recent Runs",
                show_header=True,
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Status", width=12)
            table.add_column("Ref", style="bold")
            table.add_column("Commit", width=10)
            table.add_column("Duration", justify="right")
            table.add_column("Created", style="dim")

            for idx, pipeline in enumerate(pipelines, 1):
                status_color = self._get_status_color(pipeline.status)
                status_emoji = self._get_status_emoji(pipeline.status)
                status_display = f"{status_emoji} {pipeline.status}"

                # Calculate duration
                if pipeline.duration:
                    duration_str = self._format_duration(int(pipeline.duration))
                else:
                    duration_str = "—"

                # Format created time
                created_str = pipeline.created_at[:16] if pipeline.created_at else "—"

                # Get commit SHA (first 8 chars)
                commit_sha = pipeline.sha[:8] if pipeline.sha else "—"

                table.add_row(
                    str(idx),
                    f"[{status_color}]{status_display}[/{status_color}]",
                    pipeline.ref or "—",
                    commit_sha,
                    duration_str,
                    created_str,
                )

            console.print(table)

            # Show details of the most recent pipeline
            console.print("\n[bold]Latest Pipeline Details:[/bold]")
            console.print(f"  Pipeline ID: {latest_pipeline.id}")
            console.print(f"  URL: {latest_pipeline.web_url}")

            # Fetch jobs for the latest pipeline
            try:
                console.print("\n[bold cyan]Fetching job details...[/bold cyan]")
                jobs = client.get_pipeline_jobs(latest_pipeline.id)

                if jobs:
                    job_table = Table(title="Jobs", show_header=True)
                    job_table.add_column("Status", width=12)
                    job_table.add_column("Stage", style="cyan")
                    job_table.add_column("Job Name", style="bold")
                    job_table.add_column("Duration", justify="right")

                    failed_jobs = []
                    for job in jobs:
                        status_color = self._get_status_color(job.status)
                        status_emoji = self._get_status_emoji(job.status)
                        status_display = f"{status_emoji} {job.status}"

                        # Calculate duration
                        if job.duration:
                            duration_str = self._format_duration(int(job.duration))
                        else:
                            duration_str = "—"

                        job_table.add_row(
                            f"[{status_color}]{status_display}[/{status_color}]",
                            job.stage or "—",
                            job.name or "—",
                            duration_str,
                        )

                        # Track failed jobs
                        if job.status == "failed":
                            failed_jobs.append(job)

                    console.print(job_table)

                    # Store job information
                    state.set_facts(
                        {
                            "gitlab_pipelines_latest_job_count": len(jobs),
                            "gitlab_pipelines_latest_failed_count": len(failed_jobs),
                            "gitlab_pipelines_latest_failed_jobs": [
                                {
                                    "id": j.id,
                                    "name": j.name,
                                    "stage": j.stage,
                                    "url": j.web_url,
                                }
                                for j in failed_jobs
                            ],
                        }
                    )

                    if failed_jobs:
                        console.print("\n[bold red]Failed Jobs:[/bold red]")
                        for job in failed_jobs:
                            console.print(f"\n[bold]{job.name}[/bold]")
                            console.print(f"  Stage: {job.stage}")
                            console.print(f"  URL: {job.web_url}")
                            if hasattr(job, 'failure_reason') and job.failure_reason:
                                console.print(f"  Failure: {job.failure_reason}")

            except Exception as e:
                console.print(
                    f"[yellow]⚠ Could not fetch job details: {str(e)}[/yellow]"
                )

            console.print(
                f"\n[dim]View all pipelines at: {client.project.web_url}/-/pipelines[/dim]"
            )
            return True

        except ImportError:
            console.print(
                "[bold red]✗ python-gitlab is not installed[/bold red]"
            )
            console.print("Install it with: pip install python-gitlab")
            return False
        except ValueError as e:
            console.print(f"[bold red]✗ {e}[/bold red]")
            return False
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return False
