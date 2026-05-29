from flask import current_app


def connector_proxy_request_proxies() -> dict[str, str] | None:
    proxy_url = current_app.config.get("SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_HTTP_PROXY_URL")
    if not proxy_url:
        return None
    return {"http": proxy_url, "https": proxy_url}
