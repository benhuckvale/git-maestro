"""Helper functions for interactive selection using questionary."""

from typing import List, Optional, Sequence, Set, Union

import questionary
from questionary import Choice, Style


# Custom style that works well with rich console
custom_style = Style(
    [
        ("qmark", "fg:#00aaaa bold"),  # Question mark
        ("question", "bold"),  # Question text
        ("answer", "fg:#00aaaa bold"),  # Selected answer in history
        ("pointer", "fg:#00aaaa bold"),  # Pointer arrow
        ("highlighted", "fg:#00aaaa bold"),  # Highlighted text
        ("selected", "fg:#00aaaa bold"),  # Selected (checked) items
        ("separator", "fg:#6c6c6c"),
        ("instruction", "fg:#6c6c6c"),
        ("text", ""),
        ("disabled", "fg:#858585 italic"),
    ]
)


def select_number_from_menu(
    title: str,
    text: str,
    options: List[str],
    default_index: Optional[int] = 0,
    show_numbers: bool = True,
    extra_choices: Optional[List[Choice]] = None,
    enable_shortcuts: bool = False,
    instruction: Optional[str] = None,
    instant_values: Optional[Sequence[Union[int, str]]] = None,
) -> Optional[Union[int, str]]:
    """
    Display an inline selection menu for numbered options.

    Users can navigate with arrow keys and select with Enter.
    The menu stays in the terminal scrollback (doesn't clear screen).

    Args:
        title: Title shown above the menu (currently unused, kept for compatibility)
        text: Question text shown above the options
        options: List of option labels (will be numbered automatically)
        default_index: Index of default selection (0-based)

    Returns:
        The 1-based number of the selected option, or None if cancelled

    Example:
        choice = select_number_from_menu(
            title="Initial Commit",
            text="What should be included in the initial commit?",
            options=[
                "All existing files",
                "Only README and .gitignore (if they exist)",
                "Create an empty commit",
            ],
            default_index=0
        )
        # Returns 1, 2, 3, or None
    """
    if not options:
        return None

    choices: List[Choice] = []
    for index, label in enumerate(options):
        display_text = f"{index + 1}. {label}" if show_numbers else label
        choices.append(Choice(title=display_text, value=index + 1))

    if extra_choices:
        choices.extend(extra_choices)

    default_choice: Optional[int] = None
    if default_index is not None and 0 <= default_index < len(options):
        default_choice = choices[default_index].value  # type: ignore[attr-defined]

    instruction_text = instruction or "Press enter to confirm or esc to cancel"

    question = questionary.select(
        text.strip(),
        choices=choices,
        default=default_choice,
        style=custom_style,
        instruction=instruction_text,
        use_shortcuts=enable_shortcuts,
        use_arrow_keys=True,
    )

    # Register instant shortcut handlers so specific keys can act immediately
    if instant_values:
        instant_set: Set[Union[int, str]] = set(instant_values)
        bindings = question.application.key_bindings

        for choice in choices:
            if choice.value not in instant_set:
                continue
            shortcut = choice.shortcut_key
            if not isinstance(shortcut, str):
                continue

            def _register(binding_key: str, return_value: Union[int, str]):
                @bindings.add(binding_key, eager=True)
                def _instant_choice(event):
                    event.app.exit(result=return_value)

            _register(shortcut, choice.value)
            if len(shortcut) == 1 and shortcut.isalpha():
                _register(shortcut.upper(), choice.value)

    try:
        result = question.ask()
        return result
    except (KeyboardInterrupt, EOFError):
        return None


def prompt_text(message: str, default: Optional[str] = "") -> Optional[str]:
    """Prompt the user for freeform text input."""
    try:
        return questionary.text(
            message.strip(),
            default=default or "",
            style=custom_style,
        ).ask()
    except (KeyboardInterrupt, EOFError):
        return None


def prompt_password(message: str) -> Optional[str]:
    """Prompt the user for a secret/password value."""
    try:
        return questionary.password(
            message.strip(),
            style=custom_style,
        ).ask()
    except (KeyboardInterrupt, EOFError):
        return None


def prompt_confirm(message: str, default: bool = True) -> Optional[bool]:
    """Prompt the user for a yes/no confirmation."""
    try:
        return questionary.confirm(
            message.strip(),
            default=default,
            style=custom_style,
        ).ask()
    except (KeyboardInterrupt, EOFError):
        return None
