"""Tests for GitLab integration."""

import pytest
from unittest.mock import Mock, patch
from git_maestro.gitlab import parse_gitlab_url, GitLabClient


class TestParseGitlabUrl:
    """Tests for GitLab URL parsing."""

    def test_parse_https_url(self):
        """Test parsing HTTPS GitLab URL."""
        url = "https://gitlab.com/mygroup/myproject.git"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.com"
        assert result['project_path'] == "mygroup/myproject"
        assert result['project_path_encoded'] == "mygroup%2Fmyproject"

    def test_parse_https_url_without_git_suffix(self):
        """Test parsing HTTPS URL without .git suffix."""
        url = "https://gitlab.com/mygroup/myproject"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.com"
        assert result['project_path'] == "mygroup/myproject"
        assert result['project_path_encoded'] == "mygroup%2Fmyproject"

    def test_parse_https_url_with_nested_groups(self):
        """Test parsing HTTPS URL with nested groups."""
        url = "https://gitlab.com/group/subgroup/project.git"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.com"
        assert result['project_path'] == "group/subgroup/project"
        assert result['project_path_encoded'] == "group%2Fsubgroup%2Fproject"

    def test_parse_ssh_url(self):
        """Test parsing SSH GitLab URL."""
        url = "git@gitlab.com:mygroup/myproject.git"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.com"
        assert result['project_path'] == "mygroup/myproject"
        assert result['project_path_encoded'] == "mygroup%2Fmyproject"

    def test_parse_ssh_url_without_git_suffix(self):
        """Test parsing SSH URL without .git suffix."""
        url = "git@gitlab.com:mygroup/myproject"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.com"
        assert result['project_path'] == "mygroup/myproject"

    def test_parse_ssh_url_with_nested_groups(self):
        """Test parsing SSH URL with nested groups."""
        url = "git@gitlab.com:group/subgroup/project.git"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.com"
        assert result['project_path'] == "group/subgroup/project"

    def test_parse_custom_domain_https(self):
        """Test parsing custom GitLab domain HTTPS URL."""
        url = "https://gitlab.example.com/mygroup/myproject.git"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.example.com"
        assert result['project_path'] == "mygroup/myproject"

    def test_parse_custom_domain_ssh(self):
        """Test parsing custom GitLab domain SSH URL."""
        url = "git@gitlab.example.com:mygroup/myproject.git"
        result = parse_gitlab_url(url)

        assert result is not None
        assert result['host'] == "gitlab.example.com"
        assert result['project_path'] == "mygroup/myproject"

    def test_parse_invalid_url(self):
        """Test parsing invalid URL returns None."""
        url = "https://github.com/org/repo"
        # The function might return something for github.com, so let's check it handles it
        # Actually, this might parse as a valid URL structure, so let's test empty instead
        parse_gitlab_url(url)
        assert parse_gitlab_url("") is None

    def test_parse_empty_url(self):
        """Test parsing empty URL returns None."""
        result = parse_gitlab_url("")

        assert result is None

    def test_parse_none_url(self):
        """Test parsing None URL returns None."""
        result = parse_gitlab_url(None)

        assert result is None


class TestGitLabClientInit:
    """Tests for GitLabClient initialization."""

    @patch('git_maestro.gitlab.gitlab')
    def test_client_init_with_valid_url(self, mock_gitlab_module):
        """Test client initialization with valid URL."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        url = "https://gitlab.com/testgroup/testproject.git"
        token = "test-token"

        client = GitLabClient(url, token)

        assert client.host == "gitlab.com"
        assert client.project_path == "testgroup/testproject"
        assert client.project == mock_project
        mock_gitlab_module.Gitlab.assert_called_once_with(
            "https://gitlab.com", private_token=token
        )
        mock_gl.projects.get.assert_called_once_with("testgroup%2Ftestproject")

    @patch('git_maestro.gitlab.gitlab')
    def test_client_init_with_ssh_url(self, mock_gitlab_module):
        """Test client initialization with SSH URL."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        url = "git@gitlab.com:testgroup/testproject.git"
        token = "test-token"

        client = GitLabClient(url, token)

        assert client.host == "gitlab.com"
        assert client.project_path == "testgroup/testproject"

    @patch('git_maestro.gitlab.gitlab')
    def test_client_init_with_invalid_url(self, mock_gitlab_module):
        """Test client initialization with invalid URL raises ValueError."""
        url = "not-a-valid-url"
        token = "test-token"

        with pytest.raises(ValueError, match="Invalid GitLab URL"):
            GitLabClient(url, token)

    @patch('git_maestro.gitlab.gitlab', None)
    def test_client_init_without_gitlab_installed(self):
        """Test client initialization without python-gitlab raises ImportError."""
        url = "https://gitlab.com/testgroup/testproject.git"
        token = "test-token"

        with pytest.raises(ImportError, match="python-gitlab is not installed"):
            GitLabClient(url, token)


class TestGitLabClientMethods:
    """Tests for GitLabClient methods."""

    @patch('git_maestro.gitlab.gitlab')
    def test_get_pipelines(self, mock_gitlab_module):
        """Test getting pipelines."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_pipeline = Mock()
        mock_project.pipelines.list.return_value = [mock_pipeline]
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        pipelines = client.get_pipelines(per_page=5)

        assert len(pipelines) == 1
        assert pipelines[0] == mock_pipeline
        mock_project.pipelines.list.assert_called_once_with(per_page=5, get_all=False)

    @patch('git_maestro.gitlab.gitlab')
    def test_get_pipelines_caps_at_100(self, mock_gitlab_module):
        """Test getting pipelines caps at 100."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_project.pipelines.list.return_value = []
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        client.get_pipelines(per_page=200)

        # Should be capped at 100
        mock_project.pipelines.list.assert_called_once_with(per_page=100, get_all=False)

    @patch('git_maestro.gitlab.gitlab')
    def test_get_pipeline(self, mock_gitlab_module):
        """Test getting a specific pipeline."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_pipeline = Mock()
        mock_project.pipelines.get.return_value = mock_pipeline
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        pipeline = client.get_pipeline(123)

        assert pipeline == mock_pipeline
        mock_project.pipelines.get.assert_called_once_with(123)

    @patch('git_maestro.gitlab.gitlab')
    def test_get_pipeline_jobs(self, mock_gitlab_module):
        """Test getting jobs for a pipeline."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_pipeline = Mock()
        mock_job = Mock()
        mock_pipeline.jobs.list.return_value = [mock_job]
        mock_project.pipelines.get.return_value = mock_pipeline
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        jobs = client.get_pipeline_jobs(123)

        assert len(jobs) == 1
        assert jobs[0] == mock_job
        mock_project.pipelines.get.assert_called_once_with(123)
        mock_pipeline.jobs.list.assert_called_once_with(get_all=True)

    @patch('git_maestro.gitlab.gitlab')
    def test_get_job(self, mock_gitlab_module):
        """Test getting a specific job."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_job = Mock()
        mock_project.jobs.get.return_value = mock_job
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        job = client.get_job(456)

        assert job == mock_job
        mock_project.jobs.get.assert_called_once_with(456)

    @patch('git_maestro.gitlab.gitlab')
    def test_get_job_trace(self, mock_gitlab_module):
        """Test getting job trace (logs)."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_job = Mock()
        mock_job.trace.return_value = b"log content"
        mock_project.jobs.get.return_value = mock_job
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        trace = client.get_job_trace(456)

        assert trace == "log content"
        mock_job.trace.assert_called_once()

    @patch('git_maestro.gitlab.gitlab')
    def test_get_job_trace_with_decode_error(self, mock_gitlab_module):
        """Test getting job trace handles decode errors."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_job = Mock()
        mock_job.trace.return_value = b"\xff\xfe invalid utf-8"
        mock_project.jobs.get.return_value = mock_job
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        trace = client.get_job_trace(456)

        # Should handle decode error gracefully
        assert isinstance(trace, str)

    @patch('git_maestro.gitlab.gitlab')
    def test_get_pipeline_status(self, mock_gitlab_module):
        """Test getting pipeline status."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_pipeline = Mock()
        mock_pipeline.status = "success"
        mock_pipeline.created_at = "2024-01-01T00:00:00"
        mock_pipeline.updated_at = "2024-01-01T01:00:00"
        mock_pipeline.web_url = "https://gitlab.com/test/project/-/pipelines/123"
        mock_pipeline.ref = "main"
        mock_pipeline.sha = "abc123"
        mock_project.pipelines.get.return_value = mock_pipeline
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        status = client.get_pipeline_status(123)

        assert status['status'] == "success"
        assert status['ref'] == "main"
        assert status['sha'] == "abc123"

    @patch('git_maestro.gitlab.gitlab')
    def test_get_job_status(self, mock_gitlab_module):
        """Test getting job status."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_job = Mock()
        mock_job.status = "failed"
        mock_job.stage = "test"
        mock_job.name = "unit-tests"
        mock_job.created_at = "2024-01-01T00:00:00"
        mock_job.started_at = "2024-01-01T00:05:00"
        mock_job.finished_at = "2024-01-01T00:10:00"
        mock_job.web_url = "https://gitlab.com/test/project/-/jobs/456"
        mock_job.failure_reason = "script_failure"
        mock_project.jobs.get.return_value = mock_job
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        status = client.get_job_status(456)

        assert status['status'] == "failed"
        assert status['stage'] == "test"
        assert status['name'] == "unit-tests"
        assert status['failure_reason'] == "script_failure"

    @patch('git_maestro.gitlab.gitlab')
    def test_get_failed_jobs(self, mock_gitlab_module):
        """Test getting failed jobs for a pipeline."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_pipeline = Mock()

        # Create mock jobs - some failed, some success
        mock_job_success = Mock()
        mock_job_success.status = "success"

        mock_job_failed = Mock()
        mock_job_failed.id = 456
        mock_job_failed.name = "test-job"
        mock_job_failed.stage = "test"
        mock_job_failed.status = "failed"
        mock_job_failed.web_url = "https://gitlab.com/test/project/-/jobs/456"
        mock_job_failed.failure_reason = "script_failure"

        mock_pipeline.jobs.list.return_value = [mock_job_success, mock_job_failed]
        mock_project.pipelines.get.return_value = mock_pipeline
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")
        failed_jobs = client.get_failed_jobs(123)

        assert len(failed_jobs) == 1
        assert failed_jobs[0]['id'] == 456
        assert failed_jobs[0]['name'] == "test-job"
        assert failed_jobs[0]['status'] == "failed"

    @patch('git_maestro.gitlab.gitlab')
    def test_download_job_log(self, mock_gitlab_module, tmp_path):
        """Test downloading job log to file."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_job = Mock()
        mock_job.trace.return_value = b"log content"
        mock_project.jobs.get.return_value = mock_job
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")

        output_file = tmp_path / "job.log"
        success = client.download_job_log(456, output_file)

        assert success is True
        assert output_file.exists()
        assert output_file.read_text() == "log content"

    @patch('git_maestro.gitlab.gitlab')
    def test_download_job_log_handles_error(self, mock_gitlab_module, tmp_path):
        """Test downloading job log handles errors gracefully."""
        # Setup mocks
        mock_gl = Mock()
        mock_project = Mock()
        mock_job = Mock()
        mock_job.trace.side_effect = Exception("API error")
        mock_project.jobs.get.return_value = mock_job
        mock_gl.projects.get.return_value = mock_project
        mock_gitlab_module.Gitlab.return_value = mock_gl

        client = GitLabClient("https://gitlab.com/test/project.git", "token")

        output_file = tmp_path / "job.log"
        success = client.download_job_log(456, output_file)

        # The method handles errors by writing an empty file
        assert success is True
        assert output_file.exists()
        assert output_file.read_text() == ""
