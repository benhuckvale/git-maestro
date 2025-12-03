"""Tests for CLI functionality."""

import pytest
from unittest.mock import patch, MagicMock
from git_maestro.cli import get_all_actions


def test_get_all_actions():
    """Test that get_all_actions returns action instances."""
    actions = get_all_actions()

    assert len(actions) > 0
    assert all(hasattr(action, 'is_applicable') for action in actions)
    assert all(hasattr(action, 'execute') for action in actions)


def test_all_actions_are_unique():
    """Test that all actions are unique types."""
    actions = get_all_actions()
    action_types = [type(action) for action in actions]

    assert len(action_types) == len(set(action_types))
