"""Action to fetch Azure DevOps Pipelines logs from specific runs."""

from pathlib import Path
from typing import Optional, Any
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .base import Action
from git_maestro.state import RepoState
from git_maestro.azure import parse_azure_url, AzureClient

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class GetAzurePipelinesAction(Action):
    """Fetch logs from specific Azure DevOps Pipelines runs."""

    def __init__(self):
        super().__init__()
        self.name = "View Azure Pipelines Run History and Logs"
        self.description = (
            "Browse and download logs from specific Azure DevOps Pipelines runs"
        )
        self.emoji = "☁️"
        self.category = "info"
        self.storage_dir = "traces"  # Will create .git-maestro/traces/

    def is_applicable(self, state: RepoState) -> bool:
        """Only show if we have an Azure remote with pipelines history."""
        return state.has_fact("azure_pipelines_checked") and state.get_fact(
            "azure_pipelines_has_runs", False
        )

    def _get_stored_token(self) -> Optional[str]:
        """Get stored Azure DevOps token."""
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

    def _get_azure_client(self, state: RepoState, token: str) -> Optional[AzureClient]:
        """Get authenticated Azure DevOps client."""
        try:
            # Parse Azure URL
            parsed = parse_azure_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse Azure DevOps URL from remote[/bold red]"
                )
                return None

            org, project, _ = parsed
            return AzureClient(org, project, token)
        except Exception as e:
            console.print(f"[bold red]✗ Error creating Azure client: {e}[/bold red]")
            return None

    def execute(self, state: RepoState) -> bool:
        """Execute the action to list recent runs."""
        runs = self.list_recent_runs(state, count=15)
        if runs is None:
            return False
        return len(runs) > 0

    def list_recent_runs(
        self, state: RepoState, count: int = 10
    ) -> Optional[list[dict[str, Any]]]:
        """List recent pipeline runs.

        Args:
            state: Repository state
            count: Number of recent runs to return

        Returns:
            List of run info dicts with keys: run_id, status, conclusion, created_at, pipeline_name
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No Azure DevOps token found[/bold red]")
                return None

            # Parse Azure URL
            parsed = parse_azure_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse Azure DevOps URL from remote[/bold red]"
                )
                return None

            org, project, repo = parsed

            # Get Azure client
            client = self._get_azure_client(state, token)
            if not client:
                return None

            # Get pipelines
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task("[cyan]Fetching pipelines...", total=None)
                pipelines = client.get_pipelines()

            if not pipelines:
                console.print("[yellow]No pipelines found in project[/yellow]")
                return []

            # Get recent runs from each pipeline
            runs_info = []
            for pipeline in pipelines:
                try:
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(f"[cyan]Fetching runs for {pipeline.name}..."),
                        console=console,
                    ) as progress:
                        progress.add_task(description="", total=None)
                        runs = client.get_pipeline_runs(pipeline.id, top=count)

                    for run in runs:
                        # Map Azure status to GitHub-like status
                        status = (
                            run.state.lower() if hasattr(run, "state") else "unknown"
                        )
                        conclusion = (
                            run.result.lower() if hasattr(run, "result") else None
                        )

                        # Format created date
                        created_str = "—"
                        if hasattr(run, "created_date") and run.created_date:
                            created_str = run.created_date.strftime("%Y-%m-%d %H:%M")

                        # Extract URL safely
                        url = "—"
                        try:
                            if hasattr(run, "_links") and run._links:
                                if hasattr(run._links, "get"):
                                    url = run._links.get("web", {}).get("href", "—")
                                elif hasattr(run._links, "web"):
                                    url = getattr(run._links.web, "href", "—")
                        except Exception:
                            pass

                        runs_info.append(
                            {
                                "run_id": run.id,
                                "status": status,
                                "conclusion": conclusion,
                                "created_at": created_str,
                                "pipeline_name": pipeline.name or "—",
                                "pipeline_id": pipeline.id,
                                "url": url,
                            }
                        )

                        # Display in console
                        status_display = conclusion if conclusion else status
                        console.print(
                            f"  [{created_str}] {status_display:10s} | {pipeline.name} (Run: {run.id})"
                        )

                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not fetch runs for pipeline {pipeline.name}: {e}[/yellow]"
                    )

            return runs_info

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return None

    def get_run_stages(
        self, state: RepoState, pipeline_id: int, run_id: int
    ) -> Optional[list[dict[str, Any]]]:
        """Get detailed stage/job/task information for a specific run.

        Uses the Build API timeline to get complete job and task structure,
        including all execution steps (Python setup, dependencies, tests, etc).

        Args:
            state: Repository state
            pipeline_id: Azure Pipelines pipeline ID
            run_id: Azure Pipelines run ID (same as build_id in Build API)

        Returns:
            List of job info dicts with keys: job_id, name, status, result, start_time, finish_time, tasks
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No Azure DevOps token found[/bold red]")
                return None

            # Get Azure client
            client = self._get_azure_client(state, token)
            if not client:
                return None

            # Get complete execution logs using Build API
            with Progress(
                SpinnerColumn(),
                TextColumn(f"[cyan]Fetching run {run_id} job structure..."),
                console=console,
            ) as progress:
                progress.add_task(description="", total=None)
                complete_logs = client.get_complete_execution_logs(build_id=run_id)

            if not complete_logs or not complete_logs.get("jobs"):
                console.print(f"[yellow]No jobs found in run {run_id}[/yellow]")
                return []

            # Convert to stage/job info
            stages_info = []
            for job in complete_logs["jobs"]:
                job_info = {
                    "stage_id": job["id"],
                    "name": job["name"],
                    "status": job["state"],
                    "result": job["result"],
                    "start_time": job["start_time"],
                    "finish_time": job["finish_time"],
                    "error_count": job["error_count"],
                    "warning_count": job["warning_count"],
                    "tasks": [],
                }

                # Add task details
                for task in job.get("tasks", []):
                    task_info = {
                        "task_id": task["id"],
                        "name": task["name"],
                        "type": task["type"],
                        "status": task["state"],
                        "result": task["result"],
                        "start_time": task["start_time"],
                        "finish_time": task["finish_time"],
                        "error_count": task["error_count"],
                        "warning_count": task["warning_count"],
                    }
                    job_info["tasks"].append(task_info)

                stages_info.append(job_info)

            return stages_info

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return None

    def check_run_status(
        self,
        state: RepoState,
        pipeline_id: int,
        run_id: int,
        stage_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Check the status of a run or stage without downloading logs.

        Args:
            state: Repository state
            pipeline_id: Azure Pipelines pipeline ID
            run_id: Azure Pipelines run ID
            stage_id: Optional specific stage ID. If not provided, returns run status.

        Returns:
            Dict with status info, or None if error:
            For run: {run_id, status, result, created_date}
            For stage: {stage_id, name, status, result, started_time, finished_time}
            None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                return None

            # Get Azure client
            client = self._get_azure_client(state, token)
            if not client:
                return None

            # Get run details
            run = client.get_run(pipeline_id, run_id)
            if not run:
                return None

            # If stage_id specified, return stage status
            if stage_id:
                if hasattr(run, "timeline") and run.timeline:
                    for record in run.timeline:
                        if getattr(record, "id", None) == stage_id:
                            name = getattr(record, "name", "—")
                            state_val = getattr(record, "state", "unknown").lower()
                            result = getattr(record, "result", None)
                            if result:
                                result = result.lower()

                            started_str = None
                            finished_str = None
                            if hasattr(record, "startTime") and record.startTime:
                                started_str = record.startTime.isoformat()
                            if hasattr(record, "finishTime") and record.finishTime:
                                finished_str = record.finishTime.isoformat()

                            return {
                                "stage_id": stage_id,
                                "name": name,
                                "status": state_val,
                                "result": result,
                                "started_time": started_str,
                                "finished_time": finished_str,
                            }
                return None
            else:
                # Return run status
                status = run.state.lower() if hasattr(run, "state") else "unknown"
                result = run.result.lower() if hasattr(run, "result") else None

                created_str = None
                if hasattr(run, "created_date") and run.created_date:
                    created_str = run.created_date.isoformat()

                return {
                    "run_id": run.id,
                    "status": status,
                    "result": result,
                    "created_date": created_str,
                    "url": (
                        run._links.get("web", {}).get("href")
                        if hasattr(run, "_links")
                        else None
                    ),
                }

        except Exception:
            return None

    def download_stage_logs(
        self, state: RepoState, pipeline_id: int, run_id: int, stage_id: str
    ) -> Optional[str]:
        """Download logs for a specific stage in a run.

        Args:
            state: Repository state
            pipeline_id: Azure Pipelines pipeline ID
            run_id: Azure Pipelines run ID
            stage_id: Specific stage ID to download

        Returns:
            Path to downloaded log file, or None if error
        """
        try:
            # Get token
            token = self._get_stored_token()
            if not token:
                console.print("[bold red]✗ No Azure DevOps token found[/bold red]")
                return None

            # Get Azure client
            client = self._get_azure_client(state, token)
            if not client:
                return None

            # Create storage directory with run ID
            storage_path = self.get_storage_path(state)
            run_dir = storage_path / f"run-{run_id}"
            run_dir.mkdir(parents=True, exist_ok=True)

            # Download logs
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Downloading logs..."),
                console=console,
            ) as progress:
                progress.add_task(description="", total=None)
                log_bytes = client.get_logs_for_stage(pipeline_id, run_id, stage_id)

            if not log_bytes:
                console.print("[yellow]No logs found for this stage[/yellow]")
                return None

            # Save to file
            log_file = run_dir / f"stage-{stage_id}.log"
            with open(log_file, "wb") as f:
                f.write(log_bytes)

            console.print(f"[bold green]✓ Logs saved to {log_file}[/bold green]")
            return str(log_file)

        except Exception as e:
            console.print(f"[bold red]✗ Error downloading logs: {e}[/bold red]")
            return None
