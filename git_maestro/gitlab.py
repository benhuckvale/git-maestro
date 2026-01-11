"""GitLab Pipelines integration for git-maestro."""

from pathlib import Path
from typing import Optional, Dict, List, Any
from urllib.parse import urlparse
import re

try:
    import gitlab
    from gitlab.v4.objects import Project, ProjectPipeline, ProjectPipelineJob
except ImportError:
    gitlab = None


def parse_gitlab_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a GitLab repository URL to extract the project path.

    Supports:
    - HTTPS: https://gitlab.com/group/project.git
    - SSH: git@gitlab.com:group/project.git
    - Custom domains: https://gitlab.example.com/group/project.git

    Returns:
        Dict with 'host', 'project_path', and 'project_path_encoded' keys, or None if invalid
    """
    if not url:
        return None

    # Handle SSH format: git@gitlab.com:group/project.git
    ssh_match = re.match(r'^git@([^:]+):(.+?)(?:\.git)?$', url)
    if ssh_match:
        host = ssh_match.group(1)
        project_path = ssh_match.group(2)
        return {
            'host': host,
            'project_path': project_path,
            'project_path_encoded': project_path.replace('/', '%2F')
        }

    # Handle HTTPS format
    parsed = urlparse(url)
    if parsed.scheme in ('http', 'https') and parsed.netloc:
        # Remove leading slash and .git suffix
        project_path = parsed.path.lstrip('/').rstrip('/')
        if project_path.endswith('.git'):
            project_path = project_path[:-4]

        return {
            'host': parsed.netloc,
            'project_path': project_path,
            'project_path_encoded': project_path.replace('/', '%2F')
        }

    return None


class GitLabClient:
    """Client for interacting with GitLab API."""

    def __init__(self, url: str, token: str):
        """
        Initialize GitLab client.

        Args:
            url: Repository URL (HTTPS or SSH)
            token: GitLab personal access token
        """
        if gitlab is None:
            raise ImportError(
                "python-gitlab is not installed. Install it with: pip install python-gitlab"
            )

        parsed = parse_gitlab_url(url)
        if not parsed:
            raise ValueError(f"Invalid GitLab URL: {url}")

        self.host = parsed['host']
        self.project_path = parsed['project_path']
        self.project_path_encoded = parsed['project_path_encoded']

        # Initialize GitLab client
        gitlab_url = f"https://{self.host}"
        self.gl = gitlab.Gitlab(gitlab_url, private_token=token)

        # Get project
        try:
            self.project: Project = self.gl.projects.get(self.project_path_encoded)
        except Exception as e:
            raise ValueError(f"Could not access GitLab project {self.project_path}: {e}")

    def get_pipelines(self, per_page: int = 10) -> List[ProjectPipeline]:
        """
        Get recent pipelines for the project.

        Args:
            per_page: Number of pipelines to retrieve (default 10, max 100)

        Returns:
            List of pipeline objects
        """
        return self.project.pipelines.list(per_page=min(per_page, 100), get_all=False)

    def get_pipeline(self, pipeline_id: int) -> ProjectPipeline:
        """
        Get a specific pipeline by ID.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Pipeline object
        """
        return self.project.pipelines.get(pipeline_id)

    def get_pipeline_jobs(self, pipeline_id: int) -> List[ProjectPipelineJob]:
        """
        Get all jobs for a specific pipeline.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            List of job objects
        """
        pipeline = self.get_pipeline(pipeline_id)
        return pipeline.jobs.list(get_all=True)

    def get_job(self, job_id: int):
        """
        Get a specific job by ID.

        Args:
            job_id: Job ID

        Returns:
            Job object
        """
        return self.project.jobs.get(job_id)

    def get_job_trace(self, job_id: int) -> str:
        """
        Get the trace (log) for a specific job.

        Args:
            job_id: Job ID

        Returns:
            Job trace as string
        """
        job = self.get_job(job_id)
        try:
            return job.trace().decode('utf-8')
        except Exception:
            # If decode fails, try returning as-is or empty string
            try:
                trace = job.trace()
                if isinstance(trace, bytes):
                    return trace.decode('utf-8', errors='replace')
                return str(trace) if trace else ""
            except Exception:
                return ""

    def get_pipeline_status(self, pipeline_id: int) -> Dict[str, Any]:
        """
        Get status information for a pipeline.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            Dict with status information including:
            - status: Pipeline status (created, waiting_for_resource, preparing, pending, running, success, failed, canceled, skipped, manual)
            - created_at: Creation timestamp
            - updated_at: Last update timestamp
            - web_url: Web URL to view the pipeline
        """
        pipeline = self.get_pipeline(pipeline_id)
        return {
            'status': pipeline.status,
            'created_at': pipeline.created_at,
            'updated_at': pipeline.updated_at,
            'web_url': pipeline.web_url,
            'ref': pipeline.ref,
            'sha': pipeline.sha,
        }

    def get_job_status(self, job_id: int) -> Dict[str, Any]:
        """
        Get status information for a job.

        Args:
            job_id: Job ID

        Returns:
            Dict with status information
        """
        job = self.get_job(job_id)
        return {
            'status': job.status,
            'stage': job.stage,
            'name': job.name,
            'created_at': job.created_at,
            'started_at': getattr(job, 'started_at', None),
            'finished_at': getattr(job, 'finished_at', None),
            'web_url': job.web_url,
            'failure_reason': getattr(job, 'failure_reason', None),
        }

    def download_job_log(self, job_id: int, output_path: Path) -> bool:
        """
        Download job log to a file.

        Args:
            job_id: Job ID
            output_path: Path to save the log file

        Returns:
            True if successful, False otherwise
        """
        try:
            trace = self.get_job_trace(job_id)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(trace, encoding='utf-8')
            return True
        except Exception:
            return False

    def get_failed_jobs(self, pipeline_id: int) -> List[Dict[str, Any]]:
        """
        Get all failed jobs for a pipeline.

        Args:
            pipeline_id: Pipeline ID

        Returns:
            List of dicts with failed job information
        """
        jobs = self.get_pipeline_jobs(pipeline_id)
        failed_jobs = []

        for job in jobs:
            if job.status == 'failed':
                failed_jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'stage': job.stage,
                    'status': job.status,
                    'web_url': job.web_url,
                    'failure_reason': getattr(job, 'failure_reason', None),
                })

        return failed_jobs
