"""Pytest configuration and fixtures."""

import pytest
import tempfile
import shutil
from pathlib import Path
import git


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def git_repo(temp_dir):
    """Create a temporary git repository."""
    repo = git.Repo.init(temp_dir)
    yield repo, temp_dir
    # Cleanup happens via temp_dir fixture


@pytest.fixture
def git_repo_with_commits(git_repo):
    """Create a git repository with an initial commit."""
    repo, temp_dir = git_repo

    # Create a test file
    test_file = temp_dir / "test.txt"
    test_file.write_text("test content")

    # Add and commit
    repo.index.add(["test.txt"])
    repo.index.commit("Initial commit")

    yield repo, temp_dir


@pytest.fixture
def git_repo_with_remote(git_repo_with_commits):
    """Create a git repository with a remote configured."""
    repo, temp_dir = git_repo_with_commits
    repo.create_remote("origin", "git@github.com:test/test.git")
    yield repo, temp_dir


@pytest.fixture
def git_repo_no_commits(git_repo):
    """Create a git repository with no commits."""
    repo, temp_dir = git_repo
    yield repo, temp_dir
