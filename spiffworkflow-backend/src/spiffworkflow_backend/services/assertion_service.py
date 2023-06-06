import contextlib
from collections.abc import Generator

import sentry_sdk
from flask import current_app


@contextlib.contextmanager
def safe_assertion(condition: bool) -> Generator[bool, None, None]:
    try:
        yield True
    except AssertionError as e:
        if not condition:
            sentry_sdk.capture_exception(e)
            current_app.logger.exception(e)
            if current_app.config["ENV_IDENTIFIER"] in ["local_development", "unit_testing"]:
                raise e
