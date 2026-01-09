# GitHub API Integration

Git Maestro integrates with GitHub, GitLab, and Azure DevOps APIs to automate repository management and CI/CD monitoring.

## GitHub API

### Required Scopes

To create repositories and access GitHub Actions data, Git Maestro requires a Personal Access Token (PAT) with these scopes:

- `repo` - Full control of private repositories (includes public repos)
- `workflow` - Update GitHub Action workflows (for accessing Actions data)

### Creating a GitHub Personal Access Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Give it a descriptive name like "Git Maestro"
4. Select the following scopes:
   - `repo` (all sub-scopes)
   - `workflow`
5. Click **Generate token**
6. Copy the token immediately (you won't see it again)

### Authentication Method

Git Maestro uses **Personal Access Token (PAT)** authentication:

```bash
# Git Maestro will prompt for your token when needed
git-maestro
```

Your token is stored securely in `~/.config/git-maestro/tokens.conf` and never committed to any repository.

### Available GitHub Operations

- **Create Repository**: Create a new GitHub repository (public or private)
- **List Workflow Runs**: Get recent GitHub Actions runs
- **Get Job Details**: View job structure and status for a workflow run
- **Check Job Status**: Lightweight polling for CI/CD status
- **Download Logs**: Fetch logs for specific jobs or all failed jobs

## GitLab API

### Required Scopes

For GitLab, you need a Personal Access Token with:

- `api` - Full API access

### Creating a GitLab Personal Access Token

1. Go to [GitLab Settings → Access Tokens](https://gitlab.com/-/profile/personal_access_tokens)
2. Enter a name like "Git Maestro"
3. Select scope: `api`
4. Click **Create personal access token**
5. Copy the token immediately

### Authentication

Git Maestro will prompt for your GitLab token when you select GitLab as your remote provider.

## Azure DevOps API

### Required Access

For Azure DevOps, you need a Personal Access Token with:

- `Code` - Read & Write
- `Build` - Read & Execute

### Creating an Azure DevOps Personal Access Token

1. Go to [Azure DevOps → User Settings → Personal Access Tokens](https://dev.azure.com)
2. Click **New Token**
3. Select scopes:
   - Code: Read & Write
   - Build: Read & Execute
4. Click **Create**
5. Copy the token immediately

## MCP Tools for GitHub Actions

When running as an MCP server, Git Maestro exposes these tools for AI assistants:

### `list_github_actions_runs(count)`
Get the most recent workflow runs.

**Parameters:**
- `count` (optional, default: 10) - Number of runs to retrieve

**Returns:** List of workflow runs with status, conclusion, and metadata

### `get_github_actions_run_jobs(run_id)`
View job structure and details for a specific workflow run.

**Parameters:**
- `run_id` (required) - The workflow run ID

**Returns:** List of jobs with names, statuses, conclusions, and steps

### `check_github_actions_job_status(run_id, job_id)`
Lightweight status check (fast polling without downloading logs).

**Parameters:**
- `run_id` (required) - The workflow run ID
- `job_id` (optional) - Specific job ID to check

**Returns:** Status summary (queued, in_progress, completed)

### `download_github_actions_job_logs(run_id, job_id)`
Fetch logs for a specific job.

**Parameters:**
- `run_id` (required) - The workflow run ID
- `job_id` (required) - The job ID

**Returns:** Full job logs as text

### `download_job_traces()`
Download all failed job logs from the latest workflow run.

**Returns:** Combined logs from all failed jobs

## Rate Limiting

GitHub API has rate limits:
- **Authenticated requests**: 5,000 requests/hour
- **Unauthenticated requests**: 60 requests/hour

Git Maestro uses authenticated requests for all API calls to maximize your rate limit.

## Security Best Practices

- Store tokens in `~/.config/git-maestro/tokens.conf` (outside repositories)
- Never commit tokens to version control
- Use fine-grained tokens when possible
- Rotate tokens regularly
- Revoke tokens you no longer use

## Next Steps

- [Configure Git Maestro](configuration.md)
- [Review privacy policy](privacy.md)
- [Quick start guide](quickstart.md)
