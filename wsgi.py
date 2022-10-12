"""This is my docstring."""
import os

from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.acceptance_test_fixtures import (
    load_acceptance_test_fixtures,
)
from spiffworkflow_backend.services.data_setup_service import DataSetupService

app = create_app()

# this is in here because when we put it in the create_app function,
# it also loaded when we were running migrations, which resulted in a chicken/egg thing.
if os.environ.get("SPIFFWORKFLOW_BACKEND_LOAD_FIXTURE_DATA") == "true":
    with app.app_context():
        load_acceptance_test_fixtures()
