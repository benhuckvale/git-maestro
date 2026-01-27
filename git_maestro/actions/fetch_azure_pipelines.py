"""Action to fetch Azure DevOps Pipelines results."""

from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table

from .base import Action
from git_maestro.state import RepoState
from git_maestro.azure import parse_azure_url, AzureClient

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class FetchAzurePipelinesAction(Action):
    """Fetch Azure DevOps Pipelines results."""

    def __init__(self):
        super().__init__()
        self.name = "Check Azure Pipelines Status"
        self.description = "Gather pipeline run information from Azure DevOps"
        self.emoji = "☁️"
        self.category = "info"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the repo has an Azure remote and facts not yet gathered."""
        if not state.is_git_repo or not state.has_remote:
            return False
        if state.get_remote_type() != "azure":
            return False
        # Only show if we haven't checked Azure Pipelines yet
        return not state.has_fact("azure_pipelines_checked")

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

    def _get_status_color(self, status: str, result: Optional[str]) -> str:
        """Get color for status display."""
        status = status.lower() if status else ""
        result = result.lower() if result else ""

        if status == "completed":
            if result == "succeeded":
                return "green"
            elif result == "failed":
                return "red"
            elif result == "canceled":
                return "yellow"
            else:
                return "dim"
        elif status == "inprogress":
            return "blue"
        elif status == "notstarted":
            return "cyan"
        else:
            return "dim"

    def _get_status_emoji(self, status: str, result: Optional[str]) -> str:
        """Get emoji for status."""
        status = status.lower() if status else ""
        result = result.lower() if result else ""

        if status == "completed":
            if result == "succeeded":
                return "✓"
            elif result == "failed":
                return "✗"
            elif result == "canceled":
                return "⊘"
            else:
                return "•"
        elif status == "inprogress":
            return "⟳"
        elif status == "notstarted":
            return "⋯"
        else:
            return "•"

    def execute(self, state: RepoState) -> bool:
        """Execute the action to fetch Azure Pipelines results."""
        try:
            # Parse Azure URL
            parsed = parse_azure_url(state.remote_url)
            if not parsed:
                console.print(
                    "[bold red]✗ Could not parse Azure DevOps URL from remote[/bold red]"
                )
                return False

            org, project, repo = parsed

            # Get token
            token = self._get_stored_token()
            if not token:
                console.print(
                    "[bold yellow]⚠ No Azure DevOps token found[/bold yellow]"
                )
                console.print("You need an Azure DevOps PAT to fetch pipeline results.")
                console.print(
                    "Please run 'Setup Azure DevOps Repository' first to configure your token."
                )
                return False

            # Connect to Azure DevOps
            console.print(
                f"[bold cyan]Fetching pipelines for {org}/{project}...[/bold cyan]"
            )
            client = AzureClient(org, project, token)

            # Get pipelines
            pipelines = client.get_pipelines()

            if not pipelines:
                console.print(
                    "[bold yellow]No pipelines found in project[/bold yellow]"
                )
                state.set_facts(
                    {
                        "azure_pipelines_checked": True,
                        "azure_pipelines_has_runs": False,
                    }
                )
                return True

            # Get recent runs from first few pipelines
            all_runs = []
            for pipeline in pipelines[:5]:  # Check first 5 pipelines
                try:
                    runs = client.get_pipeline_runs(pipeline.id, top=5)
                    for run in runs:
                        run.pipeline_name = pipeline.name
                        run.pipeline_id = pipeline.id
                        all_runs.append(run)
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Could not fetch runs for {pipeline.name}: {e}[/yellow]"
                    )

            if not all_runs:
                console.print("[bold yellow]No pipeline runs found[/bold yellow]")
                state.set_facts(
                    {
                        "azure_pipelines_checked": True,
                        "azure_pipelines_has_runs": False,
                    }
                )
                return True

            # Store basic facts
            latest_run = all_runs[0]
            state.set_facts(
                {
                    "azure_pipelines_checked": True,
                    "azure_pipelines_has_runs": True,
                    "azure_pipelines_latest_run_id": latest_run.id,
                    "azure_pipelines_latest_status": latest_run.state,
                    "azure_pipelines_latest_result": latest_run.result,
                    "azure_pipelines_pipeline_id": latest_run.pipeline_id,
                }
            )

            # Create summary table
            table = Table(
                title="Azure Pipelines - Recent Runs",
                show_header=True,
            )
            table.add_column("#", style="dim", width=3)
            table.add_column("Status", width=12)
            table.add_column("Pipeline", style="bold")
            table.add_column("Created", style="dim")

            for idx, run in enumerate(all_runs[:10], 1):
                status_color = self._get_status_color(run.state, run.result)
                status_emoji = self._get_status_emoji(run.state, run.result)

                status_text = run.result if run.state == "completed" else run.state
                status_display = f"{status_emoji} {status_text}"

                # Format created time
                created_str = "—"
                if hasattr(run, "created_date") and run.created_date:
                    created_str = run.created_date.strftime("%Y-%m-%d %H:%M")

                table.add_row(
                    str(idx),
                    f"[{status_color}]{status_display}[/{status_color}]",
                    run.pipeline_name or "—",
                    created_str,
                )

            console.print(table)

            # Show details of the most recent run
            console.print("\n[bold]Latest Run Details:[/bold]")
            console.print(f"  Run ID: {latest_run.id}")
            console.print(f"  Pipeline: {latest_run.pipeline_name}")
            console.print(f"  Status: {latest_run.state}")
            if latest_run.result:
                console.print(f"  Result: {latest_run.result}")

            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return False
