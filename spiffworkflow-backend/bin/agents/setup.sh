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
    echo "   It requires apt-get, systemctl, and other Linux-specific tools."
    echo "   Please run this script in a Linux container or agent environment."
    exit 1
fi

# Change the current working directory to the script's parent directory
# (spiffworkflow-backend) to ensure all paths are correct.
cd "$(dirname "$0")/../.."
echo "Executing backend setup from: $(pwd)"

echo "--- Starting Backend Environment Setup ---"

# Step 1: Install System Dependencies
echo "[1/5] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y libpq-dev libmysqlclient-dev mysql-client mysql-server

# Step 2: Configure and Start MySQL Server
echo "[2/5] Setting up MySQL server..."
# MySQL service should start automatically after installation, but ensure it's enabled and running
sudo systemctl enable mysql
sudo systemctl start mysql
# Set root password to empty as required by recreate_db script
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '';"
# Also create the spiffworkflow user with empty password
sudo mysql -e "CREATE USER IF NOT EXISTS 'spiffworkflow'@'localhost' IDENTIFIED BY '';"
sudo mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'spiffworkflow'@'localhost';"
# Create the databases that recreate_db expects to exist
sudo mysql -e "CREATE DATABASE IF NOT EXISTS spiffworkflow_backend_local_development;"
sudo mysql -e "CREATE DATABASE IF NOT EXISTS spiffworkflow_backend_unit_testing;"
sudo mysql -e "FLUSH PRIVILEGES;"

# Step 3: Install Python Dependencies
echo "[3/5] Installing Python dependencies..."
echo "      - Running 'uv sync' from root..."
(cd ../.. && uv sync)
echo "      - Running 'uv sync' from spiffworkflow-backend..."
uv sync

# get process model repo as sibling of spiff-arena
process_model_dir="../../sample-process-models"
if [[ ! -d "$process_model_dir" ]]; then
  git clone https://github.com/sartography/sample-process-models.git "$process_model_dir"
fi

# Step 4: Set up Databases
echo "[4/5] Setting up databases..."
echo "      - Creating main database..."
./bin/recreate_db clean
echo "      - Creating test database..."
SPIFFWORKFLOW_BACKEND_DATABASE_TYPE=sqlite ./bin/recreate_db clean

# Step 5: Run Tests to Verify Setup
echo "[5/5] Running tests to verify the backend environment..."
../../bin/run_pyl

echo "--- Backend environment setup and verification complete. ---"
