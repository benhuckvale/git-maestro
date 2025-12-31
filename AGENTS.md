# AGENTS.md - Quick Start Guide for AI Assistants

This file helps AI assistants (like Claude) quickly understand the git-maestro codebase without having to explore from scratch.

## What is Git Maestro?

Git Maestro is an interactive CLI tool that helps users manage git repositories through context-aware menus. It observes the current repository state and presents only relevant actions to progress the project setup (init, README, .gitignore, remote setup, CI/CD monitoring, etc.).

## Architecture Overview

### Core Components

1. **State Detection** (`git_maestro/state.py`)
   - `RepoState` class detects current git repo state
   - Properties: `is_git_repo`, `has_commits`, `has_remote`, `branch_name`, etc.
   - Uses GitPython to introspect repository
   - Facts dictionary for caching expensive operations

2. **Action System** (`git_maestro/actions/`)
   - Base class: `Action` in `base.py`
   - Each action has:
     - `name`, `description`, `emoji` attributes
     - `is_applicable(state)` - determines if action should be shown
     - `execute(state)` - performs the action
   - Actions are registered in `cli.py::get_all_actions()`

3. **CLI** (`git_maestro/cli.py`)
   - Entry point: `main()` function
   - Creates `RepoState`, displays context, shows menu
   - Can be called as `git-maestro` or `git maestro` (git plugin)
   - MCP server mode: `git-maestro mcp`

4. **Menu System** (`git_maestro/menu.py`)
   - Interactive menu using `prompt_toolkit`
   - Shows applicable actions based on state
   - Handles user selection and execution

5. **MCP Server** (`git_maestro/mcp_server.py`)
   - Model Context Protocol server for AI integration
   - Provides tools to monitor GitHub Actions and Azure Pipelines
   - Enables closed-loop CI/CD workflows

## Directory Structure

```
git-maestro/
├── git_maestro/
│   ├── cli.py              # Entry point, registers all actions
│   ├── state.py            # Repository state detection
│   ├── menu.py             # Interactive menu system
│   ├── mcp_server.py       # MCP server for AI integration
│   └── actions/
│       ├── base.py         # Abstract Action base class
│       ├── init_repo.py    # Initialize git repository
│       ├── initial_commit.py # Create initial commit
│       ├── add_readme.py   # Add README.md
│       ├── add_gitignore.py # Add .gitignore
│       ├── setup_remote.py # Setup GitHub/GitLab remote
│       ├── create_remote_repo.py # Create remote repo if missing
│       ├── setup_azure_devops.py # Setup Azure DevOps
│       ├── fetch_github_actions.py # Fetch GitHub Actions runs
│       ├── fetch_azure_pipelines.py # Fetch Azure Pipelines
│       └── ... (other actions)
├── tests/                  # Pytest test suite (28+ tests)
├── pyproject.toml          # PDM project configuration
└── README.md               # User documentation
```

## How to Add a New Action

1. Create `git_maestro/actions/your_action.py`
2. Inherit from `Action` base class
3. Implement `is_applicable(state)` and `execute(state)`
4. Add to `git_maestro/actions/__init__.py` exports
5. Register in `cli.py::get_all_actions()`

Example:
```python
from .base import Action
from git_maestro.state import RepoState

class YourAction(Action):
    def __init__(self):
        super().__init__()
        self.name = "Your Action Name"
        self.description = "What it does"
        self.emoji = "🎯"

    def is_applicable(self, state: RepoState) -> bool:
        return state.is_git_repo  # Show only in git repos

    def execute(self, state: RepoState) -> bool:
        # Do stuff
        return True  # True = success
```

## Common Patterns

### Interactive Prompts
Uses `prompt_toolkit` for user input:
```python
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

completer = WordCompleter(["option1", "option2"])
choice = prompt("Choose: ", completer=completer, default="option1")
```

### Rich Console Output
Uses `rich` library for beautiful terminal output:
```python
from rich.console import Console
console = Console()

console.print("[cyan]Info message[/cyan]")
console.print("[yellow]Warning message[/yellow]")
console.print("[bold green]✓ Success![/bold green]")
console.print("[bold red]✗ Error![/bold red]")
```

### GitPython Usage
Common operations with GitPython:
```python
# Push to remote
origin = state.repo.remote("origin")
branch = state.repo.active_branch.name
origin.push(refspec=f"{branch}:{branch}", set_upstream=True)

# List branches
branches = [str(b) for b in state.repo.branches]

# Iterate commits
commits = list(state.repo.iter_commits(max_count=10))
```

### Configuration Storage
- Tokens stored in `~/.config/git-maestro/tokens.conf`
- Format: `github=ghp_xxx` or `gitlab=glpat_xxx`
- Action-specific data in `.git-maestro/` directory

## Key Files for Common Tasks

### Modifying Push Behavior
- `git_maestro/actions/setup_remote.py` - Push after creating GitHub/GitLab repo
- `git_maestro/actions/create_remote_repo.py` - Push when remote exists but repo missing
- `git_maestro/actions/initial_commit.py` - Push after initial commit
- `git_maestro/actions/setup_azure_devops.py` - Push after Azure setup
- **NEW**: `git_maestro/push_helper.py` - Shared push logic with selective options

### GitHub Integration
- `git_maestro/actions/setup_remote.py` - Create GitHub repos via API
- `git_maestro/actions/fetch_github_actions.py` - Fetch workflow runs
- Uses PyGithub library for GitHub API access

### GitLab Integration
- `git_maestro/actions/setup_remote.py` - Create GitLab projects via API
- Uses `python-gitlab` library

### Azure DevOps Integration
- `git_maestro/actions/setup_azure_devops.py` - Setup Azure repos
- `git_maestro/actions/fetch_azure_pipelines.py` - Fetch pipeline runs
- Uses `azure-devops` library

## Testing

```bash
# Run all tests
pdm run pytest

# Run with coverage
pdm run pytest --cov=git_maestro

# Run specific test file
pdm run pytest tests/test_state.py -v
```

Tests use mocks for git operations and API calls - no real tokens required.

## Recent Changes

### Selective Push Feature (2025-12-30)
Added granular control over what gets pushed when creating remote repositories:
- New interactive menu with 4 options:
  1. Push current branch (default, maintains backward compatibility)
  2. Push a specific branch
  3. Push specific commit from branch history (e.g., first commit only)
  4. Skip - don't push now
- Created shared `push_helper.py` module used by all push-related actions
- Files modified:
  - `git_maestro/push_helper.py` - Core implementation
  - `git_maestro/actions/setup_remote.py`
  - `git_maestro/actions/create_remote_repo.py`
  - `git_maestro/actions/initial_commit.py`
  - `git_maestro/actions/setup_azure_devops.py`

### MCP Server Integration
Git Maestro now runs as an MCP stdio server, enabling AI assistants to:
- Monitor GitHub Actions and Azure Pipelines
- Create closed-loop CI/CD workflows (push → monitor → fix → repeat)
- Poll job status without downloading full logs

## Dependencies

Core libraries:
- `gitpython` - Git repository introspection
- `rich` - Terminal formatting
- `prompt_toolkit` - Interactive prompts and menus
- `PyGithub` - GitHub API
- `python-gitlab` - GitLab API
- `azure-devops` - Azure DevOps API

## Development Setup

```bash
# Install with dev dependencies
pdm install -d

# Run in development mode
pdm run git-maestro

# Format code
pdm run black .

# Lint
pdm run ruff check .
```

## Troubleshooting

### Token Issues
- GitHub token: `~/.config/git-maestro/tokens.conf` should have `github=ghp_xxx`
- GitLab token: `gitlab=glpat_xxx`
- Azure token: `azure=xxx`

### SSH Configuration
- Git Maestro checks for SSH keys in `~/.ssh/id_rsa` and `~/.ssh/id_ed25519`
- Used when creating remote repositories with SSH URLs

### State Detection Issues
- State is re-detected after each action execution
- If state seems wrong, check `RepoState._detect_state()` in `state.py`

## Quick Reference for Common Operations

### Finding Where Actions Are Registered
Look in `cli.py::get_all_actions()` - this is the single source of truth.

### Finding Push Logic
Previously scattered across multiple files, now centralized in `push_helper.py`.

### Understanding Action Applicability
Each action's `is_applicable()` method determines when it shows up. Check the specific action file to understand the conditions.

### Extending MCP Server
Add new tool methods in `mcp_server.py` and register them in the `@server.list_tools()` handler.

---

**Last Updated**: 2025-12-30
**For**: AI assistants working with git-maestro codebase
