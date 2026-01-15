"""Action to create the initial commit in a repository."""

from rich.console import Console

from .base import Action
from git_maestro.state import RepoState
from git_maestro.push_helper import push_to_remote
from git_maestro.selection_helper import prompt_text, select_number_from_menu

console = Console()


class InitialCommitAction(Action):
    """Create the initial commit and set up the default branch."""

    def __init__(self):
        super().__init__()
        self.name = "Create Initial Commit"
        self.description = "Make the first commit and set default branch"
        self.emoji = "🎯"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the repo exists but has no commits."""
        return state.is_git_repo and not state.has_commits

    def execute(self, state: RepoState) -> bool:
        """Create the initial commit."""
        try:
            console.print("[bold cyan]Creating initial commit...[/bold cyan]")

            # Check what files exist
            untracked = state.repo.untracked_files
            console.print(
                f"\n[yellow]Found {len(untracked)} untracked file(s)[/yellow]"
            )

            if untracked:
                console.print("[dim]Files:[/dim]")
                for f in untracked[:10]:  # Show first 10
                    console.print(f"  [dim]- {f}[/dim]")
                if len(untracked) > 10:
                    console.print(f"  [dim]... and {len(untracked) - 10} more[/dim]")

            # Ask what to include in initial commit
            choice = select_number_from_menu(
                title="Initial Commit",
                text="What should be included in the initial commit?",
                options=[
                    "All existing files",
                    "Only README and .gitignore (if they exist)",
                    "Create an empty commit",
                ],
                default_index=0,
            )

            if choice is None:
                console.print("[yellow]Cancelled[/yellow]")
                return False

            choice = str(choice)

            files_to_add = []
            allow_empty = False

            if choice == "1":
                # Add all files
                files_to_add = untracked
            elif choice == "2":
                # Only README and .gitignore
                for f in untracked:
                    if f.lower().startswith("readme") or f == ".gitignore":
                        files_to_add.append(f)
            elif choice == "3":
                # Empty commit
                allow_empty = True
            else:
                console.print(
                    "[yellow]Manual file selection not implemented yet. Using all files.[/yellow]"
                )
                files_to_add = untracked

            # Add files to staging
            if files_to_add:
                console.print(
                    f"\n[cyan]Adding {len(files_to_add)} file(s) to staging...[/cyan]"
                )
                state.repo.index.add(files_to_add)
                console.print("[green]✓ Files staged[/green]")

            # Get commit message
            console.print("\n[yellow]Enter commit message:[/yellow]")
            commit_message = (
                prompt_text("Message:", default="Initial commit") or "Initial commit"
            )

            # Select branch name
            branch_choice = select_number_from_menu(
                title="Branch Name",
                text="Select default branch name:",
                options=[
                    "main",
                    "master",
                    "develop",
                    "custom (enter name)",
                ],
                default_index=0,
            )

            if branch_choice is None:
                console.print("[yellow]Cancelled, using 'main'[/yellow]")
                branch_name = "main"
            elif branch_choice == 1:
                branch_name = "main"
            elif branch_choice == 2:
                branch_name = "master"
            elif branch_choice == 3:
                branch_name = "develop"
            elif branch_choice == 4:
                branch_name = prompt_text("Enter branch name:", default="main") or "main"
            else:
                branch_name = "main"

            # Create the commit
            console.print(
                f"\n[cyan]Creating commit on branch '{branch_name}'...[/cyan]"
            )

            if allow_empty:
                state.repo.index.commit(commit_message, skip_hooks=False)
            else:
                state.repo.index.commit(commit_message)

            console.print(f"[green]✓ Commit created: {commit_message}[/green]")

            # Rename branch if needed (git will create a default branch on first commit)
            try:
                current_branch = state.repo.active_branch.name
                if current_branch != branch_name:
                    console.print(
                        f"[cyan]Renaming branch '{current_branch}' to '{branch_name}'...[/cyan]"
                    )
                    state.repo.active_branch.rename(branch_name)
                    console.print(f"[green]✓ Branch renamed to '{branch_name}'[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ Could not rename branch: {e}[/yellow]")

            # Ask about pushing
            if state.has_remote:
                origin = state.repo.remotes.origin
                push_to_remote(state, origin)

            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error creating initial commit: {e}[/bold red]")
            return False
