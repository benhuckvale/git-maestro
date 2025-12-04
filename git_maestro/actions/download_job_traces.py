"""Action to download GitHub Actions job traces/logs."""

import re
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from github import Github, GithubException
from .base import Action
from git_maestro.state import RepoState

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class DownloadJobTracesAction(Action):
    """Download logs from failed GitHub Actions jobs."""

    def __init__(self):
        super().__init__()
        self.name = "Download Failed Job Traces"
        self.description = "Download detailed logs from failed jobs to local files"
        self.emoji = "📥"
        self.category = "info"
        self.storage_dir = "traces"  # Will create .git-maestro/traces/

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

    def _parse_github_url(self, remote_url: str) -> tuple[str, str] | None:
        """Parse GitHub URL to extract owner and repo name."""
        match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote_url)
        if match:
            return match.group(1), match.group(2)
        return None

    def execute(self, state: RepoState) -> bool:
        """Execute the action to download job traces."""
        try:
            failed_jobs = state.get_fact("github_actions_latest_failed_jobs", [])
            if not failed_jobs:
                console.print("[yellow]No failed jobs found.[/yellow]")
                return True

            run_id = state.get_fact("github_actions_latest_run_id")
            if not run_id:
                console.print("[bold red]✗ Could not retrieve run ID[/bold red]")
                return False

            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No GitHub token found[/bold red]")
                return False

            # Parse GitHub URL
            parsed = self._parse_github_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse GitHub URL from remote[/bold red]"
                )
                return False

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

            console.print(
                f"\n[bold cyan]Downloading traces to: {run_dir}[/bold cyan]\n"
            )

            # Get all jobs for the run
            jobs = list(run.jobs())
            failed_job_ids = {j["id"] for j in failed_jobs}

            downloaded_count = 0

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                for job in jobs:
                    # Only download failed jobs
                    if job.id not in failed_job_ids:
                        continue

                    task = progress.add_task(f"Downloading: {job.name}", total=None)

                    try:
                        # Get job logs URL - this returns a signed Azure Blob Storage URL
                        # that doesn't need GitHub authentication
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

                            progress.update(
                                task, description=f"✓ Downloaded: {job.name}"
                            )
                            downloaded_count += 1
                        else:
                            progress.update(
                                task,
                                description=f"✗ Failed: {job.name} (HTTP {response.status_code})",
                            )
                            console.print(f"[dim]Response: {response.text[:200]}[/dim]")

                    except Exception as e:
                        progress.update(
                            task, description=f"✗ Error: {job.name} - {str(e)}"
                        )

            # Create a summary file
            summary_file = run_dir / "README.md"
            summary_content = f"""# GitHub Actions Run {run_id}

**Repository:** {owner}/{repo}
**Branch:** {state.branch_name}
**Run URL:** {run.html_url}
**Downloaded:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Failed Jobs

"""
            for job_info in failed_jobs:
                safe_name = re.sub(r"[^\w\-.]", "_", job_info["name"])
                log_file = f"job-{job_info['id']}-{safe_name}.log"
                summary_content += f"- **{job_info['name']}**\n"
                summary_content += f"  - Job URL: {job_info['url']}\n"
                summary_content += f"  - Log file: `{log_file}`\n\n"

            summary_file.write_text(summary_content)

            console.print(
                f"\n[bold green]✓ Downloaded {downloaded_count} job trace(s)[/bold green]"
            )
            console.print(f"[dim]Location: {run_dir}[/dim]")
            console.print(f"[dim]Summary: {summary_file}[/dim]")

            # Store fact that traces have been downloaded
            state.set_facts(
                {
                    "github_actions_traces_downloaded": True,
                    "github_actions_traces_path": str(run_dir),
                    "github_actions_traces_run_id": run_id,
                }
            )

            return True

        except GithubException as e:
            error_msg = e.data.get("message", str(e)) if hasattr(e, "data") else str(e)
            console.print(f"[bold red]✗ GitHub API error: {error_msg}[/bold red]")
            return False
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return False
