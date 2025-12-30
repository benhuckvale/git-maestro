"""Action to download Azure DevOps Pipelines stage logs."""

from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .base import Action
from git_maestro.state import RepoState
from git_maestro.azure import parse_azure_url, AzureClient

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class DownloadAzureStageLogsAction(Action):
    """Download logs from Azure DevOps Pipelines stages."""

    def __init__(self):
        super().__init__()
        self.name = "Download Azure Pipeline Logs"
        self.description = "Download detailed logs from pipeline stages to local files"
        self.emoji = "📥"
        self.category = "info"
        self.storage_dir = "traces"  # Will create .git-maestro/traces/

    def is_applicable(self, state: RepoState) -> bool:
        """Only show if we have Azure pipelines checked and there are failed runs."""
        return (
            state.has_fact("azure_pipelines_checked")
            and state.get_fact("azure_pipelines_has_runs", False)
            and state.get_fact("azure_pipelines_latest_result") == "failed"
        )

    def _get_stored_token(self) -> Optional[str]:
        """Get stored Azure token."""
        if not CONFIG_FILE.exists():
            return None
        try:
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    if line.startswith("azure="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            return None
        return None

    def execute(self, state: RepoState) -> bool:
        """Execute the action to download complete execution logs using Build API."""
        try:
            # Get the latest failed run info
            run_id = state.get_fact("azure_pipelines_latest_run_id")
            pipeline_id = state.get_fact("azure_pipelines_pipeline_id")

            if not run_id or not pipeline_id:
                console.print("[bold red]✗ Could not retrieve run/pipeline ID[/bold red]")
                return False

            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No Azure DevOps token found[/bold red]")
                return False

            # Parse Azure URL
            parsed = parse_azure_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse Azure DevOps URL from remote[/bold red]"
                )
                return False

            org, project, repo = parsed

            # Connect to Azure DevOps
            azure_client = AzureClient(org, project, token)

            # Create storage directory with run ID
            storage_path = self.get_storage_path(state)
            run_dir = storage_path / f"run-{run_id}"
            run_dir.mkdir(parents=True, exist_ok=True)

            console.print(
                f"\n[bold cyan]Downloading complete execution logs to: {run_dir}[/bold cyan]\n"
            )

            # Get complete execution logs using Build API
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Fetching pipeline structure and logs..."),
                console=console,
            ) as progress:
                progress.add_task(description="", total=None)
                complete_logs = azure_client.get_complete_execution_logs(build_id=run_id)

            if not complete_logs or not complete_logs.get('jobs'):
                console.print("[yellow]No jobs found in run[/yellow]")
                return False

            downloaded_count = 0

            # Download logs for each job and task
            console.print(f"[cyan]Downloading logs from {len(complete_logs['jobs'])} job(s)...[/cyan]\n")

            for job in complete_logs['jobs']:
                job_name = job['name']
                console.print(f"[cyan]Job: {job_name}[/cyan]")

                # Display and save diagnostic issues if present
                if job.get('issues'):
                    console.print(f"[bold red]  Diagnostic Issues:[/bold red]")

                    # Build issues content
                    issues_content = []
                    for issue in job['issues']:
                        issue_type = issue.get('type', 'error').upper()
                        message = issue.get('message', 'Unknown error')
                        console.print(f"  [{issue_type}] {message}")
                        issues_content.append(f"[{issue_type}] {message}")

                    # Save issues to file
                    try:
                        issues_file = run_dir / f"job-{job['id']}-{job_name.replace(' ', '_')}.issues"
                        with open(issues_file, "w") as f:
                            f.write('\n'.join(issues_content))
                        console.print(f"  [green]✓ Saved diagnostic issues[/green]")
                        downloaded_count += 1
                    except Exception as e:
                        console.print(f"  [yellow]⚠ Error saving issues: {e}[/yellow]")

                    console.print()

                # Save job-level log if available
                if job.get('log_content'):
                    try:
                        job_log_file = run_dir / f"job-{job['id']}-{job_name.replace(' ', '_')}.log"
                        with open(job_log_file, "w") as f:
                            f.write(job['log_content'])
                        console.print(f"  [green]✓ Downloaded job log[/green]")
                        downloaded_count += 1
                    except Exception as e:
                        console.print(f"  [yellow]⚠ Error saving job log: {e}[/yellow]")

                # Save logs for each task
                for task in job.get('tasks', []):
                    task_name = task['name']

                    # Display and save task diagnostic issues if present
                    if task.get('issues'):
                        console.print(f"  [yellow]⚠ {task_name} has issues:[/yellow]")

                        # Build and save issues content
                        task_issues_content = []
                        for issue in task['issues']:
                            issue_type = issue.get('type', 'warning').upper()
                            message = issue.get('message', 'Unknown issue')
                            console.print(f"    [{issue_type}] {message}")
                            task_issues_content.append(f"[{issue_type}] {message}")

                        # Save task issues to file
                        try:
                            task_issues_file = run_dir / f"task-{task['id']}-{task_name.replace(' ', '_')}.issues"
                            with open(task_issues_file, "w") as f:
                                f.write('\n'.join(task_issues_content))
                            downloaded_count += 1
                        except Exception as e:
                            console.print(f"    [yellow]⚠ Error saving task issues: {e}[/yellow]")

                    if task.get('log_content'):
                        try:
                            task_result = task['result'] or 'unknown'
                            task_log_file = run_dir / f"task-{task['id']}-{task_name.replace(' ', '_')}.log"
                            with open(task_log_file, "w") as f:
                                f.write(task['log_content'])
                            status_icon = "[green]✓[/green]" if task_result == 'succeeded' else "[red]✗[/red]"
                            console.print(f"  {status_icon} Task: {task_name} ({task_result})")
                            downloaded_count += 1
                        except Exception as e:
                            console.print(f"  [yellow]⚠ Error saving task log: {e}[/yellow]")
                    else:
                        console.print(f"  [yellow]⚠ No log content for task: {task_name}[/yellow]")

            console.print(
                f"\n[bold green]✓ Downloaded {downloaded_count} log file(s) to: {run_dir}[/bold green]"
            )
            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return False
