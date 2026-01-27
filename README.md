<p align="center">
  <img src="docs/assets/banner.png" alt="Git Maestro" width="600">
</p>

# 🎼 Git Maestro

[![PyPI version](https://badge.fury.io/py/git-maestro.svg)](https://badge.fury.io/py/git-maestro)
[![Documentation](https://img.shields.io/badge/docs-github.io-blue)](https://benhuckvale.github.io/git-maestro/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A convenient TUI for managing git repositories with interactive menus.

📚 **[Read the full documentation](https://benhuckvale.github.io/git-maestro/)**

Git Maestro observes the current state of your git repository, both local and remote, and presents you with context-aware actions to help you quickly set up and manage your projects. No more typing countless git commands and switching in and out of the browser - just select from a beautiful menu and let Git Maestro handle the rest!

## Features

- 🎯 **Context-Aware Actions**: Only shows actions that are relevant to your current repository state
- 🎨 **Beautiful CLI Interface**: Built with Rich and Prompt Toolkit for a polished user experience
- 🔧 **Modular Design**: Easy to extend with new actions
- ⚡ **Fast Setup**: Quickly initialize repos, add READMEs, .gitignore files, and remote repositories
- 🎭 **Works as Git Plugin**: Can be called as `git maestro` after installation
- 🔌 **MCP Integration**: Seamlessly works with Model Context Protocol for AI-powered workflows

## Installation

### From PyPI (Recommended)

```bash
pip install git-maestro
```

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/benhuckvale/git-maestro.git
cd git-maestro

# Install with PDM
pdm install

# Run in development mode
pdm run git-maestro
```

After installation, you can run `git-maestro` from anywhere, or use it as a git plugin with `git maestro`.

📖 **[Installation Guide](https://benhuckvale.github.io/git-maestro/installation/)**

## Usage

Simply navigate to any directory and run:

```bash
git-maestro
```

Or use it as a git plugin:

```bash
git maestro
```

Git Maestro will:
1. Detect the current state of the directory
2. Show you what's configured and what's missing
3. Present a menu of applicable actions
4. Execute your selected action
5. Refresh and show updated options

📖 **[Quick Start Guide](https://benhuckvale.github.io/git-maestro/quickstart/)**

## Current Actions

- **Initialize Git Repository** 🎬: Run `git init` in a non-git directory
- **Add README.md** 📝: Create a README with basic project structure
- **Add .gitignore** 🚫: Add a .gitignore file with templates for Python, Node.js, or Generic projects
- **Setup Remote Repository** 🌐: Configure GitHub or GitLab as your remote origin

### MCP Server for AI Assistants

Git Maestro runs as a **Model Context Protocol (MCP) stdio server**, enabling AI assistants (like Claude) to access git and GitHub Actions data **outside their sandboxes**.

#### What This Enables

AI assistants can now autonomously:
- **Monitor CI/CD**: Check GitHub Actions job status without downloading full logs
- **Debug Failures**: Fetch job logs and analyze test failures
- **Create Closed Loops**: Make code fixes, push commits, and monitor new CI runs until tests pass
- **Understand Pipeline Complexity**: See job dependencies and understand which failures are root causes vs cascading

#### Example Workflow

```bash
# Start the MCP server
git-maestro mcp
```

An AI assistant can then:
1. Make code changes and push them
2. Poll `check_github_actions_job_status()` to wait for CI to complete
3. Fetch failing job logs with `download_github_actions_job_logs()`
4. Analyze failures and make targeted fixes
5. Loop until all tests pass—without any human intervention

#### Available MCP Tools

- `list_github_actions_runs(count)` - Get recent workflow runs
- `get_github_actions_run_jobs(run_id)` - View job structure and details
- `check_github_actions_job_status(run_id, [job_id])` - Lightweight polling (fast status checks)
- `download_github_actions_job_logs(run_id, job_id)` - Fetch logs for specific jobs
- `download_job_traces()` - Download all failed job logs from the latest run

#### Configuration

Add to your Claude Code `mcp.json`:

```json
{
  "mcpServers": {
    "git-maestro": {
      "command": "git-maestro",
      "args": ["mcp"]
    }
  }
}
```

Then use `git-maestro mcp` in your Claude session to enable these tools.

📖 **[Full MCP Documentation](https://benhuckvale.github.io/git-maestro/github-api/#mcp-tools-for-github-actions)**

## Requirements

- Python >= 3.9
- Git installed on your system
- Dependencies (automatically installed):
  - rich >= 13.7.0
  - prompt-toolkit >= 3.0.43
  - gitpython >= 3.1.40

## Development

```bash
# Install with dev dependencies
pdm install -d

# Run tests
pdm run pytest

# Run tests with verbose output
pdm run pytest -v

# Run tests with coverage
pdm run pytest --cov=git_maestro

# Format code
pdm run black .

# Lint
pdm run ruff check .
```

### Test Suite

Git Maestro has a comprehensive test suite with 28+ tests covering:
- Repository state detection
- SSH configuration detection
- Action applicability logic
- CLI functionality

See [tests/README.md](tests/README.md) for more details.

### Security Note

Git Maestro stores tokens in `~/.config/git-maestro/tokens.conf` (outside the repository). The `.gitignore` file blocks common sensitive patterns (`*.token`, `.env`, `credentials.json`, etc.). Unit tests use mocks and don't require real tokens.

## Extending Git Maestro

To add a new action:

1. Create a new file in `git_maestro/actions/` (e.g., `your_action.py`)
2. Inherit from the `Action` base class
3. Implement `is_applicable()` and `execute()` methods
4. Add your action to `git_maestro/actions/__init__.py`
5. Register it in `git_maestro/cli.py` in the `get_all_actions()` function

Example:

```python
from .base import Action
from git_maestro.state import RepoState

class YourAction(Action):
    def __init__(self):
        super().__init__()
        self.name = "Your Action Name"
        self.description = "What your action does"
        self.emoji = "🎯"

    def is_applicable(self, state: RepoState) -> bool:
        # Return True if this action should be shown
        return state.is_git_repo

    def execute(self, state: RepoState) -> bool:
        # Perform your action
        # Return True if successful
        return True
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Integrations

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/github-lockup-white.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/assets/github-lockup.svg">
  <img src="docs/assets/github-lockup.svg" alt="Works with GitHub" height="24" style="vertical-align: middle;">
</picture>

Works with GitHub.
