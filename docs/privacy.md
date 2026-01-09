# Privacy Policy

## Overview

Git Maestro is designed with privacy in mind. This document explains what data is accessed, what is stored, and what is never persisted.

## What Data Is Accessed

Git Maestro accesses the following data to function:

### Local Repository Data
- Git repository status and configuration
- Local branch information
- Remote URLs and configurations
- File listings (to detect README, .gitignore, etc.)

### Remote API Data (GitHub, GitLab, Azure DevOps)
When you use remote repository features, Git Maestro accesses:
- Your repository list
- Repository metadata (name, visibility, URL)
- GitHub Actions workflow runs and job statuses
- Job logs for CI/CD monitoring

### Authentication Tokens
- Personal Access Tokens (PATs) for GitHub, GitLab, and Azure DevOps
- Tokens are stored locally only (see below)

## What Data Is Stored

Git Maestro stores minimal data on your local system:

### Authentication Tokens
**Location**: `~/.config/git-maestro/tokens.conf`

This file contains your API tokens for GitHub, GitLab, and Azure DevOps.

**Security measures**:
- Stored outside your repository (never committed)
- File permissions should be `600` (read/write for owner only)
- Tokens are stored in plain text locally (you are responsible for filesystem security)

### No Other Persistent Storage
Git Maestro does **not** store:
- Repository data
- Workflow logs
- User preferences
- Usage analytics
- Telemetry data

## What Data Is Never Persisted

The following data is **only** used in memory during execution and **never** written to disk:

- Repository file contents
- Git commit history
- Workflow run details
- Job logs (unless you explicitly save them)
- API responses

## Data Transmission

### API Calls
Git Maestro makes direct API calls to:
- `api.github.com` (GitHub)
- `gitlab.com` or your GitLab instance (GitLab)
- `dev.azure.com` (Azure DevOps)

**All API calls use HTTPS** for encryption in transit.

### No Third-Party Analytics
Git Maestro does **not**:
- Send telemetry to any third party
- Track usage statistics
- Report errors to external services
- Phone home for updates

## MCP Server Privacy

When running as an MCP (Model Context Protocol) server, Git Maestro:

- Exposes tools to the connected AI assistant (e.g., Claude Code)
- All data accessed through MCP tools follows the same privacy rules above
- The AI assistant may see repository data and logs **you explicitly request**
- No data is sent to third parties beyond the AI service you're using

## Token Security

### Your Responsibility
- Protect your `~/.config/git-maestro/tokens.conf` file
- Use filesystem permissions to restrict access
- Rotate tokens regularly
- Revoke tokens when no longer needed

### Our Commitment
- We never transmit your tokens to any server except the API they're intended for
- Tokens are never logged or included in error messages
- We use tokens only for authenticated API calls you initiate

## GitHub Developer Program Compliance

Git Maestro is suitable for the GitHub Developer Program because:

1. **Transparent API usage**: All API calls are documented and user-initiated
2. **Secure token handling**: Tokens are stored locally and never shared
3. **No data harvesting**: We don't collect or store user data beyond what's necessary
4. **Clear privacy policy**: This document explains all data access and storage
5. **Open source**: All code is available for review

## Data Deletion

To remove all data stored by Git Maestro:

```bash
rm -rf ~/.config/git-maestro
```

This deletes all stored tokens. You can then revoke the tokens from:
- [GitHub Personal Access Tokens](https://github.com/settings/tokens)
- [GitLab Access Tokens](https://gitlab.com/-/profile/personal_access_tokens)
- [Azure DevOps Personal Access Tokens](https://dev.azure.com)

## Changes to This Policy

This privacy policy may be updated as Git Maestro evolves. Check the [repository](https://github.com/benhuckvale/git-maestro) for the latest version.

## Contact

For privacy concerns or questions, please open an issue on the [GitHub repository](https://github.com/benhuckvale/git-maestro/issues).

## Summary

**Accessed**: Local git data, remote API data (when you request it), your API tokens

**Stored**: API tokens only (in `~/.config/git-maestro/tokens.conf`)

**Never Persisted**: Repository contents, logs, workflow data, analytics, telemetry
