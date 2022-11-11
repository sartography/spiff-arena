"""Test_acceptance_test_fixtures."""
from flask.app import Flask
from spiffworkflow_backend.services.acceptance_test_fixtures import (
    load_acceptance_test_fixtures,
)


def test_start_dates_are_one_hour_apart(app: Flask) -> None:
    """Test_start_dates_are_one_hour_apart."""
    process_instances = load_acceptance_test_fixtures()

    assert len(process_instances) > 2
    assert process_instances[0].start_in_seconds is not None
    assert process_instances[1].start_in_seconds is not None
    assert (process_instances[0].start_in_seconds - 3600) == (
        process_instances[1].start_in_seconds
    )
