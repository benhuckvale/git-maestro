"""Tests for SSH configuration detection."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from git_maestro.ssh_config import SSHConfig


@pytest.fixture
def mock_ssh_dir(temp_dir, monkeypatch):
    """Mock the SSH directory."""
    ssh_dir = temp_dir / ".ssh"
    ssh_dir.mkdir()
    monkeypatch.setattr(Path, "home", lambda: temp_dir)
    return ssh_dir


def test_no_ssh_keys(temp_dir, monkeypatch):
    """Test when no SSH keys exist."""
    monkeypatch.setattr(Path, "home", lambda: temp_dir)
    ssh_config = SSHConfig()

    assert ssh_config.has_github_key() is False
    assert ssh_config.has_gitlab_key() is False


def test_default_key_detection(mock_ssh_dir):
    """Test detection of default SSH keys."""
    # Create a default key
    key_file = mock_ssh_dir / "id_rsa"
    key_file.write_text("fake private key")
    pub_file = mock_ssh_dir / "id_rsa.pub"
    pub_file.write_text("ssh-rsa AAAAB3NzaC1yc2E test@example.com")

    ssh_config = SSHConfig()

    assert ssh_config.has_github_key() is True
    assert ssh_config.has_gitlab_key() is True
    assert ssh_config.github_key == key_file


def test_ssh_config_parsing(mock_ssh_dir):
    """Test parsing of SSH config file."""
    # Create SSH config with GitHub entry
    config_file = mock_ssh_dir / "config"
    config_content = """
Host github.com
 HostName github.com
 IdentityFile ~/.ssh/id_rsa_github

Host gitlab.com
 HostName gitlab.com
 IdentityFile ~/.ssh/id_rsa_gitlab
"""
    config_file.write_text(config_content)

    # Create the key files
    github_key = mock_ssh_dir / "id_rsa_github"
    github_key.write_text("fake github key")
    gitlab_key = mock_ssh_dir / "id_rsa_gitlab"
    gitlab_key.write_text("fake gitlab key")

    ssh_config = SSHConfig()

    assert ssh_config.has_github_key() is True
    assert ssh_config.has_gitlab_key() is True
    assert ssh_config.github_key.name == "id_rsa_github"
    assert ssh_config.gitlab_key.name == "id_rsa_gitlab"


def test_get_public_key_content(mock_ssh_dir):
    """Test reading public key content."""
    # Create key pair
    key_file = mock_ssh_dir / "id_rsa"
    key_file.write_text("fake private key")
    pub_file = mock_ssh_dir / "id_rsa.pub"
    pub_content = "ssh-rsa AAAAB3NzaC1yc2E test@example.com"
    pub_file.write_text(pub_content)

    ssh_config = SSHConfig()
    content = ssh_config.get_public_key_content(key_file)

    assert content == pub_content


def test_get_public_key_missing(mock_ssh_dir):
    """Test getting public key when .pub file doesn't exist."""
    key_file = mock_ssh_dir / "id_rsa"
    key_file.write_text("fake private key")
    # No .pub file created

    ssh_config = SSHConfig()
    content = ssh_config.get_public_key_content(key_file)

    assert content is None


@patch('subprocess.run')
def test_ssh_command_detection(mock_run, mock_ssh_dir):
    """Test SSH detection using ssh -G command."""
    # Mock ssh -G output
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = f"identityfile {mock_ssh_dir}/id_rsa_github\nidentityfile {mock_ssh_dir}/id_rsa\n"
    mock_run.return_value = mock_result

    # Create the key file
    key_file = mock_ssh_dir / "id_rsa_github"
    key_file.write_text("fake key")

    ssh_config = SSHConfig()

    # Should find the first existing key from ssh -G output
    assert ssh_config.has_github_key() is True


@patch('subprocess.run')
def test_ssh_command_failure_fallback(mock_run, mock_ssh_dir):
    """Test fallback when ssh -G command fails."""
    # Mock ssh -G to fail
    mock_run.side_effect = FileNotFoundError()

    # Create a default key for fallback
    key_file = mock_ssh_dir / "id_rsa"
    key_file.write_text("fake key")

    ssh_config = SSHConfig()

    # Should fall back to default key detection
    assert ssh_config.has_github_key() is True
