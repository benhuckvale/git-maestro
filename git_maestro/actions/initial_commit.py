"""Action to create the initial commit in a repository."""

from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from .base import Action
from git_maestro.state import RepoState

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
            console.print(f"\n[yellow]Found {len(untracked)} untracked file(s)[/yellow]")

            if untracked:
                console.print("[dim]Files:[/dim]")
                for f in untracked[:10]:  # Show first 10
                    console.print(f"  [dim]- {f}[/dim]")
                if len(untracked) > 10:
                    console.print(f"  [dim]... and {len(untracked) - 10} more[/dim]")

            # Ask what to include in initial commit
            console.print("\n[yellow]What should be included in the initial commit?[/yellow]")
            console.print("1. All existing files")
            console.print("2. Only README and .gitignore (if they exist)")
            console.print("3. Create an empty commit")
            console.print("4. Select files manually (not implemented yet)")

            choice_completer = WordCompleter(["1", "2", "3", "4"])
            choice = prompt("Choice (1-3): ", completer=choice_completer, default="1")

            files_to_add = []
            allow_empty = False

            if choice == "1":
                # Add all files
                files_to_add = untracked
            elif choice == "2":
                # Only README and .gitignore
                for f in untracked:
                    if f.lower().startswith('readme') or f == '.gitignore':
                        files_to_add.append(f)
            elif choice == "3":
                # Empty commit
                allow_empty = True
            else:
                console.print("[yellow]Manual file selection not implemented yet. Using all files.[/yellow]")
                files_to_add = untracked

            # Add files to staging
            if files_to_add:
                console.print(f"\n[cyan]Adding {len(files_to_add)} file(s) to staging...[/cyan]")
                state.repo.index.add(files_to_add)
                console.print("[green]✓ Files staged[/green]")

            # Get commit message
            console.print("\n[yellow]Enter commit message:[/yellow]")
            commit_message = prompt("Message: ", default="Initial commit")

            # Select branch name
            console.print("\n[yellow]Select default branch name:[/yellow]")
            console.print("1. main")
            console.print("2. master")
            console.print("3. develop")
            console.print("4. custom")

            branch_completer = WordCompleter(["1", "2", "3", "4", "main", "master", "develop"])
            branch_choice = prompt("Branch (1-4): ", completer=branch_completer, default="1")

            branch_map = {
                "1": "main",
                "2": "master",
                "3": "develop",
                "main": "main",
                "master": "master",
                "develop": "develop",
            }

            if branch_choice.lower() in branch_map:
                branch_name = branch_map[branch_choice.lower()]
            elif branch_choice == "4":
                branch_name = prompt("Enter branch name: ", default="main")
            else:
                branch_name = "main"

            # Create the commit
            console.print(f"\n[cyan]Creating commit on branch '{branch_name}'...[/cyan]")

            if allow_empty:
                state.repo.index.commit(commit_message, skip_hooks=False)
            else:
                state.repo.index.commit(commit_message)

            console.print(f"[green]✓ Commit created: {commit_message}[/green]")

            # Rename branch if needed (git will create a default branch on first commit)
            try:
                current_branch = state.repo.active_branch.name
                if current_branch != branch_name:
                    console.print(f"[cyan]Renaming branch '{current_branch}' to '{branch_name}'...[/cyan]")
                    state.repo.active_branch.rename(branch_name)
                    console.print(f"[green]✓ Branch renamed to '{branch_name}'[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠ Could not rename branch: {e}[/yellow]")

            # Ask about pushing
            if state.has_remote:
                console.print(f"\n[yellow]Push to remote ({state.remote_url})?[/yellow]")
                should_push = prompt("Push (y/n): ", default="y").lower()

                if should_push == "y":
                    try:
                        console.print(f"[cyan]Pushing to origin {branch_name}...[/cyan]")
                        origin = state.repo.remotes.origin
                        origin.push(refspec=f"{branch_name}:{branch_name}", set_upstream=True)
                        console.print("[bold green]✓ Pushed to remote successfully![/bold green]")
                    except Exception as push_error:
                        console.print(f"[bold red]✗ Push failed: {push_error}[/bold red]")
                        console.print(f"[yellow]You can push manually later with:[/yellow]")
                        console.print(f"[dim]  git push -u origin {branch_name}[/dim]")

            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error creating initial commit: {e}[/bold red]")
            return False
