# Test Project for CI/CD Integration Testing

This is a minimal test project for testing git-maestro's integration with:
- GitHub Actions
- GitLab CI/CD
- Azure Pipelines

## Purpose

This project contains simple CI/CD configurations that can be pushed to GitHub, GitLab, or Azure DevOps to test git-maestro's ability to:
1. List pipeline/workflow runs
2. Get job details
3. Download logs
4. Check pipeline status

## Setup Using git-maestro

### For GitLab Testing

1. **Initialize the repository using git-maestro:**
   ```bash
   cd test-project
   git-maestro
   ```

2. **In the git-maestro TUI:**
   - Select "Initialize Git Repository" (if not already initialized)
   - Select "Create Initial Commit"
   - Select "Setup Remote Repository"
     - Choose GitLab
     - Enter your GitLab token when prompted
     - For the repository URL, use: `git@gitlab.com:yourgroup/yourproject.git`
   - Select "Create Repository on Remote"
     - This will create the project in the specified namespace/group
     - Choose visibility (public recommended for testing)
     - It will automatically push your code

3. **Trigger a pipeline:**
   The `.gitlab-ci.yml` will automatically trigger when you push

4. **Test the integration:**
   ```bash
   cd test-project
   git-maestro  # Select "Check GitLab Pipelines Status"

   # Or use the test script:
   python ../integration-tests/test_gitlab_live.py --project-url https://gitlab.com/yourgroup/yourproject
   ```

### For GitHub Testing

1. **Initialize using git-maestro:**
   ```bash
   cd test-project
   git-maestro
   ```

2. **In the git-maestro TUI:**
   - Select "Initialize Git Repository"
   - Select "Create Initial Commit"
   - Select "Setup Remote Repository"
     - Choose GitHub
     - Enter your GitHub token when prompted
     - For the repository URL, use: `git@github.com:yourusername/git-maestro-test.git`
   - Select "Create Repository on Remote"

3. The `.github/workflows/test.yml` will automatically trigger

### For Azure DevOps Testing

1. **Initialize using git-maestro:**
   ```bash
   cd test-project
   git-maestro
   ```

2. **In the git-maestro TUI:**
   - Select "Initialize Git Repository"
   - Select "Create Initial Commit"
   - Select "Setup Azure DevOps"
   - Follow the prompts to create the project

3. The `azure-pipelines.yml` can be used to create a pipeline in Azure DevOps

## CI/CD Configurations

Each configuration includes:
- A test stage with a simple job
- A build stage with another job
- One job that always succeeds
- One job that can be configured to fail (for testing error handling)

## Files

- `.gitlab-ci.yml` - GitLab CI/CD configuration
- `.github/workflows/test.yml` - GitHub Actions workflow
- `azure-pipelines.yml` - Azure Pipelines configuration
- `src/hello.py` - Simple Python script that gets "tested" and "built"
- `tests/test_hello.py` - Minimal test file
