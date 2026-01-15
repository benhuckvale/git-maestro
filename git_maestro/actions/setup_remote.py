"""Action to set up a remote repository."""

import os
from pathlib import Path
from typing import Optional

import gitlab
from github import Github, GithubException
from rich.console import Console

from .base import Action
from git_maestro.state import RepoState
from git_maestro.ssh_config import SSHConfig
from git_maestro.description_helper import get_description_options
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


class SetupRemoteAction(Action):
    """Set up a remote repository (GitHub/GitLab)."""

    def __init__(self):
        super().__init__()
        self.name = "Setup Remote Repository"
        self.description = "Create and connect to a GitHub/GitLab repository"
        self.emoji = "🌐"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the directory is a git repo without a remote."""
        return state.is_git_repo and not state.has_remote

    def _get_stored_token(self, provider: str) -> Optional[str]:
        """Get stored token for a provider."""
        if not CONFIG_FILE.exists():
            return None
        try:
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    if line.startswith(f"{provider}="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            return None
        return None

    def _store_token(self, provider: str, token: str):
        """Store token for a provider."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Ensure directory has correct permissions (even if it existed)
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
        tokens[provider] = token

        # Write back
        try:
            with open(CONFIG_FILE, "w") as f:
                for key, value in tokens.items():
                    f.write(f"{key}={value}\n")
            # Make file readable only by user
            os.chmod(CONFIG_FILE, 0o600)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not store token: {e}[/yellow]")

    def _get_token(self, provider: str) -> str:
        """Get or prompt for access token."""
        # Check for stored token
        stored_token = self._get_stored_token(provider)
        if stored_token:
            console.print(f"[dim]Using stored {provider} token[/dim]")
            use_stored = prompt_confirm("Use stored token?", default=True)
            if use_stored:
                return stored_token

        # Prompt for new token with detailed instructions
        console.print(
            f"\n[yellow]A {provider.title()} Personal Access Token is required to create repositories via the API.[/yellow]"
        )
        console.print(
            "[yellow]This is different from your SSH key (used for git push/pull).[/yellow]\n"
        )

        if provider == "github":
            console.print("[cyan]To create a GitHub Personal Access Token:[/cyan]")
            console.print(
                "  [dim]1.[/dim] Go to [blue]https://github.com/settings/tokens[/blue]"
            )
            console.print(
                "  [dim]2.[/dim] Click 'Generate new token' → 'Generate new token (classic)'"
            )
            console.print("  [dim]3.[/dim] Give it a name like 'git-maestro'")
            console.print(
                "  [dim]4.[/dim] Select scope: [bold]repo[/bold] (full control of private repositories)"
            )
            console.print("  [dim]5.[/dim] Click 'Generate token'")
            console.print(
                "  [dim]6.[/dim] Copy the token (starts with [dim]ghp_...[/dim])"
            )
        else:  # gitlab
            console.print("[cyan]To create a GitLab Personal Access Token:[/cyan]")
            console.print(
                "  [dim]1.[/dim] Go to [blue]https://gitlab.com/-/profile/personal_access_tokens[/blue]"
            )
            console.print("  [dim]2.[/dim] Click 'Add new token'")
            console.print("  [dim]3.[/dim] Give it a name like 'git-maestro'")
            console.print(
                "  [dim]4.[/dim] Select scope: [bold]api[/bold] (full API access)"
            )
            console.print("  [dim]5.[/dim] Click 'Create personal access token'")
            console.print(
                "  [dim]6.[/dim] Copy the token (starts with [dim]glpat-...[/dim])"
            )

        console.print()
        token = prompt_password("Enter token:")
        if token is None:
            raise KeyboardInterrupt

        # Ask to store
        store = prompt_confirm("Store token for future use?", default=True)
        if store:
            self._store_token(provider, token)
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
        """Set up a remote repository."""
        try:
            console.print("[bold cyan]Setting up remote repository...[/bold cyan]")

            # Ask for provider
            console.print("\n[yellow]Select a git hosting provider:[/yellow]")
            provider_choice = select_number_from_menu(
                title="Remote Provider",
                text="Select a remote provider:",
                options=[
                    "GitHub (will create repository via API)",
                    "GitLab (will create repository via API)",
                    "Azure DevOps (manual repository creation)",
                    "Other (just add remote URL, won't create repository)",
                ],
                default_index=0,
            )

            if provider_choice is None:
                console.print("[yellow]Cancelled[/yellow]")
                return False

            # Handle GitHub
            if provider_choice == 1:
                return self._setup_github(state)

            # Handle GitLab
            elif provider_choice == 2:
                return self._setup_gitlab(state)

            # Handle Azure DevOps
            elif provider_choice == 3:
                from .setup_azure_devops import SetupAzureDevOpsAction
                azure_action = SetupAzureDevOpsAction()
                return azure_action.execute(state)

            # Handle other/manual
            elif provider_choice == 4:
                return self._setup_manual(state)

            else:
                console.print("[yellow]Invalid choice[/yellow]")
                return False

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return False
        except Exception as e:
            console.print(f"[bold red]✗ Error setting up remote: {e}[/bold red]")
            return False

    def _setup_github(self, state: RepoState) -> bool:
        """Set up GitHub repository."""
        try:
            # Get token
            token = self._get_token("github")

            # Connect to GitHub
            console.print("[cyan]Connecting to GitHub...[/cyan]")
            g = Github(token)
            user = g.get_user()
            console.print(f"[green]✓ Authenticated as {user.login}[/green]")

            # Check SSH configuration
            console.print("\n[cyan]Checking SSH configuration...[/cyan]")
            ssh_config = SSHConfig()
            if ssh_config.has_github_key():
                console.print(
                    f"[green]✓ SSH key found: {ssh_config.github_key}[/green]"
                )

                # Verify if key is added to GitHub account
                is_verified, message = ssh_config.verify_key_on_github(g)
                if is_verified:
                    console.print(f"[green]✓ {message}[/green]")
                else:
                    console.print(f"[yellow]⚠ {message}[/yellow]")
                    console.print(
                        "[dim]Add your SSH key at: https://github.com/settings/keys[/dim]"
                    )
                    console.print(
                        f"[dim]Public key: {ssh_config.get_github_public_key()}[/dim]"
                    )
            else:
                console.print(
                    "[yellow]⚠ No GitHub SSH key detected in ~/.ssh/[/yellow]"
                )
                console.print(
                    "[dim]You may want to set up SSH keys for easier authentication[/dim]"
                )
                console.print(
                    "[dim]Guide: https://docs.github.com/en/authentication/connecting-to-github-with-ssh[/dim]"
                )

            # Get repository details
            console.print("\n[yellow]Enter the repository name:[/yellow]")
            repo_name = prompt_text("Repository:", default=state.path.name) or state.path.name

            # Get description with smart suggestions
            description = self._get_description(state, repo_name)

            visibility_choice = select_number_from_menu(
                title="Repository Visibility",
                text="Select repository visibility:",
                options=[
                    "Public",
                    "Private",
                ],
                default_index=0,
            )

            if visibility_choice is None:
                console.print("[yellow]Cancelled, using Public[/yellow]")
                is_private = False
            else:
                is_private = (visibility_choice == 2)

            # Create repository
            console.print(f"\n[cyan]Creating GitHub repository '{repo_name}'...[/cyan]")
            try:
                github_repo = user.create_repo(
                    name=repo_name,
                    description=description,
                    private=is_private,
                    auto_init=False,
                )
                console.print(
                    f"[bold green]✓ Repository created: {github_repo.html_url}[/bold green]"
                )
            except GithubException as e:
                if e.status == 422:
                    console.print(
                        f"[yellow]Repository '{repo_name}' already exists[/yellow]"
                    )
                    github_repo = user.get_repo(repo_name)
                else:
                    raise

            # Add remote
            remote_url = github_repo.ssh_url
            origin = state.repo.create_remote("origin", remote_url)
            console.print(
                f"[bold green]✓ Remote 'origin' added: {remote_url}[/bold green]"
            )

            # Push if there are commits
            if state.has_commits:
                return push_to_remote(state, origin)

            console.print(
                "[yellow]No commits yet - add some commits and push manually later[/yellow]"
            )
            return True

        except GithubException as e:
            console.print(f"[bold red]✗ GitHub API error: {e}[/bold red]")
            return False

    def _setup_gitlab(self, state: RepoState) -> bool:
        """Set up GitLab repository."""
        try:
            # Get token
            token = self._get_token("gitlab")

            # Connect to GitLab
            console.print("[cyan]Connecting to GitLab...[/cyan]")
            gl = gitlab.Gitlab("https://gitlab.com", private_token=token)
            gl.auth()
            user = gl.user
            console.print(f"[green]✓ Authenticated as {user.username}[/green]")

            # Check SSH configuration
            console.print("\n[cyan]Checking SSH configuration...[/cyan]")
            ssh_config = SSHConfig()
            if ssh_config.has_gitlab_key():
                console.print(
                    f"[green]✓ SSH key found: {ssh_config.gitlab_key}[/green]"
                )

                # Verify if key is added to GitLab account
                is_verified, message = ssh_config.verify_key_on_gitlab(gl)
                if is_verified:
                    console.print(f"[green]✓ {message}[/green]")
                else:
                    console.print(f"[yellow]⚠ {message}[/yellow]")
                    console.print(
                        "[dim]Add your SSH key at: https://gitlab.com/-/profile/keys[/dim]"
                    )
                    console.print(
                        f"[dim]Public key: {ssh_config.get_gitlab_public_key()}[/dim]"
                    )
            else:
                console.print(
                    "[yellow]⚠ No GitLab SSH key detected in ~/.ssh/[/yellow]"
                )
                console.print(
                    "[dim]You may want to set up SSH keys for easier authentication[/dim]"
                )
                console.print(
                    "[dim]Guide: https://docs.gitlab.com/ee/user/ssh.html[/dim]"
                )

            # Get repository details
            console.print("\n[yellow]Enter the repository name:[/yellow]")
            repo_name = prompt_text("Repository:", default=state.path.name) or state.path.name

            # Get description with smart suggestions
            description = self._get_description(state, repo_name)

            visibility_choice = select_number_from_menu(
                title="Repository Visibility",
                text="Select repository visibility:",
                options=[
                    "Public",
                    "Internal (visible to authenticated users)",
                    "Private",
                ],
                default_index=0,
            )

            if visibility_choice is None:
                console.print("[yellow]Cancelled, using Public[/yellow]")
                visibility = "public"
            elif visibility_choice == 1:
                visibility = "public"
            elif visibility_choice == 2:
                visibility = "internal"
            elif visibility_choice == 3:
                visibility = "private"
            else:
                visibility = "public"

            # Create repository
            console.print(f"\n[cyan]Creating GitLab repository '{repo_name}'...[/cyan]")
            try:
                project = gl.projects.create(
                    {
                        "name": repo_name,
                        "description": description,
                        "visibility": visibility,
                        "initialize_with_readme": False,
                    }
                )
                console.print(
                    f"[bold green]✓ Repository created: {project.web_url}[/bold green]"
                )
            except gitlab.exceptions.GitlabCreateError as e:
                if "has already been taken" in str(e):
                    console.print(
                        f"[yellow]Repository '{repo_name}' already exists[/yellow]"
                    )
                    projects = gl.projects.list(search=repo_name, owned=True)
                    project = next((p for p in projects if p.name == repo_name), None)
                    if not project:
                        raise Exception(
                            f"Could not find existing project '{repo_name}'"
                        )
                else:
                    raise

            # Add remote
            remote_url = project.ssh_url_to_repo
            origin = state.repo.create_remote("origin", remote_url)
            console.print(
                f"[bold green]✓ Remote 'origin' added: {remote_url}[/bold green]"
            )

            # Push if there are commits
            if state.has_commits:
                return push_to_remote(state, origin)

            console.print(
                "[yellow]No commits yet - add some commits and push manually later[/yellow]"
            )
            return True

        except gitlab.exceptions.GitlabAuthenticationError:
            console.print(
                "[bold red]✗ GitLab authentication failed - check your token[/bold red]"
            )
            return False
        except Exception as e:
            console.print(f"[bold red]✗ GitLab error: {e}[/bold red]")
            return False

    def _setup_manual(self, state: RepoState) -> bool:
        """Set up manual remote URL."""
        console.print("\n[yellow]Enter the remote repository URL:[/yellow]")
        remote_url = prompt_text("URL:", default="")
        if not remote_url:
            console.print("[yellow]No remote URL entered. Cancelled.[/yellow]")
            return False

        # Add remote
        origin = state.repo.create_remote("origin", remote_url)
        console.print(f"[bold green]✓ Remote 'origin' added: {remote_url}[/bold green]")

        console.print(
            "\n[yellow]Note: Make sure the repository exists on the remote server[/yellow]"
        )

        # Ask if user wants to push
        if state.has_commits:
            return push_to_remote(state, origin)

        return True
