"""Action to fetch GitHub Actions workflow results."""

import re
from pathlib import Path
from rich.console import Console
from rich.table import Table
from github import Github, GithubException
from .base import Action
from git_maestro.state import RepoState

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class FetchGithubActionsAction(Action):
    """Fetch GitHub Actions workflow results."""

    def __init__(self):
        super().__init__()
        self.name = "Check GitHub Actions Status"
        self.description = "Gather workflow run information from GitHub Actions"
        self.emoji = "⚙️"
        self.category = "info"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the repo has a GitHub remote and facts not yet gathered."""
        if not state.is_git_repo or not state.has_remote:
            return False
        if state.get_remote_type() != "github":
            return False
        # Only show if we haven't checked GitHub Actions yet
        return not state.has_fact("github_actions_checked")

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

    def _parse_github_url(self, remote_url: str) -> tuple[str, str] | None:
        """Parse GitHub URL to extract owner and repo name."""
        # Handle HTTPS URLs: https://github.com/owner/repo.git
        https_match = re.search(
            r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url
        )
        if https_match:
            return https_match.group(1), https_match.group(2)
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

    def _get_status_color(self, status: str, conclusion: str | None) -> str:
        """Get color for status display."""
        if status == "completed":
            if conclusion == "success":
                return "green"
            elif conclusion == "failure":
                return "red"
            elif conclusion == "cancelled":
                return "yellow"
            else:
                return "dim"
        elif status == "in_progress":
            return "blue"
        elif status == "queued":
            return "cyan"
        else:
            return "dim"

    def _get_status_emoji(self, status: str, conclusion: str | None) -> str:
        """Get emoji for status."""
        if status == "completed":
            if conclusion == "success":
                return "✓"
            elif conclusion == "failure":
                return "✗"
            elif conclusion == "cancelled":
                return "⊘"
            else:
                return "•"
        elif status == "in_progress":
            return "⟳"
        elif status == "queued":
            return "⋯"
        else:
            return "•"

    def execute(self, state: RepoState) -> bool:
        """Execute the action to fetch GitHub Actions results."""
        try:
            # Parse GitHub URL
            parsed = self._parse_github_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse GitHub URL from remote[/bold red]"
                )
                return False

            owner, repo = parsed

            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold yellow]⚠ No GitHub token found[/bold yellow]")
                console.print("You need a GitHub token to fetch workflow results.")
                console.print(
                    "Please run 'Setup Remote Repository' first to configure your token."
                )
                return False

            # Connect to GitHub
            console.print(
                f"[bold cyan]Fetching workflow runs for {owner}/{repo}...[/bold cyan]"
            )
            g = Github(token)
            github_repo = g.get_repo(f"{owner}/{repo}")

            # Get workflow runs for current branch
            current_branch = state.branch_name or "main"
            runs = github_repo.get_workflow_runs(branch=current_branch)

            # Display up to 10 most recent runs
            run_list = list(runs[:10])

            if not run_list:
                console.print(
                    f"[bold yellow]No workflow runs found for branch '{current_branch}'[/bold yellow]"
                )
                # Store facts even if no runs
                state.set_facts(
                    {
                        "github_actions_checked": True,
                        "github_actions_has_runs": False,
                    }
                )
                return True

            # Store basic facts
            latest_run = run_list[0]
            state.set_facts(
                {
                    "github_actions_checked": True,
                    "github_actions_has_runs": True,
                    "github_actions_latest_run_id": latest_run.id,
                    "github_actions_latest_status": latest_run.status,
                    "github_actions_latest_conclusion": latest_run.conclusion,
                    "github_actions_latest_url": latest_run.html_url,
                }
            )

            # Create summary table
            table = Table(
                title=f"GitHub Actions - Recent Runs on '{current_branch}'",
                show_header=True,
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Status", width=12)
            table.add_column("Workflow", style="bold")
            table.add_column("Commit", width=10)
            table.add_column("Duration", justify="right")
            table.add_column("Started", style="dim")

            for idx, run in enumerate(run_list, 1):
                status_color = self._get_status_color(run.status, run.conclusion)
                status_emoji = self._get_status_emoji(run.status, run.conclusion)

                status_text = (
                    run.conclusion if run.status == "completed" else run.status
                )
                status_display = f"{status_emoji} {status_text}"

                # Calculate duration
                if run.status == "completed" and run.created_at and run.updated_at:
                    duration = (run.updated_at - run.created_at).total_seconds()
                    duration_str = self._format_duration(int(duration))
                else:
                    duration_str = "—"

                # Format created time
                created_str = (
                    run.created_at.strftime("%Y-%m-%d %H:%M") if run.created_at else "—"
                )

                # Get commit SHA (first 7 chars)
                commit_sha = run.head_sha[:7] if run.head_sha else "—"

                table.add_row(
                    str(idx),
                    f"[{status_color}]{status_display}[/{status_color}]",
                    run.name or "—",
                    commit_sha,
                    duration_str,
                    created_str,
                )

            console.print(table)

            # Show details of the most recent run
            console.print("\n[bold]Latest Run Details:[/bold]")
            console.print(f"  Run ID: {latest_run.id}")
            console.print(f"  URL: {latest_run.html_url}")

            # Fetch jobs for the latest run
            failed_jobs = []
            try:
                console.print("\n[bold cyan]Fetching job details...[/bold cyan]")
                jobs = latest_run.jobs()
                job_list = list(jobs)

                if job_list:
                    job_table = Table(title="Jobs", show_header=True)
                    job_table.add_column("Status", width=12)
                    job_table.add_column("Job Name", style="bold")
                    job_table.add_column("Duration", justify="right")

                    for job in job_list:
                        status_color = self._get_status_color(
                            job.status, job.conclusion
                        )
                        status_emoji = self._get_status_emoji(
                            job.status, job.conclusion
                        )
                        status_text = (
                            job.conclusion if job.status == "completed" else job.status
                        )
                        status_display = f"{status_emoji} {status_text}"

                        # Calculate duration
                        if (
                            job.status == "completed"
                            and job.started_at
                            and job.completed_at
                        ):
                            duration = (
                                job.completed_at - job.started_at
                            ).total_seconds()
                            duration_str = self._format_duration(int(duration))
                        else:
                            duration_str = "—"

                        job_table.add_row(
                            f"[{status_color}]{status_display}[/{status_color}]",
                            job.name or "—",
                            duration_str,
                        )

                    console.print(job_table)

                    # Store job information
                    failed_jobs = [j for j in job_list if j.conclusion == "failure"]
                    state.set_facts(
                        {
                            "github_actions_latest_job_count": len(job_list),
                            "github_actions_latest_failed_count": len(failed_jobs),
                            "github_actions_latest_failed_jobs": [
                                {"id": j.id, "name": j.name, "url": j.html_url}
                                for j in failed_jobs
                            ],
                        }
                    )

                    if failed_jobs:
                        console.print("\n[bold red]Failed Jobs:[/bold red]")
                        for job in failed_jobs:
                            console.print(f"\n[bold]{job.name}[/bold]")
                            console.print(f"  URL: {job.html_url}")

                            # Get the first few steps that failed
                            steps = job.steps
                            failed_steps = [
                                s for s in steps if s.conclusion == "failure"
                            ]
                            if failed_steps:
                                console.print("  Failed steps:")
                                for step in failed_steps[
                                    :3
                                ]:  # Show first 3 failed steps
                                    console.print(f"    • {step.name}")

            except GithubException as e:
                console.print(
                    f"[yellow]⚠ Could not fetch job details: {e.data.get('message', str(e))}[/yellow]"
                )

            console.print(
                f"\n[dim]View all runs at: {github_repo.html_url}/actions[/dim]"
            )
            return True

        except GithubException as e:
            error_msg = e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
            console.print(f"[bold red]✗ GitHub API error: {error_msg}[/bold red]")
            if e.status == 401:
                console.print(
                    "[yellow]Your token may be invalid or expired. Try running 'Setup Remote Repository' again.[/yellow]"
                )
            return False
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return False
