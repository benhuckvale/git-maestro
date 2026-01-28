# Contributing to Git Maestro

Thanks for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/benhuckvale/git-maestro.git
cd git-maestro
pdm install -d
```

## Running Locally

```bash
pdm run git-maestro
```

## Code Quality

Before submitting a PR add/amend relevant tests and:

```bash
pdm run black .
pdm run ruff check .
pdm run pytest
```

## Adding a New Action

1. Create a new file in `git_maestro/actions/`
2. Inherit from the `Action` base class
3. Implement `is_applicable()` and `execute()` methods
4. Register it in `git_maestro/actions/__init__.py` and `git_maestro/cli.py`

See existing actions for examples.

## Changelog

We maintain a [CHANGELOG.md](CHANGELOG.md). When making changes:

- Add an entry under `[Unreleased]` for user-visible changes
- Use the appropriate section: Added, Changed, Deprecated, Removed, Fixed, Security
- Internal refactors are fine to include if they're significant standalone changes
- Minor refactors that are part of a feature don't need separate mention

## Use of AI-driven coding

### Self-modifiable MCP Guard

When using an AI coding assistant on this repo, don't let it use the in-development
git-maestro as its MCP server - that creates a self-modification risk. Use a
separately installed (stable) git-maestro instead.

### Code Quality

AI assistants tend toward:
- Over-engineering and unnecessary abstraction
- Adding dependencies that aren't needed
- Verbose code where concise code would do

Review generated code with these in mind. Keep changes minimal and focused.
