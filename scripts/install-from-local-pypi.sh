#!/bin/bash
# Install git-maestro from the local PyPI server

set -e

# Create a test venv
TEST_VENV="/tmp/git-maestro-test-venv"

# Validate TEST_VENV is set and not empty
if [ -z "$TEST_VENV" ]; then
    echo "✗ Error: TEST_VENV path is empty"
    exit 1
fi

if [ -d "$TEST_VENV" ]; then
    echo "Removing existing test venv..."
    rm -rf "$TEST_VENV" || exit 1
fi

echo "Creating test virtual environment..."
python -m venv "$TEST_VENV"

echo "Installing git-maestro from local PyPI..."
"$TEST_VENV/bin/pip" install -i http://localhost:8080/simple git-maestro

echo ""
echo "✓ Installation successful!"
echo ""
echo "Test venv location: $TEST_VENV"
echo ""
echo "To test the installation:"
echo "  source $TEST_VENV/bin/activate"
echo "  git-maestro --help"
echo "  git-maestro mcp -h"
echo ""
echo "To run verification tests:"
echo "  $TEST_VENV/bin/python -c 'from git_maestro.cli import main; print(\"✓ CLI import works\")'
echo "  $TEST_VENV/bin/python -c 'from git_maestro.mcp_server import MCPServer; print(\"✓ MCP import works\")'
echo "  $TEST_VENV/bin/python -c 'from git_maestro.actions import GetGithubActionsLogsAction; print(\"✓ Actions import works\")'
