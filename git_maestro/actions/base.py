"""Base action class for git-maestro actions."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from git_maestro.state import RepoState


class Action(ABC):
    """Base class for all actions."""

    def __init__(self):
        self.name = "Base Action"
        self.description = "A base action"
        self.emoji = "🔧"

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

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"
