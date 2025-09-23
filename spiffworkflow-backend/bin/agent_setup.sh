#!/usr/bin/env bash

function error_handler() {
  >&2 echo "Exited with BAD EXIT CODE '${2}' in ${0} script at line: ${1}."
  exit "$2"
}
trap 'error_handler ${LINENO} $?' ERR
set -o errtrace -o errexit -o nounset -o pipefail

# Change the current working directory to the script's parent directory
# (spiffworkflow-backend) to ensure all paths are correct.
cd "$(dirname "$0")/.."
echo "Executing setup from: $(pwd)"

echo "--- Starting Environment Setup ---"

# Step 1: Install System Dependencies
echo "[1/5] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y libpq-dev libmysqlclient-dev mysql-client mysql-server

# Step 2: Configure and Start MySQL Server
echo "[2/5] Setting up MySQL server..."
# MySQL service should start automatically after installation, but ensure it's enabled and running
sudo systemctl enable mysql
sudo systemctl start mysql
# Create user with empty password as required by the application
sudo mysql -e "CREATE USER IF NOT EXISTS 'spiffworkflow'@'localhost' IDENTIFIED BY '';"
sudo mysql -e "GRANT ALL PRIVILEGES ON *.* TO 'spiffworkflow'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Step 3: Install Python Dependencies
echo "[3/5] Installing Python dependencies..."
echo "      - Running 'uv sync' from root..."
(cd .. && uv sync)
echo "      - Running 'uv sync' from spiffworkflow-backend..."
uv sync

# get process model repo as sibling of spiff-arena
process_model_dir="../sample-process-models"
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
echo "[5/5] Running tests to verify the environment..."
../bin/run_pyl

echo "--- Environment setup and verification complete. ---"
