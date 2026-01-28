"""Menu system for git-maestro using rich and inline prompts."""

from typing import List, Tuple

from questionary import Choice
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .state import RepoState
from .actions.base import Action
from .selection_helper import select_number_from_menu
from .version import get_version_string


console = Console()

# Badger mascot with baton and bow-tie
BADGER_ART = r"""
    |  ^_ _^
    |  | \ |\
    |  \ o\|o|
    |   \_ \ |
    "     \_\|
    O     >o<
""".strip('\n')

TITLE_ART = r"""
  ▄▀  █ ▀█▀   █▀▄▀█ ▄▀▄ ██▀ ▄▀▀ ▀█▀ █▀▄ █▀█
  ▀▄█ █  █    █ ▀ █ █▀█ █▄▄ ▄█▀  █  █▀▄ █▄█
""".strip('\n')


def display_banner():
    """Display the Git Maestro startup banner."""
    version = get_version_string()
    version_str = f"v{version}" if not version.startswith("v") else version

    badger_lines = BADGER_ART.split('\n')
    title_lines = TITLE_ART.split('\n')

    # Combine badger and title side by side
    banner_lines = []
    max_badger_width = max(len(line) for line in badger_lines)
    title_width = 42

    for i in range(max(len(badger_lines), len(title_lines))):
        badger_part = badger_lines[i] if i < len(badger_lines) else ""
        title_part = title_lines[i] if i < len(title_lines) else ""
        padded_badger = badger_part.ljust(max_badger_width)

        # Put version on the right side of line 4 (bow-tie area)
        if i == 4:
            right_part = f"{title_part:<{title_width - len(version_str)}}{version_str}"
        else:
            right_part = title_part

        banner_lines.append(f"  {padded_badger}    {right_part}")

    banner_text = '\n'.join(banner_lines)

    console.print(Panel(
        f"[cyan]{banner_text}[/cyan]",
        border_style="magenta",
        padding=(0, 1),
    ))


class Menu:
    """Interactive menu for git-maestro."""

    def __init__(self, state: RepoState, actions: List[Action]):
        self.state = state
        self.actions = actions
        self.applicable_actions: List[Action] = []

    def display_state(self):
        """Display the current repository state."""
        table = Table(show_header=False, box=box.ROUNDED, border_style="cyan", expand=True)
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
                table.add_row(":fountain_pen:  Modified Files", str(len(self.state.modified_files)))

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

    def display_menu(self) -> Tuple[bool, bool]:
        """
        Display the action menu and handle user input.

        Returns:
            Tuple[bool, bool]: (should_continue, show_state_next)
        """
        applicable_actions = self.get_applicable_actions()

        if not applicable_actions:
            console.print(
                "\n[bold green]✨ Everything looks good! No actions needed.[/bold green]\n"
            )
            return False, True

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
        console.print(
            "[dim]Use arrow keys to pick next action. Press 's' to show the repository state. Esc exits.[/dim]\n"
        )

        show_state_choice = Choice(
            title="👀 Show repository state (press s)",
            value="show_state",
            shortcut_key="s",
        )
        extra_choices = [show_state_choice]

        instruction = (
            "Press enter to confirm, 's' to show the repository state, or esc to cancel"
        )

        while True:
            try:
                choice_num = select_number_from_menu(
                    title="Git Maestro",
                    text="Select an action:",
                    options=options,
                    default_index=None,
                    show_numbers=True,
                    extra_choices=extra_choices,
                    enable_shortcuts=True,
                    instruction=instruction,
                    instant_values=["show_state"],
                )
            except KeyboardInterrupt:
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
                return False, True
            except EOFError:
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
                return False, True

            if choice_num == "show_state":
                console.print()
                self.display_state()
                continue

            if choice_num is None or choice_num == len(options):
                # User cancelled or selected Exit
                console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
                return False, True

            # Execute the chosen action
            selected_action = self.applicable_actions[choice_num - 1]
            console.print()
            success = selected_action.execute(self.state)

            if success:
                # Refresh state after successful action
                self.state.refresh()
                console.print()

            return True, selected_action.modifies_state()

    def run(self):
        """Run the interactive menu loop."""
        try:
            # Show banner on startup
            display_banner()

            iteration = 0
            show_state_next = True
            while True:
                console.print()
                if iteration:
                    console.rule("[dim]Next actions[/dim]")

                if show_state_next:
                    self.display_state()
                else:
                    console.print(
                        "[dim]Press 's' in the menu if you want to see the repository state again.[/dim]\n"
                    )

                should_continue, show_state_next = self.display_menu()
                if not should_continue:
                    break

                iteration += 1
        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]\n")
