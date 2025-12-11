"""Main CLI entry point for git-maestro."""

import sys
from pathlib import Path
from rich.console import Console

from .state import RepoState
from .menu import Menu
from .mcp_server import MCPServer
from .actions import (
    InitRepoAction,
    InitialCommitAction,
    AddReadmeAction,
    AddGitignoreAction,
    SetupRemoteAction,
    CreateRemoteRepoAction,
    FetchGithubActionsAction,
    RefreshGithubActionsAction,
    ViewFailedJobsAction,
    DownloadJobTracesAction,
)

console = Console()


def get_all_actions():
    """Get all available actions."""
    return [
        # Setup actions
        InitRepoAction(),
        InitialCommitAction(),
        AddReadmeAction(),
        AddGitignoreAction(),
        SetupRemoteAction(),
        CreateRemoteRepoAction(),
        # Info actions
        FetchGithubActionsAction(),
        RefreshGithubActionsAction(),
        ViewFailedJobsAction(),
        DownloadJobTracesAction(),
    ]


def show_help():
    """Show help message."""
    console.print("""[bold cyan]git-maestro[/bold cyan] - A slick CLI tool to manage git repositories

[bold]Usage:[/bold]
  git-maestro [PATH]          Start interactive menu for PATH (default: current directory)
  git-maestro mcp             Start MCP (Model Context Protocol) stdio server
  git-maestro -h, --help      Show this help message
  git-maestro mcp -h          Show MCP server help

[bold]Commands:[/bold]
  mcp                         Run as MCP stdio server for AI assistants
""")


def main_interactive(path: Path):
    """Run the interactive CLI menu."""
    # Detect repository state
    state = RepoState(path)

    # Get all actions
    actions = get_all_actions()

    # Create and run menu
    menu = Menu(state, actions)
    menu.run()


def main_mcp():
    """Run the MCP server."""
    server = MCPServer()
    server.handle_message()


def main():
    """Main entry point for the CLI."""
    try:
        # Parse arguments
        if len(sys.argv) > 1:
            first_arg = sys.argv[1]

            # Check for help
            if first_arg in ("-h", "--help"):
                show_help()
                sys.exit(0)

            # Check for mcp subcommand
            if first_arg == "mcp":
                # Check for help on mcp subcommand
                if len(sys.argv) > 2 and sys.argv[2] in ("-h", "--help"):
                    console.print("""[bold cyan]git-maestro mcp[/bold cyan] - MCP stdio server for AI assistants

[bold]Usage:[/bold]
  git-maestro mcp             Start the MCP server
  git-maestro mcp -h          Show this help message

[bold]Description:[/bold]
  Runs git-maestro as a Model Context Protocol stdio server, allowing AI assistants
  to use git-maestro tools like downloading GitHub Actions job traces.

[bold]Configuration:[/bold]
  Add to your mcp.json configuration file:

  {
    "mcpServers": {
      "git-maestro": {
        "command": "git-maestro",
        "args": ["mcp"]
      }
    }
  }
""")
                    sys.exit(0)
                main_mcp()
                return

            # Otherwise treat as path argument
            path = Path(first_arg).resolve()
            if not path.exists():
                console.print(
                    f"[bold red]Error: Path '{path}' does not exist.[/bold red]"
                )
                sys.exit(1)
            if not path.is_dir():
                console.print(
                    f"[bold red]Error: '{path}' is not a directory.[/bold red]"
                )
                sys.exit(1)
        else:
            # No arguments - use current directory
            path = Path.cwd()

        # Run interactive menu
        main_interactive(path)

    except KeyboardInterrupt:
        console.print("\n[bold yellow]👋 Goodbye![/bold yellow]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Fatal error: {e}[/bold red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
