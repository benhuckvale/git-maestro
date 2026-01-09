# Installation

## Requirements

- Python >= 3.9
- Git installed on your system

## Install from PyPI

The easiest way to install Git Maestro is via pip:

```bash
pip install git-maestro
```

This will install the `git-maestro` command globally, making it available from any directory.

## Install as Git Plugin

After installation, Git Maestro can be used as a git plugin:

```bash
git maestro
```

This works automatically because git looks for executables named `git-*` in your PATH.

## Development Installation

If you want to contribute to Git Maestro or modify it for your needs:

### Using PDM (Recommended)

```bash
# Clone the repository
git clone https://github.com/benhuckvale/git-maestro.git
cd git-maestro

# Install dependencies with PDM
pdm install

# Run in development mode
pdm run git-maestro
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/benhuckvale/git-maestro.git
cd git-maestro

# Install in editable mode
pip install -e .

# Run from anywhere
git-maestro
```

## Verify Installation

After installation, verify it works:

```bash
git-maestro --help
```

You should see the help message with available commands and options.

## Dependencies

Git Maestro automatically installs these dependencies:

- `rich>=13.7.0` - Terminal formatting and styling
- `prompt-toolkit>=3.0.43` - Interactive prompts
- `gitpython>=3.1.40` - Git repository interaction
- `PyGithub>=2.1.1` - GitHub API integration
- `python-gitlab>=4.4.0` - GitLab API integration
- `azure-devops>=7.1.0b4` - Azure DevOps API integration

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configure GitHub/GitLab Access](github-api.md)
- [Learn About Privacy](privacy.md)
