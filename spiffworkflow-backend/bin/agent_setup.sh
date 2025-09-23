#!/bin/bash

# This script automates the setup of the development environment.
# It is designed to be run from any location, as it will change its
# own working directory to the parent 'spiffworkflow-backend' directory.

# Exit on error
set -e

# Change the current working directory to the script's parent directory
# (spiffworkflow-backend) to ensure all paths are correct.
cd "$(dirname "$0")/.."
echo "Executing setup from: $(pwd)"

echo "--- Starting Environment Setup ---"

# Step 1: Install System Dependencies
echo "[1/4] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y libpq-dev libmysqlclient-dev mysql-client

# Step 2: Install Python Dependencies
echo "[2/4] Installing Python dependencies..."
# First, from the repository root, as requested.
echo "      - Running 'uv sync' from root..."
(cd .. && uv sync)
# Second, from the backend directory, as requested.
echo "      - Running 'uv sync' from spiffworkflow-backend..."
uv sync

# Step 3: Set up Databases
echo "[3/4] Setting up databases..."
# These commands are run from the spiffworkflow-backend directory,
# as per AGENTS.md.
echo "      - Creating main database..."
./bin/recreate_db clean
echo "      - Creating test database..."
SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean

# Step 4: Run Tests to Verify Setup
echo "[4/4] Running tests to verify the environment..."
# The test runner script is in the root bin/ directory and should be
# executed from the root, as per AGENTS.md.
(cd .. && ./bin/run_pyl)

echo "--- Environment setup and verification complete. ---"
