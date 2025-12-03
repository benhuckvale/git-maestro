"""Helper functions for generating repository descriptions."""

import re
import subprocess
from pathlib import Path
from typing import List, Optional
from rich.console import Console

console = Console()


def extract_descriptions_from_readme(repo_path: Path) -> List[str]:
    """
    Extract potential descriptions from README file.

    Looks for:
    1. First paragraph after the title
    2. Any line that looks like a description
    3. First sentence after title

    Returns a list of potential descriptions (max 3).
    """
    readme_files = ["README.md", "README.rst", "README.txt", "README"]
    descriptions = []

    for readme_name in readme_files:
        readme_path = repo_path / readme_name
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding='utf-8')
                descriptions = _parse_readme_content(content)
                if descriptions:
                    break
            except Exception:
                continue

    return descriptions[:3]  # Return max 3 suggestions


def _parse_readme_content(content: str) -> List[str]:
    """Parse README content to extract descriptions."""
    descriptions = []
    lines = content.split('\n')

    # Remove empty lines at the start
    while lines and not lines[0].strip():
        lines.pop(0)

    # Skip the title (first line with # or first non-empty line)
    if lines:
        lines.pop(0)

    # Method 1: Get first non-empty paragraph after title
    paragraph_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if paragraph_lines:
                break
        elif not stripped.startswith('#') and not stripped.startswith('```'):
            # Skip markdown headings and code blocks
            paragraph_lines.append(stripped)

    if paragraph_lines:
        paragraph = ' '.join(paragraph_lines)
        # Clean up markdown formatting
        paragraph = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', paragraph)  # Remove links
        paragraph = re.sub(r'[*_`]', '', paragraph)  # Remove bold/italic/code markers
        if len(paragraph) <= 300 and len(paragraph) > 10:
            descriptions.append(paragraph)

    # Method 2: Get first sentence
    if paragraph_lines:
        first_line = paragraph_lines[0]
        # Try to find first sentence
        match = re.match(r'^([^.!?]+[.!?])', first_line)
        if match:
            first_sentence = match.group(1).strip()
            first_sentence = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', first_sentence)
            first_sentence = re.sub(r'[*_`]', '', first_sentence)
            if len(first_sentence) <= 200 and len(first_sentence) > 10:
                if first_sentence not in descriptions:
                    descriptions.append(first_sentence)

    return descriptions


def generate_description_with_ai(repo_path: Path, repo_name: str) -> Optional[str]:
    """
    Generate a repository description using Claude CLI if available.

    Returns None if Claude CLI is not available or fails.
    """
    try:
        # Check if claude CLI is available
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True,
            timeout=2
        )
        if result.returncode != 0:
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None

    # Build a prompt for Claude
    readme_content = ""
    for readme_name in ["README.md", "README.rst", "README.txt", "README"]:
        readme_path = repo_path / readme_name
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding='utf-8')[:1000]  # First 1000 chars
                break
            except Exception:
                continue

    # Get list of files in repo
    try:
        files = [f.name for f in repo_path.iterdir() if f.is_file()][:20]
        files_list = ", ".join(files)
    except Exception:
        files_list = ""

    prompt = f"""Generate a concise one-sentence description (max 100 characters) for a GitHub repository named '{repo_name}'.

Files in the repo: {files_list}

README excerpt:
{readme_content}

Return ONLY the description text, nothing else."""

    try:
        # Call Claude CLI
        result = subprocess.run(
            ["claude", "--no-stream"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            description = result.stdout.strip()
            # Clean up any markdown or extra formatting
            description = re.sub(r'[*_`"]', '', description)
            description = description.strip()
            if len(description) <= 300 and len(description) > 10:
                return description
    except (subprocess.TimeoutExpired, Exception):
        pass

    return None


def get_description_options(repo_path: Path, repo_name: str, use_ai: bool = True) -> List[tuple[str, str]]:
    """
    Get description options for a repository.

    Returns a list of (label, description) tuples.
    """
    options = []

    # Extract from README
    readme_descriptions = extract_descriptions_from_readme(repo_path)
    for i, desc in enumerate(readme_descriptions, 1):
        if i == 1:
            options.append(("From README (first paragraph)", desc))
        elif i == 2:
            options.append(("From README (first sentence)", desc))
        else:
            options.append((f"From README (option {i})", desc))

    # Try AI generation if enabled
    if use_ai:
        console.print("[dim]Generating AI description...[/dim]", end="\r")
        ai_desc = generate_description_with_ai(repo_path, repo_name)
        console.print(" " * 50, end="\r")  # Clear the line
        if ai_desc:
            options.append(("AI-generated (Claude)", ai_desc))

    return options
