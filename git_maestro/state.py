"""State detection module for git repositories."""

import os
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
            self.has_readme = any((self.path / readme).exists() for readme in readme_files)

            # Check for .gitignore
            self.has_gitignore = (self.path / ".gitignore").exists()

            # Check for remote
            try:
                remotes = self.repo.remotes
                if remotes:
                    self.has_remote = True
                    self.remote_url = remotes[0].url
            except:
                self.has_remote = False

            # Check working tree status
            if self.has_commits:
                try:
                    self.is_clean = not self.repo.is_dirty()
                    self.untracked_files = self.repo.untracked_files
                    self.modified_files = [item.a_path for item in self.repo.index.diff(None)]
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

    def __repr__(self):
        return (
            f"RepoState(is_git_repo={self.is_git_repo}, "
            f"has_commits={self.has_commits}, "
            f"has_readme={self.has_readme}, "
            f"has_gitignore={self.has_gitignore}, "
            f"has_remote={self.has_remote})"
        )
