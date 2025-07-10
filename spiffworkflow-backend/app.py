from spiffworkflow_backend import create_app

# this is used by flask when running with it directly like:
#   uv run flask db
# to run a server, use uvicorn like in ./bin/run_server_locally and ./bin/boot_server_in_docker
app = create_app().app
