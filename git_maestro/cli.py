"""Main CLI entry point for git-maestro."""

import sys
import subprocess
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
    GetGithubActionsLogsAction,
    SetupAzureDevOpsAction,
    ConfigureAzureTokenAction,
    FetchAzurePipelinesAction,
    GetAzurePipelinesAction,
    DownloadAzureStageLogsAction,
)

console = Console()


def get_git_info() -> tuple[str, str, bool]:
    """Get git commit hash, describe output, and dirty status for this package.

    Returns:
        Tuple of (commit_hash, git_describe, is_dirty) or ("", "", False) if not a git repo
    """
    try:
        # Get the directory where git_maestro is installed
        package_dir = Path(__file__).parent.parent

        # Get commit hash
        commit = subprocess.check_output(
            ["git", "-C", str(package_dir), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        # Get git describe (tag-based version)
        describe = subprocess.check_output(
            ["git", "-C", str(package_dir), "describe", "--tags", "--always"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        # Check if working directory is dirty
        status = subprocess.check_output(
            ["git", "-C", str(package_dir), "status", "--porcelain"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        is_dirty = bool(status)

        return commit, describe, is_dirty
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "", "", False


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
        SetupAzureDevOpsAction(),
        ConfigureAzureTokenAction(),
        # Info actions
        FetchGithubActionsAction(),
        FetchAzurePipelinesAction(),
        RefreshGithubActionsAction(),
        ViewFailedJobsAction(),
        DownloadJobTracesAction(),
        DownloadAzureStageLogsAction(),
        GetGithubActionsLogsAction(),
        GetAzurePipelinesAction(),
    ]


def show_help():
    """Show help message."""
    console.print(
        """[bold cyan]git-maestro[/bold cyan] - A convenient TUI for managing git repositories

[bold]Usage:[/bold]
  git-maestro [PATH]          Start interactive menu for PATH (default: current directory)
  git-maestro mcp             Start MCP (Model Context Protocol) stdio server
  git-maestro -h, --help      Show this help message
  git-maestro --version       Show version information
  git-maestro mcp -h          Show MCP server help

[bold]Commands:[/bold]
  mcp                         Run as MCP stdio server for AI assistants
"""
    )


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

            # Check for version
            if first_arg == "--version":
                commit, describe, is_dirty = get_git_info()
                version_info = "git-maestro 0.1.0"
                if commit:
                    dirty_indicator = "-dirty" if is_dirty else ""
                    version_info += f" ({describe}{dirty_indicator} @ {commit})"
                console.print(version_info)
                sys.exit(0)

            # Check for mcp subcommand
            if first_arg == "mcp":
                # Check for help on mcp subcommand
                if len(sys.argv) > 2 and sys.argv[2] in ("-h", "--help"):
                    console.print(
                        """[bold cyan]git-maestro mcp[/bold cyan] - MCP stdio server for AI assistants

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
"""
                    )
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
