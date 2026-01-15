"""Action to initialize a git repository."""

import git
from rich.console import Console

from .base import Action
from git_maestro.state import RepoState
from git_maestro.selection_helper import prompt_text, select_number_from_menu

console = Console()


class InitRepoAction(Action):
    """Initialize a git repository in the current directory."""

    def __init__(self):
        super().__init__()
        self.name = "Initialize Git Repository"
        self.description = "Run 'git init' to create a new git repository"
        self.emoji = "🎬"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is only applicable if the directory is not a git repo."""
        return not state.is_git_repo

    def execute(self, state: RepoState) -> bool:
        """Initialize the git repository."""
        try:
            console.print(
                f"[bold green]Initializing git repository in {state.path}...[/bold green]"
            )

            # Ask for initial branch name
            choice = select_number_from_menu(
                title="Initial Branch",
                text="Select initial branch name:",
                options=[
                    "main",
                    "master",
                    "develop",
                    "custom (enter name)",
                ],
                default_index=0,
            )

            if choice is None:
                console.print("[yellow]Cancelled, using 'main'[/yellow]")
                branch_name = "main"
            elif choice == 1:
                branch_name = "main"
            elif choice == 2:
                branch_name = "master"
            elif choice == 3:
                branch_name = "develop"
            elif choice == 4:
                console.print("\n[yellow]Enter custom branch name:[/yellow]")
                branch_name = prompt_text("Branch name:", default="main") or "main"
            else:
                branch_name = "main"

            # Initialize repository
            repo = git.Repo.init(state.path)
            console.print("[bold green]✓ Git repository initialized![/bold green]")

            # Create initial commit to allow branch renaming
            console.print(
                f"[bold cyan]Setting initial branch to '{branch_name}'...[/bold cyan]"
            )

            # Git requires at least one commit to rename branch
            # We'll create an empty initial commit
            repo.index.commit("Initial commit")

            # Rename the branch
            repo.head.reference = repo.heads[repo.active_branch.name]
            repo.head.reference.rename(branch_name)

            console.print(f"[bold green]✓ Branch set to '{branch_name}'![/bold green]")
            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error initializing repository: {e}[/bold red]")
            return False
