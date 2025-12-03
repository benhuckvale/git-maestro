"""Action to initialize a git repository."""

import git
from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from .base import Action
from git_maestro.state import RepoState

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
            console.print(f"[bold green]Initializing git repository in {state.path}...[/bold green]")

            # Ask for initial branch name
            console.print("\n[yellow]Select initial branch name:[/yellow]")
            console.print("1. main")
            console.print("2. master")
            console.print("3. develop")
            console.print("4. custom")

            branch_completer = WordCompleter(["1", "2", "3", "4", "main", "master", "develop", "custom"])
            choice = prompt("Choice (1-4): ", completer=branch_completer, default="1")

            # Map choice to branch name
            branch_map = {
                "1": "main",
                "2": "master",
                "3": "develop",
                "main": "main",
                "master": "master",
                "develop": "develop",
            }

            if choice.lower() in branch_map:
                branch_name = branch_map[choice.lower()]
            elif choice == "4" or choice.lower() == "custom":
                console.print("\n[yellow]Enter custom branch name:[/yellow]")
                branch_name = prompt("Branch name: ", default="main")
            else:
                branch_name = "main"

            # Initialize repository
            repo = git.Repo.init(state.path)
            console.print("[bold green]✓ Git repository initialized![/bold green]")

            # Create initial commit to allow branch renaming
            console.print(f"[bold cyan]Setting initial branch to '{branch_name}'...[/bold cyan]")

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
