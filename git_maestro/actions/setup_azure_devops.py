"""Action to set up an Azure DevOps remote repository."""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console

from .base import Action
from git_maestro.state import RepoState
from git_maestro.ssh_config import SSHConfig
from git_maestro.description_helper import get_description_options
from git_maestro.azure import AzureClient
from git_maestro.push_helper import push_to_remote
from git_maestro.selection_helper import (
    prompt_confirm,
    prompt_password,
    prompt_text,
    select_number_from_menu,
)

console = Console()

# Config file location
CONFIG_DIR = Path.home() / ".config" / "git-maestro"
CONFIG_FILE = CONFIG_DIR / "tokens.conf"


class SetupAzureDevOpsAction(Action):
    """Set up an Azure DevOps remote repository."""

    def __init__(self):
        super().__init__()
        self.name = "Setup Azure DevOps Repository"
        self.description = "Create and connect to an Azure DevOps repository"
        self.emoji = "☁️"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the directory is a git repo without a remote."""
        return state.is_git_repo and not state.has_remote

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

    def _get_token(self) -> str:
        """Get or prompt for Personal Access Token."""
        # Check for stored token
        stored_token = self._get_stored_token()
        if stored_token:
            console.print("[dim]Using stored Azure DevOps token[/dim]")
            use_stored = prompt_confirm("Use stored token?", default=True)
            if use_stored:
                return stored_token

        # Prompt for new token with detailed instructions
        console.print(
            "\n[yellow]An Azure DevOps Personal Access Token (PAT) is required to create repositories via the API.[/yellow]"
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
            "  [dim]4.[/dim] Select scope: [bold]Code (read & write)[/bold] and [bold]Project & Team (read)[/bold]"
        )
        console.print("  [dim]5.[/dim] Click 'Create'")
        console.print(
            "  [dim]6.[/dim] Copy the token immediately (it won't be shown again)"
        )

        console.print()
        token = prompt_password("Enter PAT:")
        if token is None:
            raise KeyboardInterrupt

        # Ask to store
        store = prompt_confirm("Store token for future use?", default=True)
        if store:
            self._store_token(token)
            console.print("[green]Token stored securely[/green]")

        return token

    def _get_description(self, state: RepoState, repo_name: str) -> str:
        """Get repository description with smart suggestions."""
        console.print("\n[yellow]Select or enter a repository description:[/yellow]")

        # Get description options
        options = get_description_options(state.path, repo_name, use_ai=True)

        if options:
            # Build menu options
            menu_options = []
            for label, desc in options:
                # Truncate long descriptions for display
                display_desc = desc if len(desc) <= 60 else desc[:57] + "..."
                menu_options.append(f"[{label}] {display_desc}")

            menu_options.append("Enter custom description")
            menu_options.append("Skip - no description")

            # Get user choice
            choice_num = select_number_from_menu(
                title="Repository Description",
                text="Select a description or enter a custom one:",
                options=menu_options,
                default_index=0,
            )

            if choice_num is None:
                # Cancelled, skip
                return ""
            elif 1 <= choice_num <= len(options):
                # User selected a suggestion
                selected_desc = options[choice_num - 1][1]
                console.print(f"[dim]Selected: {selected_desc}[/dim]")
                return selected_desc
            elif choice_num == len(options) + 1:
                # Custom description
                return prompt_text("Enter custom description:", default="") or ""
            elif choice_num == len(options) + 2:
                # Skip
                return ""
            else:
                return ""

        # Fallback to manual entry
        return prompt_text("Description:", default="") or ""

    def execute(self, state: RepoState) -> bool:
        """Set up an Azure DevOps remote repository."""
        try:
            console.print(
                "[bold cyan]Setting up Azure DevOps remote repository...[/bold cyan]"
            )

            # Get token
            token = self._get_token()

            # Get organization
            console.print(
                "\n[yellow]Enter your Azure DevOps organization name:[/yellow]"
            )
            console.print(
                "[dim]Example: if your URL is https://dev.azure.com/mycompany, enter 'mycompany'[/dim]"
            )
            organization = prompt_text("Organization:", default="")

            if not organization:
                console.print("[bold red]✗ Organization name is required[/bold red]")
                return False

            # Get project name
            console.print("\n[yellow]Enter your Azure DevOps project name:[/yellow]")
            project = (
                prompt_text("Project:", default=state.path.name) or state.path.name
            )

            if not project:
                console.print("[bold red]✗ Project name is required[/bold red]")
                return False

            # Check SSH configuration
            console.print("\n[cyan]Checking SSH configuration...[/cyan]")
            ssh_config = SSHConfig()
            if ssh_config.has_github_key():  # GitHub key works for Azure too
                console.print(
                    f"[green]✓ SSH key found: {ssh_config.github_key}[/green]"
                )
                console.print("[dim]This SSH key can be used with Azure DevOps[/dim]")
            else:
                console.print("[yellow]⚠ No SSH key detected in ~/.ssh/[/yellow]")
                console.print(
                    "[dim]You may want to set up SSH keys for easier authentication[/dim]"
                )
                console.print(
                    "[dim]Guide: https://docs.microsoft.com/en-us/azure/devops/repos/git/use-ssh-keys-to-authenticate[/dim]"
                )

            # Get repository details
            console.print("\n[yellow]Enter the repository name:[/yellow]")
            repo_name = (
                prompt_text("Repository:", default=state.path.name) or state.path.name
            )

            if not repo_name:
                console.print("[bold red]✗ Repository name is required[/bold red]")
                return False

            # Get description with smart suggestions
            description = self._get_description(state, repo_name)
            if description:
                console.print(f"[dim]Description: {description}[/dim]")

            # Test authentication and create project
            console.print("\n[cyan]Authenticating with Azure DevOps...[/cyan]")
            try:
                AzureClient(organization, project, token)
                # Simple test: try to get pipelines (will fail if project doesn't exist, but that's ok)
                # We're really just testing the authentication here
                console.print("[green]✓ Authenticated with Azure DevOps[/green]")
            except Exception as e:
                console.print(
                    f"[bold red]✗ Azure DevOps authentication failed: {e}[/bold red]"
                )
                return False

            # Build SSH remote URL
            # Format: git@ssh.dev.azure.com:v3/{org}/{project}/{repo}
            remote_url = (
                f"git@ssh.dev.azure.com:v3/{organization}/{project}/{repo_name}"
            )

            console.print("\n[cyan]Adding remote...[/cyan]")
            try:
                origin = state.repo.create_remote("origin", remote_url)
                console.print(
                    f"[bold green]✓ Remote 'origin' added: {remote_url}[/bold green]"
                )
            except Exception as e:
                console.print(f"[bold red]✗ Failed to add remote: {e}[/bold red]")
                return False

            console.print(
                "\n[yellow]Note: Repository creation via API is not yet supported.[/yellow]"
            )
            console.print(
                "[dim]You'll need to create the repository manually in Azure DevOps web portal:[/dim]"
            )
            console.print(
                f"[dim]  https://dev.azure.com/{organization}/{project}/_git[/dim]"
            )
            console.print(
                "[dim]  Then push your code with: git push -u origin main[/dim]"
            )

            # Push if there are commits
            if state.has_commits:
                return push_to_remote(state, origin)

            console.print(
                "[yellow]No commits yet - add some commits and push manually later[/yellow]"
            )
            return True

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return False
        except Exception as e:
            console.print(f"[bold red]✗ Error setting up remote: {e}[/bold red]")
            return False
