"""Helper functions for interactive selection using questionary."""

from typing import List, Optional

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
) -> Optional[int]:
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

    default_choice: Optional[str] = None
    if default_index is not None and 0 <= default_index < len(choices):
        default_choice = choices[default_index].title

    instruction = "Press enter to confirm or esc to cancel"

    try:
        result = questionary.select(
            text.strip(),
            choices=choices,
            default=default_choice,
            style=custom_style,
            instruction=instruction,
            use_shortcuts=False,
            use_arrow_keys=True,
        ).ask()

        return result if result is None else int(result)
    except (KeyboardInterrupt, EOFError):
        return None
