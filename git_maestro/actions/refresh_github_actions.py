"""Action to refresh GitHub Actions facts."""

from .base import Action
from git_maestro.state import RepoState
from .fetch_github_actions import FetchGithubActionsAction


class RefreshGithubActionsAction(Action):
    """Refresh GitHub Actions workflow status."""

    def __init__(self):
        super().__init__()
        self.name = "Refresh GitHub Actions Status"
        self.description = "Re-check workflow runs for latest updates"
        self.emoji = "🔄"
        self.category = "info"

    def is_applicable(self, state: RepoState) -> bool:
        """Only show if GitHub Actions facts have already been gathered."""
        return state.get_remote_type() == "github" and state.has_fact(
            "github_actions_checked"
        )

    def execute(self, state: RepoState) -> bool:
        """Clear existing facts and re-run the fetch action."""
        # Clear GitHub Actions facts
        state.clear_facts_matching("github_actions_")

        # Re-run the fetch action
        fetch_action = FetchGithubActionsAction()
        return fetch_action.execute(state)
