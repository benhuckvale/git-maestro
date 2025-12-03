"""Main CLI entry point for git-maestro."""

import sys
from pathlib import Path
from rich.console import Console

from .state import RepoState
from .menu import Menu
from .actions import (
    InitRepoAction,
    InitialCommitAction,
    AddReadmeAction,
    AddGitignoreAction,
    SetupRemoteAction,
    CreateRemoteRepoAction,
)

console = Console()


def get_all_actions():
    """Get all available actions."""
    return [
        InitRepoAction(),
        InitialCommitAction(),
        AddReadmeAction(),
        AddGitignoreAction(),
        SetupRemoteAction(),
        CreateRemoteRepoAction(),
    ]


def main():
    """Main entry point for the CLI."""
    try:
        # Get the current working directory
        path = Path.cwd()

        # Check if a path was provided as argument
        if len(sys.argv) > 1:
            path = Path(sys.argv[1]).resolve()
            if not path.exists():
                console.print(f"[bold red]Error: Path '{path}' does not exist.[/bold red]")
                sys.exit(1)
            if not path.is_dir():
                console.print(f"[bold red]Error: '{path}' is not a directory.[/bold red]")
                sys.exit(1)

        # Detect repository state
        state = RepoState(path)

        # Get all actions
        actions = get_all_actions()

        # Create and run menu
        menu = Menu(state, actions)
        menu.run()

    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
