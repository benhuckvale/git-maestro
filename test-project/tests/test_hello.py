"""
Unit tests for hello.py
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hello import greet


def test_greet_default():
    """Test greet with default argument."""
    assert greet() == "Hello, World!"


def test_greet_custom_name():
    """Test greet with custom name."""
    assert greet("Alice") == "Hello, Alice!"
    assert greet("Bob") == "Hello, Bob!"


def test_greet_empty_string():
    """Test greet with empty string."""
    assert greet("") == "Hello, !"
