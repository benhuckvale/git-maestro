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

## MCP Server

When running as an MCP server, Git Maestro exposes CI/CD tools for AI assistants.

### Platform Selection

Use flags to enable only the platforms you need:

```bash
git-maestro mcp                    # All platforms (13 tools)
git-maestro mcp --github           # GitHub Actions only (5 tools)
git-maestro mcp --azure            # Azure DevOps only (4 tools)
git-maestro mcp --gitlab           # GitLab CI/CD only (4 tools)
git-maestro mcp --github --azure   # Multiple platforms (9 tools)
```

**Why filter platforms?** Each tool definition consumes context window tokens when used with AI assistants. If you only use GitHub, there's no need to load Azure and GitLab tools.

### Configuration

Add to your `mcp.json`:

```json
{
  "mcpServers": {
    "git-maestro": {
      "command": "git-maestro",
      "args": ["mcp", "--github"]
    }
  }
}
```

### GitHub Actions Tools (`--github`)

#### `list_github_actions_runs(count)`
Get the most recent workflow runs.

**Parameters:**
- `count` (optional, default: 10) - Number of runs to retrieve

**Returns:** List of workflow runs with status, conclusion, and metadata

#### `get_github_actions_run_jobs(run_id)`
View job structure and details for a specific workflow run.

**Parameters:**
- `run_id` (required) - The workflow run ID

**Returns:** List of jobs with names, statuses, conclusions, and steps

#### `check_github_actions_job_status(run_id, job_id)`
Lightweight status check (fast polling without downloading logs).

**Parameters:**
- `run_id` (required) - The workflow run ID
- `job_id` (optional) - Specific job ID to check

**Returns:** Status summary (queued, in_progress, completed)

#### `download_github_actions_job_logs(run_id, job_id)`
Fetch logs for a specific job.

**Parameters:**
- `run_id` (required) - The workflow run ID
- `job_id` (required) - The job ID

**Returns:** Full job logs as text

##### `download_job_traces()`
Download all failed job logs from the latest workflow run.

**Returns:** Combined logs from all failed jobs

### Azure DevOps Tools (`--azure`)

#### `list_azure_pipelines_runs(count)`
Get the most recent pipeline runs.

**Parameters:**
- `count` (optional, default: 10) - Number of runs to retrieve

**Returns:** List of pipeline runs with status and metadata

#### `get_azure_pipelines_run_stages(pipeline_id, run_id)`
View stage structure and details for a specific pipeline run.

**Parameters:**
- `pipeline_id` (required) - The pipeline ID
- `run_id` (required) - The pipeline run ID

**Returns:** List of stages with names, statuses, and results

#### `check_azure_pipelines_run_status(pipeline_id, run_id, stage_id)`
Lightweight status check for a pipeline run or stage.

**Parameters:**
- `pipeline_id` (required) - The pipeline ID
- `run_id` (required) - The pipeline run ID
- `stage_id` (optional) - Specific stage ID to check

**Returns:** Status summary

#### `download_azure_pipelines_stage_logs(pipeline_id, run_id, stage_id)`
Fetch logs for a specific stage.

**Parameters:**
- `pipeline_id` (required) - The pipeline ID
- `run_id` (required) - The pipeline run ID
- `stage_id` (required) - The stage ID

**Returns:** Full stage logs as text

### GitLab CI/CD Tools (`--gitlab`)

#### `list_gitlab_pipelines_runs(count)`
Get the most recent pipeline runs.

**Parameters:**
- `count` (optional, default: 10) - Number of runs to retrieve

**Returns:** List of pipeline runs with status and metadata

#### `get_gitlab_pipelines_run_jobs(pipeline_id)`
View job structure and details for a specific pipeline.

**Parameters:**
- `pipeline_id` (required) - The pipeline ID

**Returns:** List of jobs with names, statuses, and stages

#### `check_gitlab_pipelines_run_status(pipeline_id, job_id)`
Lightweight status check for a pipeline or job.

**Parameters:**
- `pipeline_id` (required) - The pipeline ID
- `job_id` (optional) - Specific job ID to check

**Returns:** Status summary

#### `download_gitlab_pipelines_job_logs(pipeline_id, job_id)`
Fetch logs for a specific job.

**Parameters:**
- `pipeline_id` (required) - The pipeline ID
- `job_id` (required) - The job ID

**Returns:** Full job logs as text

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
