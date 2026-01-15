"""Action to add a README.md file."""

from rich.console import Console

from .base import Action
from git_maestro.state import RepoState
from git_maestro.selection_helper import prompt_text

console = Console()


class AddReadmeAction(Action):
    """Add a README.md file to the repository."""

    def __init__(self):
        super().__init__()
        self.name = "Add README.md"
        self.description = "Create a README.md file with basic project information"
        self.emoji = "📝"

    def is_applicable(self, state: RepoState) -> bool:
        """This action is applicable if the directory is a git repo without a README."""
        return state.is_git_repo and not state.has_readme

    def execute(self, state: RepoState) -> bool:
        """Create a README.md file."""
        try:
            console.print("[bold cyan]Creating README.md...[/bold cyan]")

            # Get project name from directory
            project_name = state.path.name

            # Ask for project description
            console.print(
                "\n[yellow]Enter a brief description for your project (or press Enter to skip):[/yellow]"
            )
            description = prompt_text("Description:", default="") or ""

            # Create README content
            readme_content = f"# {project_name}\n\n"
            if description:
                readme_content += f"{description}\n\n"
            readme_content += (
                "## Installation\n\nTODO: Add installation instructions\n\n"
            )
            readme_content += "## Usage\n\nTODO: Add usage instructions\n\n"
            readme_content += "## License\n\nTODO: Add license information\n"

            # Write README file
            readme_path = state.path / "README.md"
            readme_path.write_text(readme_content)

            console.print("[bold green]✓ README.md created successfully![/bold green]")
            return True

        except Exception as e:
            console.print(f"[bold red]✗ Error creating README.md: {e}[/bold red]")
            return False
