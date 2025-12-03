# 🎼 Git Maestro

A slick CLI tool to manage and progress git repositories with interactive menus.

Git Maestro observes the current state of your git repository and presents you with context-aware actions to help you quickly set up and manage your projects. No more typing countless git commands - just select from a beautiful menu and let Git Maestro handle the rest!

## Features

- 🎯 **Context-Aware Actions**: Only shows actions that are relevant to your current repository state
- 🎨 **Beautiful CLI Interface**: Built with Rich and Prompt Toolkit for a polished user experience
- 🔧 **Modular Design**: Easy to extend with new actions
- ⚡ **Fast Setup**: Quickly initialize repos, add READMEs, .gitignore files, and remote repositories
- 🎭 **Works as Git Plugin**: Can be called as `git maestro` after installation

## Installation

### Using PDM (Recommended for Development)

```bash
# Clone the repository
git clone <your-repo-url>
cd git-maestro

# Install dependencies
pdm install

# Run in development mode
pdm run git-maestro
```

### Global Installation

```bash
# Install globally using pdm
pdm install -G

# Or install in editable mode for development
pip install -e .
```

After installation, you can run `git-maestro` from anywhere, or use it as a git plugin with `git maestro`.

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

## Current Actions

- **Initialize Git Repository** 🎬: Run `git init` in a non-git directory
- **Add README.md** 📝: Create a README with basic project structure
- **Add .gitignore** 🚫: Add a .gitignore file with templates for Python, Node.js, or Generic projects
- **Setup Remote Repository** 🌐: Configure GitHub or GitLab as your remote origin

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
