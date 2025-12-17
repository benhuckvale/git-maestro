#!/bin/bash
# Start a local PyPI server for testing package deployment

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="/tmp/git-maestro-pypi"
LOG_FILE="/tmp/git-maestro-pypi.log"
PID_FILE="/tmp/git-maestro-pypi.pid"

# Validate paths are set and not empty
if [ -z "$PACKAGE_DIR" ] || [ -z "$LOG_FILE" ] || [ -z "$PID_FILE" ]; then
    echo "✗ Error: Required path variables are empty"
    exit 1
fi

# Cleanup on exit
cleanup() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Stopping PyPI server (PID $PID)..."
            kill "$PID" 2>/dev/null || true
            sleep 1
            kill -9 "$PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
}

trap cleanup EXIT

# Create package directory
mkdir -p "$PACKAGE_DIR"
rm -f "$PACKAGE_DIR"/*.whl "$PACKAGE_DIR"/*.tar.gz

# Build the package
echo "Building package..."
cd "$REPO_ROOT"
python -m build --outdir "$PACKAGE_DIR" > /dev/null 2>&1

echo "Packages built:"
ls -lh "$PACKAGE_DIR"/ | tail -2

# Start PyPI server
echo ""
echo "Starting local PyPI server on http://localhost:8080"
echo "Package directory: $PACKAGE_DIR"
echo "Log file: $LOG_FILE"
echo ""

pypi-server -p 8080 "$PACKAGE_DIR" > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"

# Wait for server to start
sleep 2

# Check if server is running
if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "✓ PyPI server started (PID: $(cat $PID_FILE))"
    echo ""
    echo "To install from this server:"
    echo "  pip install -i http://localhost:8080/simple git-maestro"
    echo ""
    echo "To upload to this server (from another terminal):"
    echo "  twine upload -r localhost http://localhost:8080 dist/*"
    echo ""
    echo "Press Ctrl+C to stop the server"
    echo ""
    # Keep the script running
    wait $(cat "$PID_FILE")
else
    echo "✗ Failed to start PyPI server"
    cat "$LOG_FILE"
    exit 1
fi
