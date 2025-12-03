"""SSH configuration detection and management."""

import re
import subprocess
import platform
from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()


class SSHConfig:
    """
    Detect and manage SSH configuration for Git hosting providers.

    Works across macOS, Linux, and Windows (with OpenSSH).
    Note: Does not support PuTTY on Windows (uses different key format and config).
    """

    def __init__(self):
        self.platform = platform.system()
        self.ssh_dir = Path.home() / ".ssh"
        self.config_file = self.ssh_dir / "config"
        self.github_key: Optional[Path] = None
        self.gitlab_key: Optional[Path] = None
        self._detect_keys()

    def _detect_keys(self):
        """Detect SSH keys from SSH configuration."""
        # Try using ssh -G command first (more reliable)
        github_key_from_cmd = self._get_identity_from_ssh_command("github.com")
        if github_key_from_cmd:
            self.github_key = github_key_from_cmd

        gitlab_key_from_cmd = self._get_identity_from_ssh_command("gitlab.com")
        if gitlab_key_from_cmd:
            self.gitlab_key = gitlab_key_from_cmd

        # Fall back to parsing .ssh/config if ssh -G didn't work
        if not self.github_key or not self.gitlab_key:
            if self.config_file.exists():
                self._parse_ssh_config()

        # Fall back to default key locations if still not found
        if not self.github_key:
            self.github_key = self._find_default_key()
        if not self.gitlab_key:
            self.gitlab_key = self._find_default_key()

    def _get_identity_from_ssh_command(self, host: str) -> Optional[Path]:
        """
        Use 'ssh -G' to get the effective SSH configuration for a host.
        This is more reliable than parsing config files manually.

        Works on:
        - macOS (with OpenSSH)
        - Linux (with OpenSSH)
        - Windows 10/11 (with OpenSSH installed)

        Falls back gracefully if ssh command is not available.
        """
        try:
            # On Windows, we might need to use different path handling
            ssh_cmd = "ssh"
            if self.platform == "Windows":
                # Check if OpenSSH is available
                # Git for Windows and modern Windows 10/11 include OpenSSH
                try:
                    subprocess.run(
                        ["ssh", "-V"],
                        capture_output=True,
                        timeout=2
                    )
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    # OpenSSH not available, skip this method
                    return None

            result = subprocess.run(
                [ssh_cmd, "-G", host],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse the output for IdentityFile
                for line in result.stdout.splitlines():
                    if line.startswith("identityfile "):
                        key_path = line.split(None, 1)[1]

                        # Handle path expansion (~ and environment variables)
                        if self.platform == "Windows":
                            # Windows paths might use %USERPROFILE% or ~
                            key_path = key_path.replace("%USERPROFILE%", str(Path.home()))
                        key_path = key_path.replace("~", str(Path.home()))

                        key_path = Path(key_path)

                        # ssh -G returns all possible identity files, pick the first one that exists
                        if key_path.exists():
                            return key_path

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # ssh command not available or failed, will fall back to file parsing
            # This is normal on systems without OpenSSH or using PuTTY
            pass

        return None

    def _parse_ssh_config(self):
        """Parse SSH config file to find identity files for GitHub and GitLab."""
        try:
            with open(self.config_file, 'r') as f:
                content = f.read()

            # Parse SSH config for GitHub
            github_match = re.search(
                r'Host\s+github\.com\s*\n((?:\s+\w+.*\n)*)',
                content,
                re.MULTILINE
            )
            if github_match:
                host_config = github_match.group(1)
                identity_match = re.search(r'IdentityFile\s+(.+)', host_config)
                if identity_match:
                    key_path = identity_match.group(1).strip()
                    # Expand ~ to home directory
                    key_path = Path(key_path.replace('~', str(Path.home())))
                    if key_path.exists():
                        self.github_key = key_path

            # Parse SSH config for GitLab
            gitlab_match = re.search(
                r'Host\s+gitlab\.com\s*\n((?:\s+\w+.*\n)*)',
                content,
                re.MULTILINE
            )
            if gitlab_match:
                host_config = gitlab_match.group(1)
                identity_match = re.search(r'IdentityFile\s+(.+)', host_config)
                if identity_match:
                    key_path = identity_match.group(1).strip()
                    key_path = Path(key_path.replace('~', str(Path.home())))
                    if key_path.exists():
                        self.gitlab_key = key_path

        except Exception as e:
            console.print(f"[dim]Note: Could not parse SSH config: {e}[/dim]")

    def _find_default_key(self) -> Optional[Path]:
        """Find default SSH key if it exists."""
        default_keys = [
            self.ssh_dir / "id_rsa",
            self.ssh_dir / "id_ed25519",
            self.ssh_dir / "id_ecdsa",
        ]

        for key_path in default_keys:
            if key_path.exists():
                return key_path

        return None

    def get_public_key_content(self, key_path: Path) -> Optional[str]:
        """Get the content of a public key file."""
        pub_key_path = Path(str(key_path) + ".pub")
        if not pub_key_path.exists():
            return None

        try:
            return pub_key_path.read_text().strip()
        except Exception:
            return None

    def has_github_key(self) -> bool:
        """Check if a GitHub SSH key is configured."""
        return self.github_key is not None and self.github_key.exists()

    def has_gitlab_key(self) -> bool:
        """Check if a GitLab SSH key is configured."""
        return self.gitlab_key is not None and self.gitlab_key.exists()

    def get_github_public_key(self) -> Optional[str]:
        """Get the GitHub public key content."""
        if not self.github_key:
            return None
        return self.get_public_key_content(self.github_key)

    def get_gitlab_public_key(self) -> Optional[str]:
        """Get the GitLab public key content."""
        if not self.gitlab_key:
            return None
        return self.get_public_key_content(self.gitlab_key)

    def display_ssh_status(self, provider: str = "both"):
        """Display SSH key status for the provider."""
        if provider in ["github", "both"]:
            if self.has_github_key():
                console.print(f"[green]✓ GitHub SSH key found: {self.github_key}[/green]")
            else:
                console.print("[yellow]⚠ No GitHub SSH key detected[/yellow]")

        if provider in ["gitlab", "both"]:
            if self.has_gitlab_key():
                console.print(f"[green]✓ GitLab SSH key found: {self.gitlab_key}[/green]")
            else:
                console.print("[yellow]⚠ No GitLab SSH key detected[/yellow]")

    def verify_key_on_github(self, github_client) -> tuple[bool, str]:
        """
        Verify if the local SSH key is added to the GitHub account.

        Args:
            github_client: Authenticated PyGithub client

        Returns:
            (is_verified, message)
        """
        if not self.has_github_key():
            return (False, "No local SSH key found")

        public_key = self.get_github_public_key()
        if not public_key:
            return (False, f"Could not read public key from {self.github_key}.pub")

        try:
            # Get the key fingerprint from the public key content
            # GitHub API returns keys with their full content
            user = github_client.get_user()
            github_keys = user.get_keys()

            # Extract just the key part (without ssh-rsa and comment)
            local_key_parts = public_key.split()
            if len(local_key_parts) >= 2:
                local_key = local_key_parts[1]

                for key in github_keys:
                    if local_key in key.key:
                        return (True, f"SSH key '{key.title}' is registered on GitHub")

            return (False, "SSH key is not added to your GitHub account")

        except Exception as e:
            return (False, f"Could not verify key: {e}")

    def verify_key_on_gitlab(self, gitlab_client) -> tuple[bool, str]:
        """
        Verify if the local SSH key is added to the GitLab account.

        Args:
            gitlab_client: Authenticated python-gitlab client

        Returns:
            (is_verified, message)
        """
        if not self.has_gitlab_key():
            return (False, "No local SSH key found")

        public_key = self.get_gitlab_public_key()
        if not public_key:
            return (False, f"Could not read public key from {self.gitlab_key}.pub")

        try:
            # Get current user's SSH keys from GitLab
            user = gitlab_client.user
            keys = gitlab_client.user_keys.list()

            # Extract just the key part
            local_key_parts = public_key.split()
            if len(local_key_parts) >= 2:
                local_key = local_key_parts[1]

                for key in keys:
                    if local_key in key.key:
                        return (True, f"SSH key '{key.title}' is registered on GitLab")

            return (False, "SSH key is not added to your GitLab account")

        except Exception as e:
            return (False, f"Could not verify key: {e}")

    def __repr__(self):
        return (
            f"SSHConfig(github_key={self.github_key}, "
            f"gitlab_key={self.gitlab_key})"
        )
