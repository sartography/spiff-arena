import logging

import falcon.asgi
import httpx
import orjson

# TODO: change this for prod
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

http_client = httpx.AsyncClient(timeout=None)


#
# Controllers
#


class v1_commands:
    async def on_get(self, req, resp):
        resp.media = embedded_connectors


class v1_do_http_connector:
    def __init__(self, request_method):
        self.request_method = request_method
    
    async def on_post(self, req, resp):
        params = await req.media
        auth = None
        error = None
        status = 0
        url = params.get("url")
        
        basic_auth_username = params.get("basic_auth_username")
        basic_auth_password = params.get("basic_auth_password")

        if basic_auth_username and basic_auth_password:
            auth = (basic_auth_username, basic_auth_password)

        # TODO: error handling
        http_response = await http_client.request(self.request_method, url,
            headers=params.get("headers"),
            params=params.get("params"),
            json=params.get("data"),
            auth=auth)
        status = http_response.status_code
 
        content_type = http_response.headers.get("Content-Type", "")
        raw_response = http_response.text

        if "application/json" in content_type:
            command_response = orjson.loads(raw_response)
        else:
            command_response = { "raw_response": raw_response }

        resp.media = {
            "command_response": {
                "body": command_response,
                "mimetype": "application/json",
                "http_status": status,
            },
            "command_response_version": 2,
            "error": error,
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

app.add_route("/v1/commands", v1_commands())

app.add_route("/v1/do/http/DeleteRequest", v1_do_http_connector("DELETE"))
app.add_route("/v1/do/http/GetRequest", v1_do_http_connector("GET"))
app.add_route("/v1/do/http/HeadRequest", v1_do_http_connector("HEAD"))
app.add_route("/v1/do/http/PatchRequest", v1_do_http_connector("PATCH"))
app.add_route("/v1/do/http/PostRequest", v1_do_http_connector("POST"))
app.add_route("/v1/do/http/PutRequest", v1_do_http_connector("PUT"))


#
# Static Data
#


http_base_params = [
    { "id": "url", "type": "str", "required": True },
    { "id": "headers", "type": "any", "required": False },
]

http_basic_auth_params = [
    { "id": "basic_auth_username", "type": "str", "required": False },
    { "id": "basic_auth_password", "type": "str", "required": False },
]

http_ro_params = [
    *http_base_params,
    { "id": "params", "type": "any", "required": False },
    *http_basic_auth_params,
]

http_rw_params = [
    *http_base_params,
    { "id": "data", "type": "any", "required": False },
    *http_basic_auth_params,
]

embedded_connectors = [
    { "id": "http/DeleteRequest", "parameters": http_rw_params },
    { "id": "http/GetRequest", "parameters": http_ro_params },
    { "id": "http/HeadRequest", "parameters": http_ro_params },
    { "id": "http/PatchRequest", "parameters": http_rw_params },
    { "id": "http/PostRequest", "parameters": http_rw_params },
    { "id": "http/PutRequest", "parameters": http_rw_params },
]
