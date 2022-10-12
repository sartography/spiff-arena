import importlib
import inspect
import json
import os
import pkgutil
import types
import typing

from flask import Flask
from flask import redirect
from flask import request
from flask import Response
from flask import session
from flask import url_for
from flask_oauthlib.contrib.client import OAuth


app = Flask(__name__)

app.config.from_pyfile("config.py", silent=True)

if app.config["ENV"] != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


@app.before_first_request
def load_plugins():
    print("load the plugins once here?")


@app.route("/liveness")
def status():
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def list_targets(targets):
    descriptions = []

    for plugin_name, plugin_targets in targets.items():
        for target_name, target in plugin_targets.items():
            description = PluginService.describe_target(
                plugin_name, target_name, target
            )
            descriptions.append(description)

    return Response(json.dumps(descriptions), status=200, mimetype="application/json")


@app.route("/v1/auths")
def list_auths():
    return list_targets(PluginService.available_auths_by_plugin())


@app.route("/v1/commands")
def list_commands():
    return list_targets(PluginService.available_commands_by_plugin())


def auth_handler(plugin_display_name, auth_name, params):
    auth = PluginService.auth_named(plugin_display_name, auth_name)
    if auth is not None:
        handler_params = auth.filtered_params(params)
        app_description = auth(**handler_params).app_description()

        # TODO right now this assumes Oauth.
        # would need to expand if other auth providers are used
        handler = OAuth(app).remote_app(**app_description)

        @handler.tokengetter
        def tokengetter():
            pass

        @handler.tokensaver
        def tokensaver(token):
            pass

        return handler


@app.route("/v1/auth/<plugin_display_name>/<auth_name>")
def do_auth(plugin_display_name, auth_name):
    params = request.args.to_dict()
    our_redirect_url = params["redirect_url"]
    session["redirect_url"] = our_redirect_url

    handler = auth_handler(plugin_display_name, auth_name, params)
    if handler is None:
        return Response("Auth not found", status=404)

    # TODO factor into handler
    # TODO namespace the keys
    session["client_id"] = params["client_id"]
    session["client_secret"] = params["client_secret"]

    oauth_redirect_url = url_for(
        "auth_callback",
        plugin_display_name=plugin_display_name,
        auth_name=auth_name,
        _external=True,
    )

    return handler.authorize(callback_uri=oauth_redirect_url)


@app.route("/v1/auth/<plugin_display_name>/<auth_name>/callback")
def auth_callback(plugin_display_name, auth_name):
    handler = auth_handler(plugin_display_name, auth_name, session)
    if handler is None:
        return Response("Auth not found", status=404)

    response = json.dumps(handler.authorized_response())
    redirect_url = session["redirect_url"]

    # TODO compare redirect_url to whitelist

    return redirect(f"{redirect_url}?response={response}")


@app.route("/v1/do/<plugin_display_name>/<command_name>")
def do_command(plugin_display_name, command_name):
    command = PluginService.command_named(plugin_display_name, command_name)
    if command is None:
        return json_error_response(
            f"Command not found: {plugin_display_name}:{command_name}", status=404
        )

    params = request.args.to_dict()
    raw_task_data = params.pop('spiff__task_data', '{}')
    task_data = json.loads(raw_task_data)

    try:
        result = command(**params).execute(app.config, task_data)
    except Exception as e:
        return json_error_response(
            f"Error encountered when executing {plugin_display_name}:{command_name} {str(e)}",
            status=404,
        )

    return Response(result["response"], mimetype=result["mimetype"], status=200)


def json_error_response(message, status):
    resp = {"error": message, "status": status}
    return Response(json.dumps(resp), status=status)


class PluginService:
    PLUGIN_PREFIX = "connector_"

    @staticmethod
    def plugin_display_name(plugin_name):
        return plugin_name.removeprefix(PluginService.PLUGIN_PREFIX)

    @staticmethod
    def plugin_name_from_display_name(plugin_display_name):
        return PluginService.PLUGIN_PREFIX + plugin_display_name

    @staticmethod
    def available_plugins():
        return {
            name: importlib.import_module(name)
            for finder, name, ispkg in pkgutil.iter_modules()
            if name.startswith(PluginService.PLUGIN_PREFIX)
        }

    @staticmethod
    def available_auths_by_plugin():
        return {
            plugin_name: {
                auth_name: auth
                for auth_name, auth in PluginService.auths_for_plugin(
                    plugin_name, plugin
                )
            }
            for plugin_name, plugin in PluginService.available_plugins().items()
        }

    @staticmethod
    def available_commands_by_plugin():
        return {
            plugin_name: {
                command_name: command
                for command_name, command in PluginService.commands_for_plugin(
                    plugin_name, plugin
                )
            }
            for plugin_name, plugin in PluginService.available_plugins().items()
        }

    @staticmethod
    def target_id(plugin_name, target_name):
        plugin_display_name = PluginService.plugin_display_name(plugin_name)
        return f"{plugin_display_name}/{target_name}"

    @staticmethod
    def auth_named(plugin_display_name, auth_name):
        plugin_name = PluginService.plugin_name_from_display_name(plugin_display_name)
        available_auths_by_plugin = PluginService.available_auths_by_plugin()

        try:
            return available_auths_by_plugin[plugin_name][auth_name]
        except Exception:
            return None

    @staticmethod
    def command_named(plugin_display_name, command_name):
        plugin_name = PluginService.plugin_name_from_display_name(plugin_display_name)
        available_commands_by_plugin = PluginService.available_commands_by_plugin()

        try:
            return available_commands_by_plugin[plugin_name][command_name]
        except Exception:
            return None

    @staticmethod
    def modules_for_plugin_in_package(plugin, package_name):
        for finder, name, ispkg in pkgutil.iter_modules(plugin.__path__):
            if ispkg and name == package_name:
                sub_pkg = finder.find_module(name).load_module(name)
                yield from PluginService.modules_for_plugin_in_package(sub_pkg, None)
            else:
                spec = finder.find_spec(name)
                if spec is not None and spec.loader is not None:
                    module = types.ModuleType(spec.name)
                    spec.loader.exec_module(module)
                    yield name, module

    @staticmethod
    def targets_for_plugin(plugin_name, plugin, target_package_name):
        for module_name, module in PluginService.modules_for_plugin_in_package(
            plugin, target_package_name
        ):
            for member_name, member in inspect.getmembers(module, inspect.isclass):
                if member.__module__ == module_name:
                    yield member_name, member

    @staticmethod
    def auths_for_plugin(plugin_name, plugin):
        yield from PluginService.targets_for_plugin(plugin_name, plugin, "auths")

    @staticmethod
    def commands_for_plugin(plugin_name, plugin):
        # TODO check if class has an execute method before yielding
        yield from PluginService.targets_for_plugin(plugin_name, plugin, "commands")

    @staticmethod
    def param_annotation_desc(param):
        """Parses a callable parameter's type annotation, if any, to form a ParameterDescription."""
        param_id = param.name
        param_type_desc = "any"

        none_type = type(None)
        supported_types = {str, int, bool, none_type}
        unsupported_type_marker = object

        annotation = param.annotation

        if annotation in supported_types:
            annotation_types = {annotation}
        else:
            # an annotation can have more than one type in the case of a union
            # get_args normalizes Union[str, dict] to (str, dict)
            # get_args normalizes Optional[str] to (str, none)
            # all unsupported types are marked so (str, dict) -> (str, unsupported)
            # the absense of a type annotation results in an empty set
            annotation_types = set(
                map(
                    lambda t: t if t in supported_types else unsupported_type_marker,
                    typing.get_args(annotation),
                )
            )

        # a parameter is required if it has no default value and none is not in its type set
        param_req = param.default is param.empty and none_type not in annotation_types

        # the none type from a union is used for requiredness, but needs to be discarded
        # to single out the optional type
        annotation_types.discard(none_type)

        # if we have a single supported type use that, else any is the default
        if len(annotation_types) == 1:
            annotation_type = annotation_types.pop()
            if annotation_type in supported_types:
                param_type_desc = annotation_type.__name__

        return {"id": param_id, "type": param_type_desc, "required": param_req}

    @staticmethod
    def callable_params_desc(kallable):
        sig = inspect.signature(kallable)
        params_to_skip = ["self", "kwargs"]
        sig_params = filter(
            lambda param: param.name not in params_to_skip, sig.parameters.values()
        )
        params = [PluginService.param_annotation_desc(param) for param in sig_params]

        return params

    @staticmethod
    def describe_target(plugin_name, target_name, target):
        parameters = PluginService.callable_params_desc(target.__init__)
        target_id = PluginService.target_id(plugin_name, target_name)
        return {"id": target_id, "parameters": parameters}


if __name__ == "__main__":
    app.run(host="localhost", port=5000)
