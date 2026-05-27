import logging

import falcon.asgi
import httpx
import orjson

# TODO: change this for prod
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

http_client = httpx.AsyncClient(timeout=None)

SENSITIVE_FIELD_NAMES = {
    "admin_client_secret",
    "admin_password",
    "api_key",
    "authorization",
    "basic_auth_password",
    "client_secret",
    "password",
    "smtp_password",
    "temporary_password",
}


def redacted(value):
    if isinstance(value, dict):
        redacted_value = {}
        for key, child in value.items():
            key_lower = key.lower()
            if key_lower in SENSITIVE_FIELD_NAMES or (
                key_lower == "value" and value.get("type") == "password"
            ):
                redacted_value[key] = "***REDACTED***"
            else:
                redacted_value[key] = redacted(child)
        return redacted_value
    if isinstance(value, list):
        return [redacted(item) for item in value]
    return value


def request_body_arguments(params):
    body_format = params.get("body_format", "json")
    data = params.get("data")

    if body_format in ("", None, "json"):
        return {"json": data}
    if body_format == "form":
        return {"data": data}
    if body_format == "raw":
        if isinstance(data, str):
            return {"content": data}
        return {"content": orjson.dumps(data)}
    if body_format == "none":
        return {}

    raise ValueError(
        "body_format must be one of json, form, raw, or none"
    )


def connector_response(http_response, error=None, include_response_headers=False):
    status = http_response.status_code

    content_type = http_response.headers.get("Content-Type", "")
    raw_response = http_response.text

    if "application/json" in content_type and raw_response:
        command_response = orjson.loads(raw_response)
    else:
        command_response = {"raw_response": raw_response}

    if status >= 300 and not error:
        error = {
            "error_code": f"HttpError{status}",
            "message": f"HTTP {status} error from service. Response: {raw_response}",
        }

    return {
        "command_response": {
            "body": command_response,
            "mimetype": "application/json",
            "http_status": status,
            "headers": dict(http_response.headers) if include_response_headers else {},
        },
        "command_response_version": 2,
        "error": error,
        "spiff__logs": [],
    }


#
# Controllers
#


class v1_commands:
    async def on_get(self, req, resp):
        resp.media = embedded_connectors


class v1_do_http_connector:
    def __init__(self, request_method, has_body):
        self.request_method = request_method
        self.has_body = has_body

    async def on_post(self, req, resp):
        params = await req.media
        logger.info("HTTP request: %s", redacted(params))

        auth = None
        url = params.get("url")

        basic_auth_username = params.get("basic_auth_username")
        basic_auth_password = params.get("basic_auth_password")

        if basic_auth_username and basic_auth_password:
            auth = (basic_auth_username, basic_auth_password)

        request_args = {}
        if self.has_body:
            request_args.update(request_body_arguments(params))

        try:
            http_response = await http_client.request(
                self.request_method,
                url,
                headers=params.get("headers"),
                params=params.get("params"),
                auth=auth,
                **request_args,
            )
            resp.media = connector_response(
                http_response,
                include_response_headers=params.get("include_response_headers", False),
            )
        except Exception as e:
            logger.error("HTTP request failed: %s", e, exc_info=True)
            logger.error("Request params: %s", redacted(params))
            resp.media = {
                "command_response": {
                    "body": {"raw_response": str(e)},
                    "mimetype": "application/json",
                    "http_status": 500,
                },
                "command_response_version": 2,
                "error": {"message": str(e), "error_code": "INTERNAL_ERROR"},
                "spiff__logs": [],
            }


#
# App
#


extra_handlers = {
    'application/json': falcon.media.JSONHandler(
        dumps=orjson.dumps,
        loads=orjson.loads,
    ),
}

app = falcon.asgi.App(
    cors_enable=True,
)

app.req_options.media_handlers.update(extra_handlers)
app.resp_options.media_handlers.update(extra_handlers)

class liveness:
    async def on_get(self, req, resp):
        resp.media = {"status": "ok"}


app.add_route("/liveness", liveness())
app.add_route("/v1/commands", v1_commands())

app.add_route("/v1/do/http/DeleteRequest", v1_do_http_connector("DELETE", True))
app.add_route("/v1/do/http/GetRequest", v1_do_http_connector("GET", False))
app.add_route("/v1/do/http/HeadRequest", v1_do_http_connector("HEAD", False))
app.add_route("/v1/do/http/PatchRequest", v1_do_http_connector("PATCH", True))
app.add_route("/v1/do/http/PostRequest", v1_do_http_connector("POST", True))
app.add_route("/v1/do/http/PutRequest", v1_do_http_connector("PUT", True))


#
# Static Data
#


http_base_params = [
    {"id": "url", "type": "str", "required": True},
    {"id": "headers", "type": "any", "required": False},
]

http_basic_auth_params = [
    {"id": "basic_auth_username", "type": "str", "required": False},
    {"id": "basic_auth_password", "type": "str", "required": False},
]

http_ro_params = [
    *http_base_params,
    {"id": "params", "type": "any", "required": False},
    *http_basic_auth_params,
]

http_rw_params = [
    *http_base_params,
    {"id": "data", "type": "any", "required": False},
    {"id": "body_format", "type": "str", "required": False},
    {"id": "include_response_headers", "type": "bool", "required": False},
    *http_basic_auth_params,
]

embedded_connectors = [
    {"id": "http/DeleteRequest", "parameters": http_rw_params},
    {"id": "http/GetRequest", "parameters": http_ro_params},
    {"id": "http/HeadRequest", "parameters": http_ro_params},
    {"id": "http/PatchRequest", "parameters": http_rw_params},
    {"id": "http/PostRequest", "parameters": http_rw_params},
    {"id": "http/PutRequest", "parameters": http_rw_params},
]
