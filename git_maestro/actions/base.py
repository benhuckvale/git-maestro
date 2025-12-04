"""Base action class for git-maestro actions."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from git_maestro.state import RepoState


class Action(ABC):
    """Base class for all actions."""

    def __init__(self):
        self.name = "Base Action"
        self.description = "A base action"
        self.emoji = "🔧"
        self.category = "setup"  # 'setup' or 'info'
        self.storage_dir: Optional[str] = (
            None  # Subdir name within .git-maestro/ if action needs storage
        )

    @abstractmethod
    def is_applicable(self, state: "RepoState") -> bool:
        """
        Determine if this action is applicable given the current state.

        Args:
            state: The current repository state

        Returns:
            True if the action can be performed, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, state: "RepoState") -> bool:
        """
        Execute the action.

        Args:
            state: The current repository state

        Returns:
            True if the action was successful, False otherwise
        """
        pass

    def get_display_name(self) -> str:
        """Get the display name for the menu."""
        return f"{self.emoji} {self.name}"

    def modifies_state(self) -> bool:
        """Return True if this action modifies repository state."""
        return self.category == "setup"

    def get_storage_path(self, state: "RepoState") -> Optional[Path]:
        """Get the storage directory path for this action, creating it if needed."""
        if not self.storage_dir:
            return None

        storage_path = state.path / ".git-maestro" / self.storage_dir
        storage_path.mkdir(parents=True, exist_ok=True)
        return storage_path

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(name='{self.name}', category='{self.category}')"
        )
