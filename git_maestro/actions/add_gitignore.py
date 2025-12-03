"""Action to add a .gitignore file."""

from pathlib import Path
from rich.console import Console
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from .base import Action
from git_maestro.state import RepoState

console = Console()


GITIGNORE_TEMPLATES = {
    "python": """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# PDM
__pypackages__/
.pdm.toml
.pdm-python

# OS
.DS_Store
Thumbs.db
""",
    "node": """# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production
build/
dist/

# Environment variables
.env
.env.local
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
coverage/
.nyc_output/
""",
    "generic": """# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
""",
}


class AddGitignoreAction(Action):
    """Add a .gitignore file to the repository."""

    def __init__(self):
        super().__init__()
        self.name = "Add .gitignore"
        self.description = "Create a .gitignore file with common ignore patterns"
        self.emoji = "🚫"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the directory is a git repo without a .gitignore."""
        return state.is_git_repo and not state.has_gitignore

    def execute(self, state: RepoState) -> bool:
        """Create a .gitignore file."""
        try:
            console.print("[bold cyan]Creating .gitignore...[/bold cyan]")

            # Ask for template type
            console.print("\n[yellow]Select a template type:[/yellow]")
            console.print("1. Python")
            console.print("2. Node.js")
            console.print("3. Generic")

            template_completer = WordCompleter(["1", "2", "3", "python", "node", "generic"])
            choice = prompt("Choice (1-3): ", completer=template_completer, default="1")

            # Map choice to template
            template_map = {
                "1": "python",
                "2": "node",
                "3": "generic",
                "python": "python",
                "node": "node",
                "generic": "generic",
            }

            template_key = template_map.get(choice.lower(), "generic")
            gitignore_content = GITIGNORE_TEMPLATES[template_key]

            # Write .gitignore file
            gitignore_path = state.path / ".gitignore"
            gitignore_path.write_text(gitignore_content)

            console.print(f"[bold green]✓ .gitignore created with {template_key} template![/bold green]")
            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error creating .gitignore: {e}[/bold red]")
            return False
