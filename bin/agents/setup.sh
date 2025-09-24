#!/usr/bin/env bash

set -e

echo "=== Starting Complete Agent Environment Setup ==="
echo ""

# Change to the root directory
cd "$(dirname "$0")/../.."
ROOT_DIR="$(pwd)"
echo "Executing setup from root: $ROOT_DIR"

echo ""
echo "=== Running Backend Setup ==="
cd "$ROOT_DIR/spiffworkflow-backend"
./bin/agents/setup.sh

echo ""
echo "=== Running Frontend Setup ==="
cd "$ROOT_DIR/spiffworkflow-frontend"
./bin/agents/setup.sh

echo ""
echo "=== Complete Agent Environment Setup Finished ==="
echo ""
echo "To run the backend and frontend servers, you will need two separate terminals:"
echo ""
echo "In terminal 1 (for the backend):"
echo "cd $ROOT_DIR/spiffworkflow-backend"
echo "source ./bin/local_development_environment_setup"
echo "./bin/run_server_locally"
echo ""
echo "In terminal 2 (for the frontend):"
echo "cd $ROOT_DIR/spiffworkflow-frontend"
echo "npm start"
echo ""
echo "To run Playwright tests (after servers are running):"
echo "cd $ROOT_DIR"
echo "./bin/agents/run_playwright.sh"