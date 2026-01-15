"""Action to configure Azure DevOps token for existing remotes."""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console

from .base import Action
from git_maestro.state import RepoState
from git_maestro.azure import AzureClient, parse_azure_url
from git_maestro.selection_helper import prompt_password

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class ConfigureAzureTokenAction(Action):
    """Configure Azure DevOps token for an existing remote."""

    def __init__(self):
        super().__init__()
        self.name = "Configure Azure DevOps Access"
        self.description = "Add or update Azure DevOps PAT for this repository"
        self.emoji = "🔑"

    def is_applicable(self, state: RepoState) -> bool:
        """Show this action if we have an Azure remote but no token."""
        if not state.is_git_repo or not state.has_remote:
            return False
        if state.get_remote_type() != "azure":
            return False
        # Only show if we don't have a token yet
        return not state.has_token_for_remote()

    def _store_token(self, token: str):
        """Store Azure token."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Ensure directory has correct permissions
        os.chmod(CONFIG_DIR, 0o700)

        # Read existing tokens
        tokens = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            tokens[key] = value
            except Exception:
                pass

        # Update token
        tokens["azure"] = token

        # Write back
        try:
            with open(CONFIG_FILE, "w") as f:
                for key, value in tokens.items():
                    f.write(f"{key}={value}\n")
            # Make file readable only by user
            os.chmod(CONFIG_FILE, 0o600)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not store token: {e}[/yellow]")

    def execute(self, state: RepoState) -> bool:
        """Configure Azure DevOps token."""
        try:
            console.print(
                "[bold cyan]Configuring Azure DevOps access...[/bold cyan]"
            )

            # Parse Azure URL to show org/project
            parsed = parse_azure_url(state.remote_url)
            if parsed:
                org, project, repo = parsed
                console.print(
                    f"[dim]Organization: {org}, Project: {project}, Repo: {repo}[/dim]"
                )

            # Get token
            console.print(
                "\n[yellow]An Azure DevOps Personal Access Token (PAT) is required to access pipelines via the API.[/yellow]"
            )
            console.print(
                "[yellow]This is different from your SSH key (used for git push/pull).[/yellow]\n"
            )

            console.print("[cyan]To create an Azure DevOps Personal Access Token:[/cyan]")
            console.print(
                "  [dim]1.[/dim] Go to [blue]https://dev.azure.com/{organization}/_usersSettings/tokens[/blue]"
            )
            console.print("  [dim]2.[/dim] Click 'New Token'")
            console.print("  [dim]3.[/dim] Give it a name like 'git-maestro'")
            console.print(
                "  [dim]4.[/dim] Select scope: [bold]Code (read)[/bold] is sufficient for monitoring pipelines"
            )
            console.print("  [dim]5.[/dim] Click 'Create'")
            console.print("  [dim]6.[/dim] Copy the token immediately (it won't be shown again)")

            console.print()
            token = prompt_password("Enter PAT:")

            if not token:
                console.print("[yellow]No token provided, skipping[/yellow]")
                return False

            # Test authentication
            console.print(f"\n[cyan]Testing authentication...[/cyan]")
            try:
                if parsed:
                    org, project, repo = parsed
                    azure_client = AzureClient(org, project, token)
                    # Try to list pipelines to verify access
                    azure_client.get_pipelines()
                    console.print("[green]✓ Authentication successful![/green]")
                else:
                    console.print("[yellow]Warning: Could not parse Azure URL[/yellow]")
                    return False
            except Exception as e:
                console.print(f"[bold red]✗ Authentication failed: {e}[/bold red]")
                return False

            # Store token
            self._store_token(token)
            console.print(
                "[green]✓ Token stored securely in ~/.config/git-maestro/tokens.conf[/green]"
            )

            return True

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return False
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return False
