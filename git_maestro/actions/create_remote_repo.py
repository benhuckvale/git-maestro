"""Action to create a repository on an existing remote."""

import re
from typing import Optional
from rich.console import Console
from prompt_toolkit import prompt
from github import Github, GithubException
import gitlab
from .base import Action
from .setup_remote import SetupRemoteAction
from git_maestro.state import RepoState
from git_maestro.ssh_config import SSHConfig

console = Console()


class CreateRemoteRepoAction(Action):
    """Create repository on GitHub/GitLab when remote is already configured."""

    def __init__(self):
        super().__init__()
        self.name = "Create Repository on Remote"
        self.description = (
            "Create the repository on GitHub/GitLab (remote exists but repo doesn't)"
        )
        self.emoji = "🏗️"
        self.setup_action = SetupRemoteAction()

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if there's a remote but the repo doesn't exist on GitHub/GitLab."""
        if not state.has_remote or not state.remote_url:
            return False

        # Check if it's a GitHub or GitLab URL
        remote_url = state.remote_url.lower()
        if not ("github.com" in remote_url or "gitlab.com" in remote_url):
            return False

        # Check if the remote repository actually exists
        # Use git ls-remote to test if we can access the remote repo
        try:
            import subprocess

            result = subprocess.run(
                ["git", "ls-remote", "--heads", "origin"],
                cwd=state.path,
                capture_output=True,
                timeout=5,
            )
            # If ls-remote succeeds, the repo exists on the remote
            if result.returncode == 0:
                return False  # Repo exists, no need to create it

            # If it fails (e.g., repo doesn't exist), we should offer to create it
            return True
        except (subprocess.TimeoutExpired, Exception):
            # If we can't check, assume the action is applicable
            # Better to show the option and let the user decide
            return True

    def _parse_remote_url(self, remote_url: str) -> Optional[tuple[str, str, str]]:
        """
        Parse remote URL to extract provider, username, and repo name.
        Returns: (provider, username, repo_name) or None
        """
        # Handle SSH URLs like git@github.com:username/repo.git
        ssh_match = re.match(
            r"git@(github|gitlab)\.com:([^/]+)/(.+?)(?:\.git)?$", remote_url
        )
        if ssh_match:
            provider = ssh_match.group(1)
            username = ssh_match.group(2)
            repo_name = ssh_match.group(3)
            return (provider, username, repo_name)

        # Handle HTTPS URLs like https://github.com/username/repo.git
        https_match = re.match(
            r"https?://(github|gitlab)\.com/([^/]+)/(.+?)(?:\.git)?$", remote_url
        )
        if https_match:
            provider = https_match.group(1)
            username = https_match.group(2)
            repo_name = https_match.group(3)
            return (provider, username, repo_name)

        return None

    def _check_repo_exists_github(
        self, token: str, username: str, repo_name: str
    ) -> bool:
        """Check if repository exists on GitHub."""
        try:
            g = Github(token)
            user = g.get_user()
            try:
                user.get_repo(repo_name)
                return True
            except GithubException as e:
                if e.status == 404:
                    return False
                raise
        except Exception:
            return False

    def _check_repo_exists_gitlab(
        self, token: str, username: str, repo_name: str
    ) -> bool:
        """Check if repository exists on GitLab."""
        try:
            gl = gitlab.Gitlab("https://gitlab.com", private_token=token)
            gl.auth()
            projects = gl.projects.list(search=repo_name, owned=True)
            return any(p.name == repo_name for p in projects)
        except Exception:
            return False

    def execute(self, state: RepoState) -> bool:
        """Create repository on the remote platform."""
        try:
            console.print(
                "[bold cyan]Creating repository on remote platform...[/bold cyan]"
            )

            # Parse the remote URL
            parsed = self._parse_remote_url(state.remote_url)
            if not parsed:
                console.print(
                    f"[bold red]✗ Could not parse remote URL: {state.remote_url}[/bold red]"
                )
                console.print(
                    "[yellow]This action only supports GitHub and GitLab URLs[/yellow]"
                )
                return False

            provider, username, repo_name = parsed
            console.print(
                f"[dim]Detected {provider.title()} repository: {username}/{repo_name}[/dim]"
            )

            # Get token
            token = self.setup_action._get_token(provider)

            # Check SSH configuration
            console.print("\n[cyan]Checking SSH configuration...[/cyan]")
            ssh_config = SSHConfig()

            if provider == "github":
                if ssh_config.has_github_key():
                    console.print(
                        f"[green]✓ SSH key found: {ssh_config.github_key}[/green]"
                    )
                    # We'll verify after connecting to the API
                else:
                    console.print(
                        "[yellow]⚠ No GitHub SSH key detected in ~/.ssh/[/yellow]"
                    )
                    console.print(
                        "[dim]Guide: https://docs.github.com/en/authentication/connecting-to-github-with-ssh[/dim]"
                    )
            else:  # gitlab
                if ssh_config.has_gitlab_key():
                    console.print(
                        f"[green]✓ SSH key found: {ssh_config.gitlab_key}[/green]"
                    )
                else:
                    console.print(
                        "[yellow]⚠ No GitLab SSH key detected in ~/.ssh/[/yellow]"
                    )
                    console.print(
                        "[dim]Guide: https://docs.gitlab.com/ee/user/ssh.html[/dim]"
                    )

            # Check if repository already exists
            console.print(
                f"\n[cyan]Checking if repository exists on {provider.title()}...[/cyan]"
            )
            if provider == "github":
                exists = self._check_repo_exists_github(token, username, repo_name)
            else:  # gitlab
                exists = self._check_repo_exists_gitlab(token, username, repo_name)

            if exists:
                console.print(
                    f"[bold green]✓ Repository already exists on {provider.title()}![/bold green]"
                )
                console.print(
                    f"[yellow]You can push with: git push -u origin {state.branch_name or 'main'}[/yellow]"
                )
                return True

            # Repository doesn't exist, create it
            console.print(
                f"[yellow]Repository does not exist on {provider.title()}[/yellow]"
            )

            # Get description with smart suggestions
            description = self.setup_action._get_description(state, repo_name)

            if provider == "github":
                console.print("\n[yellow]Select repository visibility:[/yellow]")
                console.print("1. Public")
                console.print("2. Private")
                from prompt_toolkit.completion import WordCompleter

                visibility_completer = WordCompleter(["1", "2", "public", "private"])
                visibility_choice = prompt(
                    "Visibility (1-2): ", completer=visibility_completer, default="1"
                )
                is_private = visibility_choice in ["2", "private"]

                # Create GitHub repository
                console.print(
                    f"\n[cyan]Creating GitHub repository '{repo_name}'...[/cyan]"
                )
                g = Github(token)
                user = g.get_user()
                github_repo = user.create_repo(
                    name=repo_name,
                    description=description,
                    private=is_private,
                    auto_init=False,
                )
                console.print(
                    f"[bold green]✓ Repository created: {github_repo.html_url}[/bold green]"
                )

            else:  # gitlab
                console.print("\n[yellow]Select repository visibility:[/yellow]")
                console.print("1. Public")
                console.print("2. Internal (visible to authenticated users)")
                console.print("3. Private")
                from prompt_toolkit.completion import WordCompleter

                visibility_completer = WordCompleter(
                    ["1", "2", "3", "public", "internal", "private"]
                )
                visibility_choice = prompt(
                    "Visibility (1-3): ", completer=visibility_completer, default="1"
                )

                visibility_map = {
                    "1": "public",
                    "2": "internal",
                    "3": "private",
                    "public": "public",
                    "internal": "internal",
                    "private": "private",
                }
                visibility = visibility_map.get(visibility_choice.lower(), "public")

                # Create GitLab repository
                console.print(
                    f"\n[cyan]Creating GitLab repository '{repo_name}'...[/cyan]"
                )
                gl = gitlab.Gitlab("https://gitlab.com", private_token=token)
                gl.auth()
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

            # Offer to push
            if state.has_commits:
                console.print("\n[yellow]Push to remote now?[/yellow]")
                should_push = prompt("Push (y/n): ", default="y").lower()

                if should_push == "y":
                    try:
                        console.print("[cyan]Pushing to remote...[/cyan]")
                        branch = state.repo.active_branch.name
                        origin = state.repo.remotes.origin
                        origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
                        console.print(
                            "[bold green]✓ Pushed to remote successfully![/bold green]"
                        )
                    except Exception as push_error:
                        console.print(
                            f"[bold red]✗ Push failed: {push_error}[/bold red]"
                        )
                        console.print(
                            f"[yellow]You can push manually with: git push -u origin {branch}[/yellow]"
                        )

            return True

        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return False
        except GithubException as e:
            console.print(f"[bold red]✗ GitHub API error: {e}[/bold red]")
            return False
        except gitlab.exceptions.GitlabError as e:
            console.print(f"[bold red]✗ GitLab API error: {e}[/bold red]")
            return False
        except Exception as e:
            console.print(f"[bold red]✗ Error: {e}[/bold red]")
            return False
