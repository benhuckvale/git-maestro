"""Action to set up a remote repository."""

import os
from pathlib import Path
from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from github import Github, GithubException
import gitlab
from .base import Action
from git_maestro.state import RepoState
from git_maestro.ssh_config import SSHConfig
from git_maestro.description_helper import get_description_options

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

    def _get_stored_token(self, provider: str) -> str | None:
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
            use_stored = prompt("Use stored token? (y/n): ", default="y").lower()
            if use_stored == "y":
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
        token = prompt("Enter token: ", is_password=True)

        # Ask to store
        store = prompt("Store token for future use? (y/n): ", default="y").lower()
        if store == "y":
            self._store_token(provider, token)
            console.print("[green]Token stored securely[/green]")

        return token

    def _get_description(self, state: RepoState, repo_name: str) -> str:
        """Get repository description with smart suggestions."""
        console.print("\n[yellow]Select or enter a repository description:[/yellow]")

        # Get description options
        options = get_description_options(state.path, repo_name, use_ai=True)

        if options:
            # Show available options
            console.print("\n[cyan]Suggestions:[/cyan]")
            for i, (label, desc) in enumerate(options, 1):
                # Truncate long descriptions for display
                display_desc = desc if len(desc) <= 80 else desc[:77] + "..."
                console.print(f"  [dim]{i}.[/dim] [{label}] {display_desc}")

            console.print(
                f"  [dim]{len(options) + 1}.[/dim] [Enter custom description]"
            )
            console.print(f"  [dim]{len(options) + 2}.[/dim] [Skip - no description]")

            # Build completer
            choices = [str(i) for i in range(1, len(options) + 3)]
            completer = WordCompleter(choices)

            # Get user choice
            choice = prompt(
                f"\nChoice (1-{len(options) + 2}): ", completer=completer, default="1"
            )

            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(options):
                    # User selected a suggestion
                    selected_desc = options[choice_num - 1][1]
                    console.print(f"[dim]Selected: {selected_desc}[/dim]")
                    return selected_desc
                elif choice_num == len(options) + 1:
                    # Custom description
                    return prompt("Enter custom description: ", default="")
                elif choice_num == len(options) + 2:
                    # Skip
                    return ""
            except (ValueError, IndexError):
                pass

        # Fallback to manual entry
        return prompt("Description: ", default="")

    def execute(self, state: RepoState) -> bool:
        """Set up a remote repository."""
        try:
            console.print("[bold cyan]Setting up remote repository...[/bold cyan]")

            # Ask for provider
            console.print("\n[yellow]Select a git hosting provider:[/yellow]")
            console.print("1. GitHub (will create repository via API)")
            console.print("2. GitLab (will create repository via API)")
            console.print("3. Other (just add remote URL, won't create repository)")

            provider_completer = WordCompleter(
                ["1", "2", "3", "github", "gitlab", "other"]
            )
            provider_choice = prompt(
                "Choice (1-3): ", completer=provider_completer, default="1"
            )

            # Handle GitHub
            if provider_choice in ["1", "github"]:
                return self._setup_github(state)

            # Handle GitLab
            elif provider_choice in ["2", "gitlab"]:
                return self._setup_gitlab(state)

            # Handle other/manual
            else:
                return self._setup_manual(state)

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
            repo_name = prompt("Repository: ", default=state.path.name)

            # Get description with smart suggestions
            description = self._get_description(state, repo_name)

            console.print("\n[yellow]Select repository visibility:[/yellow]")
            console.print("1. Public")
            console.print("2. Private")
            visibility_completer = WordCompleter(["1", "2", "public", "private"])
            visibility_choice = prompt(
                "Visibility (1-2): ", completer=visibility_completer, default="1"
            )

            is_private = visibility_choice in ["2", "private"]

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
                return self._push_to_remote(state, origin)

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
            repo_name = prompt("Repository: ", default=state.path.name)

            # Get description with smart suggestions
            description = self._get_description(state, repo_name)

            console.print("\n[yellow]Select repository visibility:[/yellow]")
            console.print("1. Public")
            console.print("2. Internal (visible to authenticated users)")
            console.print("3. Private")
            visibility_completer = WordCompleter(
                ["1", "2", "3", "public", "internal", "private"]
            )
            visibility_choice = prompt(
                "Visibility (1-3): ", completer=visibility_completer, default="1"
            )

            # Map choice to GitLab visibility value
            visibility_map = {
                "1": "public",
                "2": "internal",
                "3": "private",
                "public": "public",
                "internal": "internal",
                "private": "private",
            }
            visibility = visibility_map.get(visibility_choice.lower(), "public")

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
                return self._push_to_remote(state, origin)

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
        remote_url = prompt("URL: ")

        # Add remote
        origin = state.repo.create_remote("origin", remote_url)
        console.print(f"[bold green]✓ Remote 'origin' added: {remote_url}[/bold green]")

        console.print(
            "\n[yellow]Note: Make sure the repository exists on the remote server[/yellow]"
        )

        # Ask if user wants to push
        if state.has_commits:
            return self._push_to_remote(state, origin)

        return True

    def _push_to_remote(self, state: RepoState, origin) -> bool:
        """Push to remote repository."""
        console.print("\n[yellow]Push to remote now?[/yellow]")
        should_push = prompt("Push (y/n): ", default="y").lower()

        if should_push == "y":
            try:
                console.print("[cyan]Pushing to remote...[/cyan]")
                branch = state.repo.active_branch.name
                origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
                console.print(
                    "[bold green]✓ Pushed to remote successfully![/bold green]"
                )
            except Exception as push_error:
                console.print(f"[bold red]✗ Push failed: {push_error}[/bold red]")
                console.print(
                    "[yellow]You can push manually later with: git push -u origin {branch}[/yellow]".format(
                        branch=branch
                    )
                )
                return False

        return True
