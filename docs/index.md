# Git Maestro

**A convenient TUI for managing git repositories with interactive menus**

## What is Git Maestro?

Git Maestro is a context-aware command-line interface that streamlines your git workflow by observing your repository state and presenting intelligent, actionable options. No more typing countless git commands or constantly switching to your browser—just select from a beautiful interactive menu and let Git Maestro handle the rest.

## What Problem Does It Solve?

Modern software development involves juggling multiple tasks:
- Setting up new repositories with proper configuration
- Managing remotes across GitHub, GitLab, and Azure DevOps
- Monitoring CI/CD pipelines and debugging failures
- Keeping repositories clean and organized

Git Maestro eliminates this friction by:
- **Detecting your current context** and showing only relevant actions
- **Automating repetitive tasks** like creating READMEs, .gitignore files, and remote repositories
- **Providing AI integration** through Model Context Protocol (MCP) for autonomous workflow automation
- **Offering a beautiful CLI experience** with rich formatting and interactive prompts

## Who Is It For?

Git Maestro is designed for:

- **Developers** who want to streamline their git workflow
- **DevOps engineers** managing multiple repositories
- **AI assistants** (via MCP) that need to autonomously manage git operations and monitor CI/CD
- **Teams** looking for consistent repository setup and management

## Key Features

- **Context-Aware Actions**: Only shows actions relevant to your current repository state
- **Beautiful CLI Interface**: Built with Rich and Prompt Toolkit for a polished experience
- **Modular Design**: Easy to extend with custom actions
- **Fast Setup**: Quickly initialize repos, add READMEs, .gitignore files, and remotes
- **Git Plugin Support**: Can be called as `git maestro` after installation
- **MCP Integration**: Seamlessly works with Model Context Protocol for AI-powered workflows

## Quick Links

- [Installation Guide](installation.md)
- [Quick Start](quickstart.md)
- [GitHub API Integration](github-api.md)
- [Configuration](configuration.md)
- [Privacy Policy](privacy.md)

## Getting Started

Install Git Maestro with pip:

```bash
pip install git-maestro
```

Then run it in any directory:

```bash
git-maestro
```

Or use it as a git plugin:

```bash
git maestro
```

## License

Git Maestro is released under the MIT License.
