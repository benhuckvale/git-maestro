# Git Maestro Tests

Comprehensive test suite for Git Maestro.

## Running Tests

```bash
# Run all tests
pdm run pytest

# Run with verbose output
pdm run pytest -v

# Run specific test file
pdm run pytest tests/test_state.py

# Run specific test
pdm run pytest tests/test_state.py::test_git_repo_with_commits

# Run with coverage
pdm run pytest --cov=git_maestro --cov-report=html
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Pytest fixtures and configuration
├── test_state.py         # Repository state detection tests
├── test_ssh_config.py    # SSH configuration detection tests
├── test_actions.py       # Action applicability and behavior tests
└── test_cli.py           # CLI functionality tests
```

## Test Coverage

### State Detection (`test_state.py`)
- ✅ Non-git directory detection
- ✅ Empty git repository detection
- ✅ Repository with commits
- ✅ README file detection
- ✅ .gitignore detection
- ✅ Remote repository detection
- ✅ Untracked files detection
- ✅ Modified files detection
- ✅ State refresh functionality
- ✅ Repos with no commits (edge case)

### SSH Configuration (`test_ssh_config.py`)
- ✅ No SSH keys scenario
- ✅ Default key detection (id_rsa, id_ed25519, etc.)
- ✅ SSH config file parsing
- ✅ Public key content retrieval
- ✅ Missing public key handling
- ✅ ssh -G command detection
- ✅ Fallback when ssh command unavailable

### Actions (`test_actions.py`)
- ✅ InitRepoAction applicability
- ✅ AddReadmeAction applicability
- ✅ AddGitignoreAction applicability
- ✅ Action attributes validation
- ✅ Display name formatting

### CLI (`test_cli.py`)
- ✅ Action loading
- ✅ Action uniqueness

## Fixtures

Common fixtures available in `conftest.py`:

- `temp_dir` - Temporary directory for tests
- `git_repo` - Empty git repository
- `git_repo_with_commits` - Git repository with initial commit
- `git_repo_with_remote` - Git repository with remote configured
- `git_repo_no_commits` - Git repository with no commits

## Adding New Tests

1. Create a new test file in `tests/` with the prefix `test_`
2. Use existing fixtures from `conftest.py`
3. Follow the naming convention: `test_<description>`
4. Run tests to ensure they pass

Example:

```python
def test_my_feature(git_repo_with_commits):
    """Test description here."""
    repo, temp_dir = git_repo_with_commits

    # Your test code
    assert something is True
```
