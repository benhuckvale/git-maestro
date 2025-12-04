"""Menu system for git-maestro using rich and prompt-toolkit."""

from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError

from .state import RepoState
from .actions.base import Action


console = Console()


class NumberValidator(Validator):
    """Validator for menu choice input."""

    def __init__(self, max_choice: int):
        self.max_choice = max_choice

    def validate(self, document):
        text = document.text
        if text and not text.isdigit():
            raise ValidationError(message="Please enter a number")
        if text and (int(text) < 0 or int(text) > self.max_choice):
            raise ValidationError(
                message=f"Please enter a number between 0 and {self.max_choice}"
            )


class Menu:
    """Interactive menu for git-maestro."""

    def __init__(self, state: RepoState, actions: List[Action]):
        self.state = state
        self.actions = actions
        self.applicable_actions: List[Action] = []

    def display_state(self):
        """Display the current repository state."""
        table = Table(show_header=False, box=box.ROUNDED, border_style="cyan")
        table.add_column("Property", style="bold yellow")
        table.add_column("Value")

        table.add_row("📁 Path", str(self.state.path))
        table.add_row(
            "📦 Git Repository",
            "[green]Yes[/green]" if self.state.is_git_repo else "[red]No[/red]",
        )

        if self.state.is_git_repo:
            table.add_row(
                "📝 Has Commits",
                "[green]Yes[/green]" if self.state.has_commits else "[red]No[/red]",
            )
            if self.state.branch_name:
                table.add_row("🌿 Branch", self.state.branch_name)
            table.add_row(
                "📄 README",
                (
                    "[green]Exists[/green]"
                    if self.state.has_readme
                    else "[yellow]Missing[/yellow]"
                ),
            )
            table.add_row(
                "🚫 .gitignore",
                (
                    "[green]Exists[/green]"
                    if self.state.has_gitignore
                    else "[yellow]Missing[/yellow]"
                ),
            )
            table.add_row(
                "🌐 Remote",
                (
                    f"[green]{self.state.remote_url}[/green]"
                    if self.state.has_remote
                    else "[yellow]Not configured[/yellow]"
                ),
            )
            if self.state.untracked_files:
                table.add_row(
                    "📋 Untracked Files", str(len(self.state.untracked_files))
                )
            if self.state.modified_files:
                table.add_row("✏️  Modified Files", str(len(self.state.modified_files)))

        panel = Panel(
            table,
            title="[bold magenta]🎼 Git Maestro - Repository State[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
        )
        console.print(panel)

    def get_applicable_actions(self) -> List[Action]:
        """Get list of actions applicable to the current state."""
        return [action for action in self.actions if action.is_applicable(self.state)]

    def display_menu(self) -> bool:
        """Display the action menu and handle user input. Returns True if user wants to continue."""
        self.applicable_actions = self.get_applicable_actions()

        if not self.applicable_actions:
            console.print(
                "\n[bold green]✨ Everything looks good! No actions needed.[/bold green]\n"
            )
            return False

        # Group actions by category
        setup_actions = [a for a in self.applicable_actions if a.category == "setup"]
        info_actions = [a for a in self.applicable_actions if a.category == "info"]

        console.print("\n[bold cyan]Available Actions:[/bold cyan]\n")

        # Create menu table
        menu_table = Table(show_header=True, box=box.SIMPLE, border_style="blue")
        menu_table.add_column("#", style="bold cyan", width=4)
        menu_table.add_column("Action", style="bold")
        menu_table.add_column("Description", style="dim")

        current_idx = 1

        # Add setup actions first
        if setup_actions:
            menu_table.add_row(
                "", "[bold yellow]Setup[/bold yellow]", "", end_section=True
            )
            for action in setup_actions:
                menu_table.add_row(
                    str(current_idx), action.get_display_name(), action.description
                )
                current_idx += 1

        # Add info actions
        if info_actions:
            if setup_actions:
                menu_table.add_row("", "", "")  # Spacing row
            menu_table.add_row(
                "", "[bold yellow]Information[/bold yellow]", "", end_section=True
            )
            for action in info_actions:
                menu_table.add_row(
                    str(current_idx), action.get_display_name(), action.description
                )
                current_idx += 1

        menu_table.add_row("", "", "")  # Spacing row
        menu_table.add_row("0", "❌ Exit", "Exit git-maestro")

        console.print(menu_table)
        console.print()

        # Get user choice
        choices = [str(i) for i in range(len(self.applicable_actions) + 1)]
        completer = WordCompleter(choices)
        validator = NumberValidator(len(self.applicable_actions))

        try:
            choice = prompt(
                "Select an action (0 to exit): ",
                completer=completer,
                validator=validator,
            )

            choice_num = int(choice)

            if choice_num == 0:
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
                return False

            # Execute the chosen action
            selected_action = self.applicable_actions[choice_num - 1]
            console.print()
            success = selected_action.execute(self.state)

            if success:
                # Refresh state after successful action
                self.state.refresh()
                console.print()

            return True

        except (ValueError, IndexError):
            console.print("[bold red]Invalid choice. Please try again.[/bold red]")
            return True
        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
            return False
        except EOFError:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
            return False

    def run(self):
        """Run the interactive menu loop."""
        try:
            while True:
                console.clear()
                self.display_state()
                should_continue = self.display_menu()
                if not should_continue:
                    break

                console.print("\n[dim]Press Enter to continue...[/dim]")
                prompt("")

        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]\n")
