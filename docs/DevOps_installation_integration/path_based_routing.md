# Path-based Routing

If you are using frontend, frontend and backend need to share cookies.
Backend, in particular, sets a cookie, and frontend needs to read it.
As such, you cannot run frontend and backend on different subdomains, like this:

* frontend.example.com
* backend.example.com

Instead, we often run them like this:

* example.com for frontend
* api.example.com for backend

This works, since backend can set a cookie for the entire domain, and frontend can read it.

Another alternative that works well is to run them on the same host, but with different paths, like this:

 * spiff.example.com for frontend
 * spiff.example.com/api for backend

To accomplish this path-based routing scenario, set environment variables like this in frontend:

```sh
SPIFFWORKFLOW_FRONTEND_RUNTIME_CONFIG_APP_ROUTING_STRATEGY=path_based
```

And in backend, you may need to set:

```sh
SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND=https://spiff.example.com
SPIFFWORKFLOW_BACKEND_URL=https://spiff.example.com/api
# if you happen to be using the internal openid server. do not do this in production.
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL=https://spiff.example.com/api/openid
# if you can manage, use in-cluster DNS for connector. you may need a different host or port.
SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL=http://spiffworkflow-connector:8004
```

Backend does not support paths like `/api/v1.0/status`, but instead wants `/v1.0/status`.
As such, a proxy in frontend of backend will need to remove the `/api` part of the path before handing the request to backend.
