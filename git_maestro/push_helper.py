"""Shared push helper module for selective remote push operations."""

from rich.console import Console

from git_maestro.state import RepoState
from git_maestro.selection_helper import prompt_text, select_number_from_menu

console = Console()


def push_to_remote(state: RepoState, origin) -> bool:
    """
    Push to remote repository with selective options.

    Presents an interactive menu with 4 options:
    1. Push current branch with set-upstream (default, backward compatible)
    2. Push a specific branch
    3. Push specific commit from branch history
    4. Skip - don't push now

    Args:
        state: Repository state object
        origin: Git remote object

    Returns:
        bool: True if successful or skipped, False if failed
    """
    # Display context
    console.print("\n[yellow]What would you like to push to the remote?[/yellow]")

    try:
        current_branch = state.repo.active_branch.name
        console.print(f"[dim]Current branch: {current_branch}[/dim]")
    except (TypeError, AttributeError):
        # Detached HEAD or other edge case
        try:
            current_branch = state.repo.head.commit.hexsha[:7]
            console.print(
                f"[dim]Current commit (detached HEAD): {current_branch}[/dim]"
            )
        except Exception:
            current_branch = "unknown"
            console.print("[dim]Current branch: unknown[/dim]")

    # Show commit count for context
    try:
        commits = list(state.repo.iter_commits(max_count=5))
        if commits:
            console.print(
                f"[dim]Recent commits: {len(commits)} shown (may be more)[/dim]"
            )
    except Exception:
        pass

    # Present options
    choice = select_number_from_menu(
        title="Push to Remote",
        text="What would you like to push to the remote?",
        options=[
            f"Push current branch ({current_branch}) with set-upstream",
            "Push a different branch",
            "Push specific commit from branch history",
            "Skip - don't push now",
        ],
        default_index=0,
    )

    # Handle option 1: Current branch (default behavior)
    if choice == 1:
        return _push_current_branch(state, origin, current_branch)

    # Handle option 2: Specific branch
    elif choice == 2:
        return _push_specific_branch(state, origin)

    # Handle option 3: Specific commit
    elif choice == 3:
        return _push_specific_commit(state, origin)

    # Handle option 4 or cancelled: Skip
    else:
        console.print("[yellow]Skipping push. You can push later with:[/yellow]")
        console.print(f"[dim]  git push -u origin {current_branch}[/dim]")
        return True


def _push_current_branch(state: RepoState, origin, branch: str) -> bool:
    """
    Push current branch with set-upstream (option 1).

    This maintains the existing default behavior for backward compatibility.

    Args:
        state: Repository state object
        origin: Git remote object
        branch: Branch name to push

    Returns:
        bool: True if successful, False if failed
    """
    try:
        console.print(f"[cyan]Pushing {branch} to remote...[/cyan]")
        origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
        console.print("[bold green]✓ Pushed to remote successfully![/bold green]")
        return True
    except Exception as push_error:
        console.print(f"[bold red]✗ Push failed: {push_error}[/bold red]")
        console.print(
            f"[yellow]You can push manually with: git push -u origin {branch}[/yellow]"
        )
        return False


def _push_specific_branch(state: RepoState, origin) -> bool:
    """
    Push a specific branch selected by user (option 2).

    Lists all available branches and lets user select one to push.
    Optionally sets upstream tracking.

    Args:
        state: Repository state object
        origin: Git remote object

    Returns:
        bool: True if successful, False if failed or no selection
    """
    # List available branches
    try:
        branches = [str(branch) for branch in state.repo.branches]
    except Exception as e:
        console.print(f"[yellow]Could not list branches: {e}[/yellow]")
        return False

    if not branches:
        console.print("[yellow]No branches available[/yellow]")
        return False

    # Get user selection
    choice = select_number_from_menu(
        title="Select Branch",
        text="Select a branch to push:",
        options=branches,
        default_index=0,
    )

    if choice is None:
        console.print("[yellow]Cancelled[/yellow]")
        return False

    selected_branch = branches[choice - 1]

    # Ask about set-upstream
    set_upstream_choice = select_number_from_menu(
        title="Set Upstream",
        text=f"Set {selected_branch} as upstream tracking branch?",
        options=["Yes", "No"],
        default_index=0,
    )

    if set_upstream_choice is None:
        console.print("[yellow]Cancelled[/yellow]")
        return False

    set_upstream = set_upstream_choice == 1

    try:
        # Push
        console.print(f"[cyan]Pushing {selected_branch} to remote...[/cyan]")
        if set_upstream:
            origin.push(
                refspec=f"{selected_branch}:{selected_branch}", set_upstream=True
            )
        else:
            origin.push(refspec=f"{selected_branch}:{selected_branch}")

        console.print("[bold green]✓ Pushed to remote successfully![/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]✗ Push failed: {e}[/bold red]")
        return False


def _push_specific_commit(state: RepoState, origin) -> bool:
    """
    Push a specific commit from branch history (option 3).

    Shows commits on a branch, lets user select one, and pushes the branch
    up to that commit. Useful for pushing only early commits, not latest work.

    Args:
        state: Repository state object
        origin: Git remote object

    Returns:
        bool: True if successful, False if failed or no selection
    """
    # Get current branch as default
    try:
        current_branch = state.repo.active_branch.name
    except Exception:
        current_branch = "main"

    # Ask which branch to view commits from
    console.print("\n[yellow]Which branch's commits would you like to view?[/yellow]")
    branch_to_view = (
        prompt_text(
            f"Branch name (default: {current_branch}):",
            default=current_branch,
        )
        or current_branch
    )

    # Show commits on that branch
    console.print(f"\n[cyan]Recent commits on {branch_to_view}:[/cyan]")
    try:
        # Get commits on the specified branch
        commits = list(state.repo.iter_commits(branch_to_view, max_count=20))

        if not commits:
            console.print("[yellow]No commits found on this branch[/yellow]")
            return False

        # Display commits with numbers
        for i, commit in enumerate(commits, 1):
            short_sha = commit.hexsha[:7]
            message = commit.message.split("\n")[0][:60]
            author = commit.author.name
            # Format date
            commit_date = commit.committed_datetime.strftime("%Y-%m-%d")
            console.print(f"  {i}. [dim]{short_sha}[/dim] {message}")
            console.print(f"      [dim]{author} - {commit_date}[/dim]")

        if len(commits) == 20:
            console.print("\n[dim]  (showing first 20 commits)[/dim]")
    except Exception as e:
        console.print(f"[yellow]Could not list commits: {e}[/yellow]")
        return False

    # Get commit selection
    console.print("\n[yellow]Select a commit to push (by number or SHA):[/yellow]")
    console.print(
        "[dim]The branch will be pushed up to this commit (creating partial history on remote)[/dim]"
    )
    selection = prompt_text("Commit (number or SHA):", default="")

    if not selection:
        console.print("[yellow]No commit specified, skipping[/yellow]")
        return False

    # Parse selection - could be number or SHA
    commit_sha = None
    try:
        # Try as number first
        idx = int(selection) - 1
        if 0 <= idx < len(commits):
            commit_sha = commits[idx].hexsha
        else:
            console.print("[yellow]Invalid selection: number out of range[/yellow]")
            return False
    except ValueError:
        # Not a number, treat as SHA
        commit_sha = selection

    # Get target branch name for the push
    console.print(
        "\n[yellow]Which remote branch should this commit be pushed to?[/yellow]"
    )
    target_branch = (
        prompt_text("Target branch:", default=branch_to_view) or branch_to_view
    )

    # Ask about set-upstream
    set_upstream_choice = select_number_from_menu(
        title="Set Upstream",
        text=f"Set {target_branch} as upstream tracking branch?",
        options=["Yes", "No"],
        default_index=1,  # Default to No
    )

    if set_upstream_choice is None:
        console.print("[yellow]Cancelled[/yellow]")
        return False

    set_upstream = set_upstream_choice == 1

    try:
        # Push specific commit to branch
        console.print(
            f"[cyan]Pushing commit {commit_sha[:7]} to {target_branch}...[/cyan]"
        )

        if set_upstream:
            origin.push(
                refspec=f"{commit_sha}:refs/heads/{target_branch}", set_upstream=True
            )
        else:
            origin.push(refspec=f"{commit_sha}:refs/heads/{target_branch}")

        console.print(
            "[bold green]✓ Pushed commit to remote successfully![/bold green]"
        )

        if not set_upstream:
            console.print("[yellow]Note: To set upstream tracking, run:[/yellow]")
            console.print(
                f"[dim]  git branch --set-upstream-to=origin/{target_branch}[/dim]"
            )

        return True
    except Exception as push_error:
        console.print(f"[bold red]✗ Push failed: {push_error}[/bold red]")
        console.print("[yellow]You can push manually with:[/yellow]")
        console.print(
            f"[dim]  git push origin {commit_sha}:refs/heads/{target_branch}[/dim]"
        )
        return False
