# Quick Start

## Basic Usage

Navigate to any directory and run:

```bash
git-maestro
```

Or use it as a git plugin:

```bash
git maestro
```

## What Happens Next?

Git Maestro will:

1. **Detect the current state** of your directory
2. **Show you what's configured** and what's missing
3. **Present a menu** of applicable actions
4. **Execute your selected action**
5. **Refresh and show updated options**

## Example: Setting Up a New Project

### Step 1: Initialize a Git Repository

Start in an empty directory:

```bash
mkdir my-new-project
cd my-new-project
git-maestro
```

You'll see an option to **Initialize Git Repository**. Select it, and Git Maestro will run `git init`.

### Step 2: Add a README

After initialization, Git Maestro shows new options. Select **Add README.md** to create a basic README template.

### Step 3: Add a .gitignore

Select **Add .gitignore** and choose a template (Python, Node.js, or Generic).

### Step 4: Setup Remote Repository

Select **Setup Remote Repository** and choose your platform (GitHub, GitLab, or Azure DevOps). Git Maestro will:

- Prompt you for authentication if needed
- Create the remote repository
- Add it as your origin
- Push your initial commit

## Example: Using MCP for AI-Powered Workflows

Git Maestro includes an MCP (Model Context Protocol) server that enables AI assistants to autonomously manage your repository and monitor CI/CD.

### Start the MCP Server

```bash
git-maestro mcp
```

### Configure Claude Code

Add to your `mcp.json`:

```json
{
  "mcpServers": {
    "git-maestro": {
      "command": "git-maestro",
      "args": ["mcp"]
    }
  }
}
```

### AI-Powered Workflow Example

Once configured, an AI assistant can:

1. Make code changes and push them
2. Monitor GitHub Actions with `check_github_actions_job_status()`
3. Download failing job logs with `download_github_actions_job_logs()`
4. Analyze failures and apply fixes
5. Repeat until all tests pass

This creates a fully autonomous development loop.

## Available Actions

Git Maestro provides these context-aware actions:

- **Initialize Git Repository** - Run `git init` in non-git directories
- **Add README.md** - Create a README with basic project structure
- **Add .gitignore** - Add a .gitignore file (Python, Node.js, or Generic templates)
- **Setup Remote Repository** - Configure GitHub, GitLab, or Azure DevOps as remote origin

More actions are being added regularly!

## Next Steps

- [Learn about GitHub API integration](github-api.md)
- [Configure authentication and settings](configuration.md)
- [Understand data privacy](privacy.md)
