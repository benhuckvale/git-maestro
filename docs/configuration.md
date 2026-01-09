# Configuration

## Token Storage

Git Maestro stores authentication tokens securely in your home directory:

```
~/.config/git-maestro/tokens.conf
```

This file is automatically created when you first authenticate with GitHub, GitLab, or Azure DevOps.

**Important**: This file is outside your repository and should never be committed to version control.

## Environment Variables

Git Maestro supports the following environment variables:

### GitHub Token

Environment variable: `GITHUB_TOKEN`

If set, Git Maestro will use this token for GitHub API authentication instead of prompting you.

```bash
export GITHUB_TOKEN="<your-github-token>"
git-maestro
```

### GitLab Token

Environment variable: `GITLAB_TOKEN`

If set, Git Maestro will use this token for GitLab API authentication.

```bash
export GITLAB_TOKEN="<your-gitlab-token>"
git-maestro
```

### Azure DevOps Token

Environment variable: `AZURE_DEVOPS_PAT`

If set, Git Maestro will use this token for Azure DevOps API authentication.

```bash
export AZURE_DEVOPS_PAT="<your-azure-token>"
git-maestro
```

## Configuration Files

Currently, Git Maestro stores minimal configuration:

- **Token storage**: `~/.config/git-maestro/tokens.conf`

Future versions may add support for:
- Default repository visibility (public/private)
- Preferred remote provider
- Custom action configurations

## MCP Server Configuration

To use Git Maestro as an MCP server with Claude Code, add this to your `mcp.json`:

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

Or with a custom Python environment:

```json
{
  "mcpServers": {
    "git-maestro": {
      "command": "/path/to/your/venv/bin/git-maestro",
      "args": ["mcp"]
    }
  }
}
```

## Security Best Practices

### Token Management

1. **Never commit tokens** to version control
2. **Rotate tokens regularly** (every 90 days recommended)
3. **Use fine-grained tokens** when available
4. **Revoke unused tokens** immediately
5. **Store tokens securely** (use environment variables or secure config files)

### Repository Security

Git Maestro's default `.gitignore` templates block common sensitive files:
- `*.token`
- `.env`
- `credentials.json`
- `secrets.*`
- `~/.config/git-maestro/tokens.conf`

### Permissions

Ensure your token storage directory has restrictive permissions:

```bash
chmod 700 ~/.config/git-maestro
chmod 600 ~/.config/git-maestro/tokens.conf
```

## Troubleshooting

### Token Not Saved

If Git Maestro keeps prompting for your token:

1. Check that `~/.config/git-maestro/` exists and is writable
2. Verify file permissions allow writing
3. Check for errors in the console output

### API Rate Limiting

If you hit GitHub's rate limit:

1. Verify you're using an authenticated token
2. Check your rate limit status: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`
3. Wait for the limit to reset (shown in the response)

### MCP Server Not Connecting

If Claude Code can't connect to the MCP server:

1. Verify `git-maestro mcp` runs successfully in your terminal
2. Check that the path in `mcp.json` is correct
3. Ensure Git Maestro is installed in the environment Claude Code is using

## Next Steps

- [Learn about GitHub API integration](github-api.md)
- [Review privacy policy](privacy.md)
- [Quick start guide](quickstart.md)
