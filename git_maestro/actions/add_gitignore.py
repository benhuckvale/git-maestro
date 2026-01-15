"""Action to add a .gitignore file."""

from rich.console import Console
from .base import Action
from git_maestro.state import RepoState
from git_maestro.selection_helper import select_number_from_menu

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
            choice = select_number_from_menu(
                title="Gitignore Template",
                text="Select a template type:",
                options=[
                    "Python",
                    "Node.js",
                    "Generic",
                ],
                default_index=0,
            )

            if choice is None:
                console.print("[yellow]Cancelled, using Generic[/yellow]")
                template_key = "generic"
            elif choice == 1:
                template_key = "python"
            elif choice == 2:
                template_key = "node"
            elif choice == 3:
                template_key = "generic"
            else:
                template_key = "generic"
            gitignore_content = GITIGNORE_TEMPLATES[template_key]

            # Write .gitignore file
            gitignore_path = state.path / ".gitignore"
            gitignore_path.write_text(gitignore_content)

            console.print(
                f"[bold green]✓ .gitignore created with {template_key} template![/bold green]"
            )
            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error creating .gitignore: {e}[/bold red]")
            return False
