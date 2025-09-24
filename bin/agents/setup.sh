#!/usr/bin/env bash

function error_handler() {
  >&2 echo "Exited with BAD EXIT CODE '${2}' in ${0} script at line: ${1}."
  exit "$2"
}
trap 'error_handler ${LINENO} $?' ERR
set -o errtrace -o errexit -o nounset -o pipefail

# Check if running on macOS
if [[ "${OSTYPE:-}" == "darwin"* ]]; then
    echo "❌ This script is designed for Linux agent environments and cannot run on macOS."
    echo "   The backend and frontend setup scripts require Linux-specific tools."
    echo "   Please run this script in a Linux container or agent environment."
    exit 1
fi

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