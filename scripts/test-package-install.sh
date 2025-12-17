#!/bin/bash
# Test that the package installs correctly and all imports work

set -e

TEST_VENV="/tmp/git-maestro-test-venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Validate TEST_VENV is set and not empty
if [ -z "$TEST_VENV" ]; then
    echo "✗ Error: TEST_VENV path is empty"
    exit 1
fi

echo "Testing git-maestro package installation..."
echo ""

# Clean up old venv
if [ -d "$TEST_VENV" ]; then
    echo "Removing existing test venv..."
    rm -rf "$TEST_VENV" || exit 1
fi

# Create fresh venv
echo "Creating test virtual environment at $TEST_VENV..."
python -m venv "$TEST_VENV"

# Install the wheel
echo "Installing git-maestro from dist/..."
"$TEST_VENV/bin/pip" install --quiet "$SCRIPT_DIR/dist/git_maestro-0.1.0-py3-none-any.whl"

echo ""
echo "Running import tests..."
echo ""

# Test CLI import
echo -n "Testing CLI import... "
"$TEST_VENV/bin/python" -c "from git_maestro.cli import main; print('✓')"

# Test MCP server import
echo -n "Testing MCP server import... "
"$TEST_VENV/bin/python" -c "from git_maestro.mcp_server import MCPServer; print('✓')"

# Test Actions import
echo -n "Testing actions import... "
"$TEST_VENV/bin/python" -c "from git_maestro.actions import GetGithubActionsLogsAction; print('✓')"

# Test entry point is available
echo -n "Testing git-maestro command... "
if "$TEST_VENV/bin/git-maestro" --help > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗ (failed)"
    exit 1
fi

# Test MCP subcommand
echo -n "Testing MCP subcommand... "
if "$TEST_VENV/bin/git-maestro" mcp -h > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗ (failed)"
    exit 1
fi

# Test MCP tools are registered
echo -n "Testing MCP tools registration... "
TOOLS=$("$TEST_VENV/bin/python" -c "from git_maestro.mcp_server import MCPServer; s = MCPServer(); print(len(s.tools))")
if [ "$TOOLS" -ge 5 ]; then
    echo "✓ ($TOOLS tools)"
else
    echo "✗ (expected >=5 tools, got $TOOLS)"
    exit 1
fi

echo ""
echo "✓ All installation tests passed!"
echo ""
echo "Test venv at: $TEST_VENV"
echo ""
echo "To manually test:"
echo "  source $TEST_VENV/bin/activate"
echo "  git-maestro --help"
echo "  git-maestro mcp -h"
