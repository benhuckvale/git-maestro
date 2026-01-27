"""Version information for git-maestro."""

import subprocess
from pathlib import Path


def get_git_info() -> tuple[str, str, bool]:
    """Get git commit hash, describe output, and dirty status for this package.

    Returns:
        Tuple of (commit_hash, git_describe, is_dirty) or ("", "", False) if not a git repo
    """
    try:
        # Get the directory where git_maestro is installed
        package_dir = Path(__file__).parent.parent

        # Get commit hash
        commit = subprocess.check_output(
            ["git", "-C", str(package_dir), "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        # Get git describe (tag-based version)
        describe = subprocess.check_output(
            ["git", "-C", str(package_dir), "describe", "--tags", "--always"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()

        # Check if working directory is dirty
        status = subprocess.check_output(
            ["git", "-C", str(package_dir), "status", "--porcelain"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        is_dirty = bool(status)

        return commit, describe, is_dirty
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "", "", False


