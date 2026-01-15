"""Menu system for git-maestro using rich and inline prompts."""

from typing import List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .state import RepoState
from .actions.base import Action
from .selection_helper import select_number_from_menu


console = Console()


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
        applicable_actions = self.get_applicable_actions()

        if not applicable_actions:
            console.print(
                "\n[bold green]✨ Everything looks good! No actions needed.[/bold green]\n"
            )
            return False

        # Group actions by category so we can surface the category in the prompt text
        setup_actions = [a for a in applicable_actions if a.category == "setup"]
        info_actions = [a for a in applicable_actions if a.category == "info"]
        other_actions = [
            a for a in applicable_actions if a.category not in {"setup", "info"}
        ]

        sections: List[tuple[str, List[Action]]] = []
        if setup_actions:
            sections.append(("Setup", setup_actions))
        if info_actions:
            sections.append(("Gather Facts", info_actions))
        if other_actions:
            sections.append(("Other", other_actions))

        ordered_actions: List[Action] = []
        options: List[str] = []

        for section_name, actions in sections:
            for action in actions:
                label = f"{action.get_display_name()} - {action.description}"
                if section_name:
                    label = f"[{section_name}] {label}"
                options.append(label)
                ordered_actions.append(action)

        options.append("❌ Exit")
        self.applicable_actions = ordered_actions

        console.print("\n[bold cyan]Available Actions[/bold cyan]")
        console.print("[dim]Use arrow keys to pick next action. Esc exits.[/dim]\n")

        # Get user choice with radiolist
        try:
            choice_num = select_number_from_menu(
                title="Git Maestro",
                text="Select an action:",
                options=options,
                default_index=None,
                show_numbers=True,
            )

            if choice_num is None or choice_num == len(options):
                # User cancelled or selected Exit
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

        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
            return False
        except EOFError:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
            return False

    def run(self):
        """Run the interactive menu loop."""
        try:
            iteration = 0
            while True:
                if iteration:
                    console.print()
                    console.rule("[dim]Next actions[/dim]")
                else:
                    console.print()

                self.display_state()
                should_continue = self.display_menu()
                if not should_continue:
                    break

                iteration += 1
        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]\n")
