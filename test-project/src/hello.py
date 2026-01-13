#!/usr/bin/env python3
"""
Simple hello world application for testing CI/CD integrations.
"""


def greet(name="World"):
    """Return a greeting message."""
    return f"Hello, {name}!"


def main():
    """Main entry point."""
    message = greet()
    print(message)
    print("This is a test application for git-maestro CI/CD integration testing.")
    return 0


if __name__ == "__main__":
    exit(main())
