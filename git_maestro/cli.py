"""Main CLI entry point for git-maestro."""

import sys
from pathlib import Path
from rich.console import Console

from .state import RepoState
from .menu import Menu
from .version import get_git_info
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


def main_mcp(platforms: set[str] | None = None):
    """Run the MCP server.

    Args:
        platforms: Set of platforms to enable (github, azure, gitlab).
                   If None, all platforms are enabled.
    """
    from .mcp_server import main as mcp_main

    mcp_main(platforms=platforms)


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
  git-maestro mcp [OPTIONS]    Start the MCP server
  git-maestro mcp -h           Show this help message

[bold]Options:[/bold]
  --github    Enable GitHub Actions tools
  --azure     Enable Azure DevOps Pipelines tools
  --gitlab    Enable GitLab CI/CD tools

  If no platform flags specified, all platforms are enabled.

[bold]Examples:[/bold]
  git-maestro mcp                    Enable all platforms
  git-maestro mcp --github           Enable only GitHub tools
  git-maestro mcp --github --azure   Enable GitHub and Azure tools

[bold]Description:[/bold]
  Runs git-maestro as a Model Context Protocol stdio server, allowing AI assistants
  to use git-maestro tools like downloading GitHub Actions job traces.

  Specifying only the platforms you use reduces the number of tools exposed,
  which saves context window tokens when used with AI assistants.

[bold]Configuration:[/bold]
  Add to your mcp.json configuration file:

  {
    "mcpServers": {
      "git-maestro": {
        "command": "git-maestro",
        "args": ["mcp", "--github"]
      }
    }
  }
"""
                    )
                    sys.exit(0)

                # Parse platform flags
                platforms = set()
                valid_flags = {"--github", "--azure", "--gitlab"}
                for arg in sys.argv[2:]:
                    if arg in valid_flags:
                        platforms.add(arg[2:])  # Strip --
                    else:
                        console.print(
                            f"[bold red]Error: Unknown option: {arg}[/bold red]"
                        )
                        console.print(
                            f"[dim]Valid options: {', '.join(sorted(valid_flags))}[/dim]"
                        )
                        sys.exit(1)

                # None means all platforms
                main_mcp(platforms=platforms if platforms else None)
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
