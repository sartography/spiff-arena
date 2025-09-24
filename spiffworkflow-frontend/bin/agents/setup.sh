#!/usr/bin/env bash

set -e

# Change the current working directory to the script's parent directory
# (spiffworkflow-frontend) to ensure all paths are correct.
cd "$(dirname "$0")/../.."
echo "Executing frontend setup from: $(pwd)"

echo "--- Starting Frontend Environment Setup ---"

# Step 1: Install Node.js dependencies
echo "[1/3] Installing frontend Node.js dependencies..."
npm install

# Step 2: Setup Playwright Test Environment
echo "[2/3] Setting up Playwright test environment..."
cd test/browser
echo "Installing Playwright Python dependencies..."
uv sync
echo "Installing Playwright system dependencies..."
sudo /home/jules/.local/bin/uv run playwright install-deps
echo "Installing Playwright browsers..."
uv run playwright install
cd ../..

echo "[3/3] Frontend setup complete!"
echo ""
echo "--- Frontend Environment Setup Complete ---"
echo "To start the frontend server:"
echo "cd /app/spiffworkflow-frontend"
echo "npm start"