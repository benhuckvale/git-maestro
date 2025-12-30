"""Tests for Azure DevOps integration."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from git_maestro.azure import parse_azure_url, get_org_project_from_url, AzureClient


class TestParseAzureUrl:
    """Tests for Azure URL parsing."""

    def test_parse_https_url(self):
        """Test parsing HTTPS Azure DevOps URL."""
        url = "https://dev.azure.com/myorg/myproject/_git/myrepo"
        org, project, repo = parse_azure_url(url)

        assert org == "myorg"
        assert project == "myproject"
        assert repo == "myrepo"

    def test_parse_https_url_with_git_suffix(self):
        """Test parsing HTTPS URL with .git suffix."""
        url = "https://dev.azure.com/myorg/myproject/_git/myrepo.git"
        org, project, repo = parse_azure_url(url)

        assert org == "myorg"
        assert project == "myproject"
        assert repo == "myrepo"

    def test_parse_ssh_url(self):
        """Test parsing SSH Azure DevOps URL."""
        url = "git@ssh.dev.azure.com:v3/myorg/myproject/myrepo"
        org, project, repo = parse_azure_url(url)

        assert org == "myorg"
        assert project == "myproject"
        assert repo == "myrepo"

    def test_parse_ssh_url_with_git_suffix(self):
        """Test parsing SSH URL with .git suffix."""
        url = "git@ssh.dev.azure.com:v3/myorg/myproject/myrepo.git"
        org, project, repo = parse_azure_url(url)

        assert org == "myorg"
        assert project == "myproject"
        assert repo == "myrepo"

    def test_parse_visualstudio_legacy_url(self):
        """Test parsing legacy visualstudio.com URL."""
        url = "https://myorg.visualstudio.com/myproject/_git/myrepo"
        org, project, repo = parse_azure_url(url)

        assert org == "myorg"
        assert project == "myproject"
        assert repo == "myrepo"

    def test_parse_invalid_url(self):
        """Test parsing invalid URL returns None."""
        url = "https://github.com/org/repo"
        result = parse_azure_url(url)

        assert result is None

    def test_parse_empty_url(self):
        """Test parsing empty URL returns None."""
        result = parse_azure_url("")

        assert result is None


class TestGetOrgProjectFromUrl:
    """Tests for extracting org and project from URL."""

    def test_get_org_project_https(self):
        """Test extracting org and project from HTTPS URL."""
        url = "https://dev.azure.com/myorg/myproject/_git/myrepo"
        org, project = get_org_project_from_url(url)

        assert org == "myorg"
        assert project == "myproject"

    def test_get_org_project_ssh(self):
        """Test extracting org and project from SSH URL."""
        url = "git@ssh.dev.azure.com:v3/myorg/myproject/myrepo"
        org, project = get_org_project_from_url(url)

        assert org == "myorg"
        assert project == "myproject"

    def test_get_org_project_invalid_url(self):
        """Test extracting from invalid URL returns None."""
        url = "https://github.com/org/repo"
        result = get_org_project_from_url(url)

        assert result is None


class TestAzureClientExtractIssues:
    """Tests for issue extraction from timeline records."""

    def test_extract_single_error_issue(self):
        """Test extracting a single error issue."""
        client = AzureClient("org", "project", "token")

        # Create mock issue
        issue = Mock()
        issue.message = "No parallelism available"
        issue.type = "error"

        # Create mock record with issues
        record = Mock()
        record.issues = [issue]

        issues = client._extract_issues(record)

        assert len(issues) == 1
        assert issues[0]["message"] == "No parallelism available"
        assert issues[0]["type"] == "error"

    def test_extract_multiple_issues(self):
        """Test extracting multiple issues."""
        client = AzureClient("org", "project", "token")

        issues_list = [
            Mock(message="Error 1", type="error"),
            Mock(message="Warning 1", type="warning"),
        ]

        record = Mock()
        record.issues = issues_list

        issues = client._extract_issues(record)

        assert len(issues) == 2
        assert issues[0]["message"] == "Error 1"
        assert issues[0]["type"] == "error"
        assert issues[1]["message"] == "Warning 1"
        assert issues[1]["type"] == "warning"

    def test_extract_no_issues(self):
        """Test extracting from record with no issues."""
        client = AzureClient("org", "project", "token")

        record = Mock()
        record.issues = None

        issues = client._extract_issues(record)

        assert issues == []

    def test_extract_empty_issues_list(self):
        """Test extracting from record with empty issues list."""
        client = AzureClient("org", "project", "token")

        record = Mock()
        record.issues = []

        issues = client._extract_issues(record)

        assert issues == []


class TestAzureClientBuildTimeline:
    """Tests for Build API timeline retrieval."""

    @patch("git_maestro.azure.AzureClient._get_connection")
    def test_get_build_timeline_success(self, mock_get_conn):
        """Test successful timeline retrieval."""
        # Mock the connection and client
        mock_build_client = Mock()
        mock_connection = Mock()
        mock_connection.clients.get_build_client.return_value = mock_build_client

        mock_get_conn.return_value = mock_connection

        # Create mock timeline
        mock_timeline = Mock()
        mock_timeline.id = "timeline-123"
        mock_build_client.get_build_timeline.return_value = mock_timeline

        # Test
        client = AzureClient("org", "project", "token")
        timeline = client.get_build_timeline(1)

        assert timeline is not None
        assert timeline.id == "timeline-123"
        mock_build_client.get_build_timeline.assert_called_once_with(
            project="project", build_id=1
        )

    @patch("git_maestro.azure.AzureClient._get_connection")
    def test_get_build_timeline_error(self, mock_get_conn):
        """Test timeline retrieval with error."""
        mock_get_conn.side_effect = Exception("API Error")

        client = AzureClient("org", "project", "token")
        timeline = client.get_build_timeline(1)

        assert timeline is None


class TestAzureClientCompleteExecutionLogs:
    """Tests for complete execution logs with issue extraction."""

    @patch("git_maestro.azure.AzureClient.get_build_log_content")
    @patch("git_maestro.azure.AzureClient.get_build_timeline")
    def test_get_complete_execution_logs_with_issues(
        self, mock_get_timeline, mock_get_log
    ):
        """Test retrieving complete logs with diagnostic issues."""
        # Create mock timeline records matching real structure:
        # Stage (__default)
        #   Phase (Job) - no issues
        #     Job (Job) - HAS ISSUES
        #   Checkpoint

        job_record = Mock()
        job_record.id = "job-123"
        job_record.name = "Job"
        job_record.type = "Job"
        job_record.state = "completed"
        job_record.result = "failed"
        job_record.parent_id = "phase-456"
        job_record.start_time = None
        job_record.finish_time = None
        job_record.error_count = 1
        job_record.warning_count = 0
        job_record.log = None

        # Create error issue
        error_issue = Mock()
        error_issue.message = "No hosted parallelism has been purchased or granted. To request a free parallelism grant, please fill out the following form https://aka.ms/azpipelines-parallelism-request"
        error_issue.type = "error"
        job_record.issues = [error_issue]

        phase_record = Mock()
        phase_record.id = "phase-456"
        phase_record.name = "Job"
        phase_record.type = "Phase"
        phase_record.state = "completed"
        phase_record.result = "failed"
        phase_record.parent_id = "stage-789"
        phase_record.start_time = None
        phase_record.finish_time = None
        phase_record.error_count = 0
        phase_record.warning_count = 0
        phase_record.log = Mock(id=3)
        phase_record.issues = None

        checkpoint_record = Mock()
        checkpoint_record.id = "checkpoint-999"
        checkpoint_record.name = "Checkpoint"
        checkpoint_record.type = "Checkpoint"
        checkpoint_record.state = "completed"
        checkpoint_record.result = "succeeded"
        checkpoint_record.parent_id = "stage-789"
        checkpoint_record.start_time = None
        checkpoint_record.finish_time = None
        checkpoint_record.error_count = 0
        checkpoint_record.warning_count = 0
        checkpoint_record.log = None
        checkpoint_record.issues = None

        stage_record = Mock()
        stage_record.id = "stage-789"
        stage_record.name = "__default"
        stage_record.type = "Stage"
        stage_record.state = "completed"
        stage_record.result = "abandoned"
        stage_record.parent_id = None
        stage_record.start_time = None
        stage_record.finish_time = None
        stage_record.error_count = 0
        stage_record.warning_count = 0
        stage_record.log = None
        stage_record.issues = None

        # Create mock timeline
        mock_timeline = Mock()
        mock_timeline.id = "timeline-123"
        mock_timeline.records = [stage_record, checkpoint_record, phase_record, job_record]

        mock_get_timeline.return_value = mock_timeline
        mock_get_log.return_value = None  # No log content for this test

        # Test
        client = AzureClient("org", "project", "token")
        complete_logs = client.get_complete_execution_logs(1)

        # Verify structure
        assert complete_logs["build_id"] == 1
        assert complete_logs["timeline_id"] == "timeline-123"
        assert len(complete_logs["jobs"]) == 1

        job = complete_logs["jobs"][0]
        assert job["name"] == "__default"
        assert job["type"] == "Stage"
        assert job["result"] == "abandoned"
        assert len(job["tasks"]) == 2

        # Find the Phase task
        phase_task = next(t for t in job["tasks"] if t["type"] == "Phase")
        assert phase_task["name"] == "Job"
        assert len(phase_task["issues"]) == 1
        assert phase_task["issues"][0]["type"] == "error"
        assert "No hosted parallelism" in phase_task["issues"][0]["message"]

    @patch("git_maestro.azure.AzureClient.get_build_timeline")
    def test_get_complete_execution_logs_empty_timeline(self, mock_get_timeline):
        """Test with empty timeline."""
        mock_timeline = Mock()
        mock_timeline.id = "timeline-123"
        mock_timeline.records = []

        mock_get_timeline.return_value = mock_timeline

        client = AzureClient("org", "project", "token")
        complete_logs = client.get_complete_execution_logs(1)

        assert complete_logs["build_id"] == 1
        assert complete_logs["jobs"] == []

    @patch("git_maestro.azure.AzureClient.get_build_timeline")
    def test_get_complete_execution_logs_no_timeline(self, mock_get_timeline):
        """Test when timeline is None."""
        mock_get_timeline.return_value = None

        client = AzureClient("org", "project", "token")
        complete_logs = client.get_complete_execution_logs(1)

        assert complete_logs["build_id"] == 1
        assert complete_logs["timeline_id"] is None
        assert complete_logs["jobs"] == []


class TestAzureClientLogContent:
    """Tests for log content retrieval."""

    @patch("git_maestro.azure.AzureClient._get_connection")
    def test_get_build_log_content_string(self, mock_get_conn):
        """Test retrieving log content as string."""
        mock_build_client = Mock()
        mock_connection = Mock()
        mock_connection.clients.get_build_client.return_value = mock_build_client

        mock_get_conn.return_value = mock_connection

        # Mock log content as string
        mock_build_client.get_build_log.return_value = "Log content here"

        client = AzureClient("org", "project", "token")
        content = client.get_build_log_content(1, 1)

        assert content == "Log content here"

    @patch("git_maestro.azure.AzureClient._get_connection")
    def test_get_build_log_content_generator(self, mock_get_conn):
        """Test retrieving log content from generator."""
        mock_build_client = Mock()
        mock_connection = Mock()
        mock_connection.clients.get_build_client.return_value = mock_build_client

        mock_get_conn.return_value = mock_connection

        # Mock log content as generator (like the real API returns)
        def log_generator():
            yield "Line 1\n"
            yield "Line 2\n"
            yield "Line 3"

        mock_build_client.get_build_log.return_value = log_generator()

        client = AzureClient("org", "project", "token")
        content = client.get_build_log_content(1, 1)

        assert content == "Line 1\nLine 2\nLine 3"

    @patch("git_maestro.azure.AzureClient._get_connection")
    def test_get_build_log_content_error(self, mock_get_conn):
        """Test log content retrieval with error."""
        mock_get_conn.side_effect = Exception("API Error")

        client = AzureClient("org", "project", "token")
        content = client.get_build_log_content(1, 1)

        assert content is None

    @patch("git_maestro.azure.AzureClient._get_connection")
    def test_get_build_log_content_empty(self, mock_get_conn):
        """Test log content retrieval when empty."""
        mock_build_client = Mock()
        mock_connection = Mock()
        mock_connection.clients.get_build_client.return_value = mock_build_client

        mock_get_conn.return_value = mock_connection

        mock_build_client.get_build_log.return_value = None

        client = AzureClient("org", "project", "token")
        content = client.get_build_log_content(1, 1)

        assert content is None
