# Quick Start - Setting up the Test Project with git-maestro

This guide shows you how to use git-maestro itself to set up the test project on GitLab.

## Prerequisites

1. GitLab personal access token with `api` scope
   - Get one at: https://gitlab.com/-/user_settings/personal_access_tokens
2. git-maestro installed and working

## Steps

### 1. Store your GitLab token

```bash
mkdir -p ~/.config/git-maestro
echo "gitlab=YOUR_TOKEN_HERE" >> ~/.config/git-maestro/tokens.conf
chmod 600 ~/.config/git-maestro/tokens.conf
```

### 2. Navigate to the test-project directory

```bash
cd test-project
```

### 3. Run git-maestro

```bash
git-maestro
```

### 4. Follow the interactive prompts

The git-maestro TUI will guide you through:

1. **Initialize Git Repository** - Creates a git repository
2. **Create Initial Commit** - Commits all the test files
3. **Setup Remote Repository** - Configure GitLab remote
   - Provider: Choose **GitLab**
   - It will use the token from your config file
   - Repository URL: `git@gitlab.com:yourgroup/yourproject.git`
     (Replace `yourgroup/yourproject` with your actual GitLab group and desired project name)

4. **Create Repository on Remote** - Creates the project on GitLab
   - Visibility: Choose **public** for testing
   - Description: Auto-filled from README.md
   - It will automatically push your code

### 5. Verify the pipeline

1. Visit: `https://gitlab.com/yourgroup/yourproject/-/pipelines`
2. You should see a pipeline running automatically (triggered by `.gitlab-ci.yml`)

### 6. Test git-maestro GitLab integration

**Option A: Using the TUI**
```bash
git-maestro
# Select "Check GitLab Pipelines Status"
```

**Option B: Using the test script**
```bash
python ../integration-tests/test_gitlab_live.py --project-url https://gitlab.com/yourgroup/yourproject
```

**Option C: Using MCP tools**
```bash
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"list_gitlab_pipelines_runs","arguments":{"count":10}},"id":1}' | git-maestro mcp
```

## Expected Results

After following these steps, you should have:

- ✓ A GitLab project at your specified URL
- ✓ An active CI/CD pipeline with 4 jobs (test-job, lint-job, build-job, package-job)
- ✓ Ability to list pipelines, view jobs, download logs via git-maestro
- ✓ Working demonstration of all GitLab integration features

## Troubleshooting

**"Repository already exists"**
- If the project already exists, git-maestro will detect it and offer to just push
- Or manually delete the existing project on GitLab and try again

**"Permission denied"**
- Make sure your token has the `api` scope
- Verify you have access to the specified namespace/group

**"No pipelines found"**
- Wait a moment after pushing - pipelines take a few seconds to start
- Check the project's CI/CD settings are enabled
- Verify `.gitlab-ci.yml` was pushed correctly

## Customizing the Test

To test failure scenarios:

1. Edit `.gitlab-ci.yml`
2. Set `FAIL_TEST: "true"` in the variables section
3. Commit and push: `git add . && git commit -m "Test failure" && git push`
4. The test-job will fail, allowing you to test error handling in git-maestro
