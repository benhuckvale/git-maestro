"""Actions module for git-maestro."""

from .base import Action
from .init_repo import InitRepoAction
from .initial_commit import InitialCommitAction
from .add_readme import AddReadmeAction
from .add_gitignore import AddGitignoreAction
from .setup_remote import SetupRemoteAction
from .create_remote_repo import CreateRemoteRepoAction
from .fetch_github_actions import FetchGithubActionsAction
from .refresh_github_actions import RefreshGithubActionsAction
from .view_failed_jobs import ViewFailedJobsAction
from .download_job_traces import DownloadJobTracesAction
from .get_github_actions_logs import GetGithubActionsLogsAction
from .setup_azure_devops import SetupAzureDevOpsAction
from .configure_azure_token import ConfigureAzureTokenAction
from .fetch_azure_pipelines import FetchAzurePipelinesAction
from .get_azure_pipelines import GetAzurePipelinesAction
from .download_azure_stage_logs import DownloadAzureStageLogsAction
from .fetch_gitlab_pipelines import FetchGitlabPipelinesAction
from .get_gitlab_pipelines import GetGitlabPipelinesAction

__all__ = [
    "Action",
    "InitRepoAction",
    "InitialCommitAction",
    "AddReadmeAction",
    "AddGitignoreAction",
    "SetupRemoteAction",
    "CreateRemoteRepoAction",
    "FetchGithubActionsAction",
    "RefreshGithubActionsAction",
    "ViewFailedJobsAction",
    "DownloadJobTracesAction",
    "GetGithubActionsLogsAction",
    "SetupAzureDevOpsAction",
    "ConfigureAzureTokenAction",
    "FetchAzurePipelinesAction",
    "GetAzurePipelinesAction",
    "DownloadAzureStageLogsAction",
    "FetchGitlabPipelinesAction",
    "GetGitlabPipelinesAction",
]
