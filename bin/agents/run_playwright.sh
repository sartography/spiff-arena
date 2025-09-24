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
    echo "   It assumes Linux-specific server setup and Playwright installation."
    echo "   Please run this script in a Linux container or agent environment."
    exit 1
fi

# Change to the root directory
cd "$(dirname "$0")/../.."
ROOT_DIR="$(pwd)"

echo "=== Running Playwright Tests ==="
echo "Root directory: $ROOT_DIR"
echo ""

# Variables to track what we started
STARTED_BACKEND=false
STARTED_FRONTEND=false
BACKEND_PID=""
FRONTEND_PID=""

# Cleanup function
cleanup() {
    echo ""
    echo "=== Cleaning up servers ==="
    
    if [ "${STARTED_BACKEND:-false}" = true ] && [ -n "${BACKEND_PID:-}" ]; then
        echo "Stopping backend server (PID: ${BACKEND_PID})..."
        kill "${BACKEND_PID}" 2>/dev/null || true
        wait "${BACKEND_PID}" 2>/dev/null || true
    fi
    
    if [ "${STARTED_FRONTEND:-false}" = true ] && [ -n "${FRONTEND_PID:-}" ]; then
        echo "Stopping frontend server (PID: ${FRONTEND_PID})..."
        kill "${FRONTEND_PID}" 2>/dev/null || true
        wait "${FRONTEND_PID}" 2>/dev/null || true
    fi
    
    echo "=== Cleanup complete ==="
}

# Set up trap for cleanup on exit
trap cleanup EXIT INT TERM

# Check if backend is running
echo "Checking if backend server is running..."
if ! curl -s -o /dev/null http://localhost:7000/v1.0/status; then
    echo "🚀 Starting backend server..."
    cd "$ROOT_DIR/spiffworkflow-backend"
    source ./bin/local_development_environment_setup
    ./bin/run_server_locally &
    BACKEND_PID=$!
    STARTED_BACKEND=true
    
    # Wait for backend to be ready
    echo "Waiting for backend to be ready..."
    for i in {1..60}; do
        if curl -s -o /dev/null http://localhost:7000/v1.0/status; then
            echo "✅ Backend is ready!"
            break
        fi
        if [ $i -eq 60 ]; then
            echo "❌ Backend failed to start within 60 seconds"
            exit 1
        fi
        sleep 1
    done
else
    echo "✅ Backend server is already running"
fi

# Check if frontend is running  
echo "Checking if frontend server is running..."
if ! curl -s -o /dev/null http://localhost:7001; then
    echo "🚀 Starting frontend server..."
    cd "$ROOT_DIR/spiffworkflow-frontend"
    npm start &
    FRONTEND_PID=$!
    STARTED_FRONTEND=true
    
    # Wait for frontend to be ready
    echo "Waiting for frontend to be ready..."
    for i in {1..60}; do
        if curl -s -o /dev/null http://localhost:7001; then
            echo "✅ Frontend is ready!"
            break
        fi
        if [ $i -eq 60 ]; then
            echo "❌ Frontend failed to start within 60 seconds"
            exit 1
        fi
        sleep 1
    done
else
    echo "✅ Frontend server is already running"
fi

echo ""
echo "🧪 Running Playwright tests..."
cd "$ROOT_DIR/spiffworkflow-frontend/test/browser"
uv run pytest "${@:-}"

echo ""
echo "=== Playwright Tests Complete ==="