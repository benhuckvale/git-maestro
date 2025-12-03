"""Integration tests for actions."""

import pytest
from pathlib import Path
from git_maestro.state import RepoState
from git_maestro.actions import (
    InitRepoAction,
    AddReadmeAction,
    AddGitignoreAction,
)


def test_init_repo_action_applicable(temp_dir):
    """Test that InitRepoAction is applicable to non-git directories."""
    state = RepoState(temp_dir)
    action = InitRepoAction()

    assert action.is_applicable(state) is True


def test_init_repo_action_not_applicable(git_repo):
    """Test that InitRepoAction is not applicable to git repositories."""
    repo, temp_dir = git_repo
    state = RepoState(temp_dir)
    action = InitRepoAction()

    assert action.is_applicable(state) is False


def test_add_readme_action_applicable(git_repo_with_commits):
    """Test that AddReadmeAction is applicable when README is missing."""
    repo, temp_dir = git_repo_with_commits
    state = RepoState(temp_dir)
    action = AddReadmeAction()

    assert action.is_applicable(state) is True


def test_add_readme_action_not_applicable(git_repo_with_commits):
    """Test that AddReadmeAction is not applicable when README exists."""
    repo, temp_dir = git_repo_with_commits

    # Create README
    readme = temp_dir / "README.md"
    readme.write_text("# Test")

    state = RepoState(temp_dir)
    action = AddReadmeAction()

    assert action.is_applicable(state) is False


def test_add_readme_action_not_applicable_non_git(temp_dir):
    """Test that AddReadmeAction is not applicable to non-git directories."""
    state = RepoState(temp_dir)
    action = AddReadmeAction()

    assert action.is_applicable(state) is False


def test_add_gitignore_action_applicable(git_repo_with_commits):
    """Test that AddGitignoreAction is applicable when .gitignore is missing."""
    repo, temp_dir = git_repo_with_commits
    state = RepoState(temp_dir)
    action = AddGitignoreAction()

    assert action.is_applicable(state) is True


def test_add_gitignore_action_not_applicable(git_repo_with_commits):
    """Test that AddGitignoreAction is not applicable when .gitignore exists."""
    repo, temp_dir = git_repo_with_commits

    # Create .gitignore
    gitignore = temp_dir / ".gitignore"
    gitignore.write_text("*.pyc")

    state = RepoState(temp_dir)
    action = AddGitignoreAction()

    assert action.is_applicable(state) is False


def test_all_actions_have_required_attributes():
    """Test that all actions have required attributes."""
    actions = [
        InitRepoAction(),
        AddReadmeAction(),
        AddGitignoreAction(),
    ]

    for action in actions:
        assert hasattr(action, 'name')
        assert hasattr(action, 'description')
        assert hasattr(action, 'emoji')
        assert hasattr(action, 'is_applicable')
        assert hasattr(action, 'execute')
        assert callable(action.is_applicable)
        assert callable(action.execute)
        assert callable(action.get_display_name)


def test_action_display_name():
    """Test that action display names include emoji."""
    action = InitRepoAction()
    display_name = action.get_display_name()

    assert action.emoji in display_name
    assert action.name in display_name
