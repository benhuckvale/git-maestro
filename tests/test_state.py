"""Tests for repository state detection."""

from git_maestro.state import RepoState


def test_non_git_directory(temp_dir):
    """Test state detection in a non-git directory."""
    state = RepoState(temp_dir)

    assert state.is_git_repo is False
    assert state.has_commits is False
    assert state.has_readme is False
    assert state.has_gitignore is False
    assert state.has_remote is False


def test_empty_git_repo(git_repo):
    """Test state detection in an empty git repository."""
    repo, temp_dir = git_repo
    state = RepoState(temp_dir)

    assert state.is_git_repo is True
    assert state.has_commits is False
    assert state.branch_name is None
    assert state.has_readme is False
    assert state.has_gitignore is False
    assert state.has_remote is False


def test_git_repo_with_commits(git_repo_with_commits):
    """Test state detection in a git repository with commits."""
    repo, temp_dir = git_repo_with_commits
    state = RepoState(temp_dir)

    assert state.is_git_repo is True
    assert state.has_commits is True
    assert state.branch_name is not None
    assert state.has_remote is False


def test_git_repo_with_readme(git_repo_with_commits):
    """Test README detection."""
    repo, temp_dir = git_repo_with_commits

    # Create README
    readme = temp_dir / "README.md"
    readme.write_text("# Test Project")

    state = RepoState(temp_dir)
    assert state.has_readme is True


def test_git_repo_with_gitignore(git_repo_with_commits):
    """Test .gitignore detection."""
    repo, temp_dir = git_repo_with_commits

    # Create .gitignore
    gitignore = temp_dir / ".gitignore"
    gitignore.write_text("*.pyc\n__pycache__/\n")

    state = RepoState(temp_dir)
    assert state.has_gitignore is True


def test_git_repo_with_remote(git_repo_with_remote):
    """Test remote detection."""
    repo, temp_dir = git_repo_with_remote
    state = RepoState(temp_dir)

    assert state.has_remote is True
    assert state.remote_url == "git@github.com:test/test.git"


def test_git_repo_untracked_files(git_repo_with_commits):
    """Test untracked files detection."""
    repo, temp_dir = git_repo_with_commits

    # Create an untracked file
    new_file = temp_dir / "untracked.txt"
    new_file.write_text("untracked content")

    state = RepoState(temp_dir)
    assert "untracked.txt" in state.untracked_files


def test_git_repo_modified_files(git_repo_with_commits):
    """Test modified files detection."""
    repo, temp_dir = git_repo_with_commits

    # Modify the existing file
    test_file = temp_dir / "test.txt"
    test_file.write_text("modified content")

    state = RepoState(temp_dir)
    assert "test.txt" in state.modified_files


def test_state_refresh(git_repo_with_commits):
    """Test that state can be refreshed."""
    repo, temp_dir = git_repo_with_commits
    state = RepoState(temp_dir)

    assert state.has_readme is False

    # Add README
    readme = temp_dir / "README.md"
    readme.write_text("# Test")

    # Refresh state
    state.refresh()
    assert state.has_readme is True


def test_git_repo_no_commits_state(git_repo_no_commits):
    """Test that repos with no commits don't crash when checking status."""
    repo, temp_dir = git_repo_no_commits
    state = RepoState(temp_dir)

    # Should not raise any exceptions
    assert state.is_git_repo is True
    assert state.has_commits is False
    assert state.is_clean is True
    assert state.untracked_files == []
    assert state.modified_files == []
