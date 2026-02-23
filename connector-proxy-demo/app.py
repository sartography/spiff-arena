import os
import inspect

from spiffworkflow_proxy.blueprint import proxy_blueprint
from spiffworkflow_proxy.blueprint import PluginService
from flask import Flask
from flask import request

app = Flask(__name__)
app.config.from_pyfile("config.py", silent=True)

if app.config.get("ENV", "development") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Use the SpiffConnector Blueprint, which will auto-discover any
# connector-* packages and provide API endpoints for listing and executing
# available services.
app.register_blueprint(proxy_blueprint)

# Backward compatibility: backend now sends extra `spiff__*` metadata with
# each connector call, but many existing connector command constructors do not
# accept these kwargs. Keep task data for execute(...), strip other metadata.
original_do_command = app.view_functions["proxy_blueprint.do_command"]


def _accepted_constructor_kwargs(command_class: type) -> set[str] | None:
    if command_class.__init__ is object.__init__:
        return set()

    signature = inspect.signature(command_class.__init__)
    accepts_any_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )
    if accepts_any_kwargs:
        return None

    accepted = set()
    for name, parameter in signature.parameters.items():
        if name == "self":
            continue
        if parameter.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            accepted.add(name)
    return accepted


def do_command_compat(plugin_display_name: str, command_name: str):  # type: ignore[no-untyped-def]
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        command_class = PluginService.command_named(plugin_display_name, command_name)
        if command_class is not None:
            accepted_kwargs = _accepted_constructor_kwargs(command_class)
            if accepted_kwargs is not None:
                for key in [k for k in payload if k != "spiff__task_data" and k not in accepted_kwargs]:
                    payload.pop(key, None)
    return original_do_command(plugin_display_name, command_name)


app.view_functions["proxy_blueprint.do_command"] = do_command_compat

if __name__ == "__main__":
    app.run(host="localhost", port=7004)
