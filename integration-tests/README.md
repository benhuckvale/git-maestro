# Integration Tests

This directory contains integration tests that verify git-maestro works against real external services.

## Difference from Unit Tests

| Aspect | Unit Tests (`tests/`) | Integration Tests (`integration-tests/`) |
|--------|----------------------|------------------------------------------|
| **External APIs** | Mocked | Real API calls |
| **Credentials** | Not required | Requires tokens/credentials |
| **Speed** | Fast (< 1 second) | Slower (network dependent) |
| **Isolation** | Fully isolated | Depends on external services |
| **When to run** | Always (CI/CD) | Manual/optional (requires setup) |

## GitLab Integration Tests

**File:** `test_gitlab_live.py`

Tests the GitLab integration against a real GitLab instance.

### Prerequisites

1. GitLab personal access token with `api` scope
2. A GitLab project with at least one CI/CD pipeline

### Setup

```bash
# Store your token
mkdir -p ~/.config/git-maestro
echo "gitlab=YOUR_TOKEN" >> ~/.config/git-maestro/tokens.conf
chmod 600 ~/.config/git-maestro/tokens.conf
```

### Running

```bash
# Using token from config
python integration-tests/test_gitlab_live.py --project-url https://gitlab.com/yourgroup/yourproject

# Or with explicit token
python integration-tests/test_gitlab_live.py --token YOUR_TOKEN --project-url https://gitlab.com/yourgroup/yourproject
```

### What It Tests

1. URL parsing for different GitLab URL formats
2. Client initialization and authentication
3. Listing recent pipelines
4. Getting pipeline details
5. Retrieving job information
6. Downloading job logs
7. Checking pipeline/job status
8. Listing failed jobs

## Adding New Integration Tests

When adding integration tests for other services:

1. Create a new test file: `test_<service>_live.py`
2. Follow the same pattern as `test_gitlab_live.py`
3. Document prerequisites and setup in this README
4. Make tests optional (don't fail if credentials are missing)
5. Use argparse for configuration (avoid hardcoding URLs/credentials)

## CI/CD Considerations

Integration tests should **not** run automatically in CI/CD because they:
- Require external credentials
- Depend on external service availability
- May have rate limits
- Are slower than unit tests

Run them manually when:
- Verifying a new integration works
- Testing against a specific environment
- Debugging production issues
- Before major releases
