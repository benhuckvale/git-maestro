#!/bin/bash
# Publish package to local PyPI server using twine

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE_DIR="/tmp/git-maestro-pypi"

# Validate paths are set and not empty
if [ -z "$REPO_ROOT" ] || [ -z "$PACKAGE_DIR" ]; then
    echo "✗ Error: Required path variables are empty"
    exit 1
fi

echo "Publishing to local PyPI server (http://localhost:8080)..."
echo ""

# Check if pypiserver is running
if ! curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo "✗ Local PyPI server is not running!"
    echo ""
    echo "Start it with:"
    echo "  pdm run pypi-local"
    echo ""
    exit 1
fi

# Build fresh packages
echo "Building fresh packages..."
cd "$REPO_ROOT"
rm -rf dist/
python -m build --outdir dist/ > /dev/null 2>&1

# Create ~/.pypirc for local server if it doesn't exist
if [ ! -f "$HOME/.pypirc" ]; then
    echo "Creating ~/.pypirc configuration..."
    mkdir -p "$(dirname "$HOME/.pypirc")"
    cat > "$HOME/.pypirc" << 'EOF'
[distutils]
index-servers =
    localhost

[localhost]
repository = http://localhost:8080
username = localuser
password = localpass123
EOF
fi

# Copy to local PyPI directory
mkdir -p "$PACKAGE_DIR"
cp dist/* "$PACKAGE_DIR/"

echo "Packages available:"
ls -lh "$PACKAGE_DIR"/ | tail -n +2

echo ""
echo "✓ Packages published to $PACKAGE_DIR"
echo ""
echo "To install:"
echo "  pip install -i http://localhost:8080/simple git-maestro"
