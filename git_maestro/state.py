"""State detection module for git repositories."""

from pathlib import Path
from typing import Optional
import git
from git.exc import InvalidGitRepositoryError


class RepoState:
    """Represents the current state of a directory/git repository."""

    def __init__(self, path: str = "."):
        self.path = Path(path).resolve()
        self.is_git_repo = False
        self.repo: Optional[git.Repo] = None
        self.has_commits = False
        self.has_readme = False
        self.has_gitignore = False
        self.has_remote = False
        self.remote_url: Optional[str] = None
        self.branch_name: Optional[str] = None
        self.is_clean = True
        self.untracked_files = []
        self.modified_files = []

        # Facts dictionary - for storing gathered facts from expensive operations
        self.facts: dict = {}

        self._detect_state()

    def _detect_state(self):
        """Detect the current state of the repository."""
        try:
            self.repo = git.Repo(self.path)
            self.is_git_repo = True

            # Check if there are any commits
            try:
                self.has_commits = len(list(self.repo.iter_commits(max_count=1))) > 0
                self.branch_name = self.repo.active_branch.name
            except (ValueError, git.exc.GitCommandError):
                self.has_commits = False
                self.branch_name = None

            # Check for README
            readme_files = ["README.md", "README.rst", "README.txt", "README"]
            self.has_readme = any(
                (self.path / readme).exists() for readme in readme_files
            )

            # Check for .gitignore
            self.has_gitignore = (self.path / ".gitignore").exists()

            # Check for remote
            try:
                remotes = self.repo.remotes
                if remotes:
                    self.has_remote = True
                    self.remote_url = remotes[0].url
            except Exception:
                self.has_remote = False

            # Check working tree status
            if self.has_commits:
                try:
                    self.is_clean = not self.repo.is_dirty()
                    self.untracked_files = self.repo.untracked_files
                    self.modified_files = [
                        item.a_path for item in self.repo.index.diff(None)
                    ]
                except (git.exc.GitCommandError, ValueError):
                    # If there's an error checking status (e.g., no HEAD), set safe defaults
                    self.is_clean = True
                    self.untracked_files = []
                    self.modified_files = []

        except InvalidGitRepositoryError:
            self.is_git_repo = False

    def refresh(self):
        """Refresh the state detection."""
        self._detect_state()

    def has_fact(self, fact_name: str) -> bool:
        """Check if a specific fact has been gathered."""
        return fact_name in self.facts

    def get_fact(self, fact_name: str, default=None):
        """Get a specific fact value, or return default if not available."""
        return self.facts.get(fact_name, default)

    def set_facts(self, facts: dict):
        """Set multiple facts at once."""
        self.facts.update(facts)

    def clear_fact(self, fact_name: str):
        """Clear a specific fact (useful for refreshing)."""
        self.facts.pop(fact_name, None)

    def clear_facts_matching(self, prefix: str):
        """Clear all facts that start with a given prefix."""
        keys_to_remove = [key for key in self.facts.keys() if key.startswith(prefix)]
        for key in keys_to_remove:
            del self.facts[key]

    def get_remote_type(self) -> Optional[str]:
        """Determine the type of remote (github, gitlab, etc.)."""
        if not self.has_remote or not self.remote_url:
            return None

        remote_lower = self.remote_url.lower()
        if "github.com" in remote_lower:
            return "github"
        elif "gitlab.com" in remote_lower or "gitlab" in remote_lower:
            return "gitlab"
        else:
            return "unknown"

    def __repr__(self):
        return (
            f"RepoState(is_git_repo={self.is_git_repo}, "
            f"has_commits={self.has_commits}, "
            f"has_readme={self.has_readme}, "
            f"has_gitignore={self.has_gitignore}, "
            f"has_remote={self.has_remote}, "
            f"facts={len(self.facts)})"
        )
