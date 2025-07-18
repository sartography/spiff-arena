import os

from spiffworkflow_backend import create_app
from spiffworkflow_backend.middleware.asgi_proxy_fix import ASGIProxyFix
from spiffworkflow_backend.services.acceptance_test_fixtures import load_acceptance_test_fixtures

connexion_app = create_app()

num_proxies = 0

# this is the first configuration spiffworkflow-backend supported.
# you should use SPIFFWORKFLOW_BACKEND_PROXY_COUNT_FOR_PROXY_FIX instead, since it is more precise.
if connexion_app.app.config["SPIFFWORKFLOW_BACKEND_USE_WERKZEUG_MIDDLEWARE_PROXY_FIX"]:
    num_proxies = 1

if connexion_app.app.config["SPIFFWORKFLOW_BACKEND_PROXY_COUNT_FOR_PROXY_FIX"]:
    num_proxies = int(connexion_app.app.config["SPIFFWORKFLOW_BACKEND_PROXY_COUNT_FOR_PROXY_FIX"])

if num_proxies > 0:
    connexion_app.add_middleware(ASGIProxyFix, x_for=num_proxies, x_proto=num_proxies, x_host=num_proxies, x_prefix=num_proxies)

# this is in here because when we put it in the create_app function,
# it also loaded when we were running migrations, which resulted in a chicken/egg thing.
if os.environ.get("SPIFFWORKFLOW_BACKEND_LOAD_FIXTURE_DATA") == "true":
    with connexion_app.app.app_context():
        load_acceptance_test_fixtures()
