#!/usr/bin/env bash
# This script automates the setup of the entire environment for running Playwright tests.

set -e

echo "--- Installing System Dependencies ---"
sudo apt-get update
sudo apt-get install -y libpq-dev libmysqlclient-dev mysql-client npm

echo "--- Setting up Backend ---"
cd /app/spiffworkflow-backend
echo "Installing backend Python dependencies..."
uv sync
echo "Creating backend databases..."
# Note: This requires a running mysql server.
# The script will continue if this step fails.
set +e
./bin/recreate_db clean
set -e
SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean
cd /app

echo "--- Setting up Frontend ---"
cd /app/spiffworkflow-frontend
echo "Installing frontend Node.js dependencies..."
npm install
cd /app

echo "--- Setting up Playwright Test Environment ---"
cd /app/spiffworkflow-frontend/test/browser
echo "Installing Playwright Python dependencies..."
uv sync
echo "Installing Playwright system dependencies..."
sudo /home/jules/.local/bin/uv run playwright install-deps
echo "Installing Playwright browsers..."
uv run playwright install
cd /app

echo ""
echo "--- Setup Complete! ---"
echo "You can now run the Playwright tests."
echo "To run the backend and frontend servers, you will need two separate terminals."
echo ""
echo "In terminal 1 (for the backend):"
echo "cd /app/spiffworkflow-backend"
echo "source ./bin/local_development_environment_setup"
echo "./bin/run_server_locally"
echo ""
echo "In terminal 2 (for the frontend):"
echo "cd /app/spiffworkflow-frontend"
echo "npm start"
echo ""
echo "To run the Playwright tests (in a third terminal):"
echo "cd /app/spiffworkflow-frontend/test/browser"
echo "uv run pytest"
