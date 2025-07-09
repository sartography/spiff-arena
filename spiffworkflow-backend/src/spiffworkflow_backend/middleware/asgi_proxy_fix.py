from __future__ import annotations

import typing as t

from uvicorn._types import ASGI3Application, ASGIReceiveCallable, ASGISendCallable, Scope
from werkzeug.http import parse_list_header


class ASGIProxyFix:
    """
    This middleware can be used when a known proxy is fronting the application,
    and is trusted to be properly setting the `X-Forwarded-` headers.
    It is a version of `werkzeug.middleware.proxy_fix.ProxyFix` adapted for ASGI applications.
    It should be configured with the number of proxies that are chained in front of it.
    Not all proxies set all the headers. Since incoming headers can be faked, you must
    set how many proxies are setting each header so the middleware knows what to trust.

    -   ``X-Forwarded-For`` sets ``scope['client']``.
    -   ``X-Forwarded-Proto`` sets ``scope['scheme']``.
    -   ``X-Forwarded-Host`` sets the ``host`` header.
    -   ``X-Forwarded-Port`` sets the port in the ``host`` header.
    -   ``X-Forwarded-Prefix`` sets ``scope['root_path']``.

    :param app: The ASGI application to wrap.
    :param x_for: Number of values to trust for ``X-Forwarded-For``.
    :param x_proto: Number of values to trust for ``X-Forwarded-Proto``.
    :param x_host: Number of values to trust for ``X-Forwarded-Host``.
    :param x_port: Number of values to trust for ``X-Forwarded-Port``.
    :param x_prefix: Number of values to trust for ``X-Forwarded-Prefix``.
    """

    def __init__(
        self,
        app: ASGI3Application,
        x_for: int = 1,
        x_proto: int = 1,
        x_host: int = 0,
        x_port: int = 0,
        x_prefix: int = 0,
    ) -> None:
        self.app = app
        self.x_for = x_for
        self.x_proto = x_proto
        self.x_host = x_host
        self.x_port = x_port
        self.x_prefix = x_prefix

    def _get_real_value(self, trusted: int, value: str | None) -> str | None:
        """Get the real value from a list header based on the configured
        number of trusted proxies.
        """
        if not (trusted and value):
            return None
        values = parse_list_header(value)
        if len(values) >= trusted:
            return values[-trusted]
        return None

    async def __call__(self, scope: Scope, receive: ASGIReceiveCallable, send: ASGISendCallable) -> None:
        print("WE CALL THIS NOW")
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])

        def get_header(name: bytes) -> str | None:
            value = headers.get(name)
            return value.decode("latin1") if value else None

        # X-Forwarded-For
        x_for_value = self._get_real_value(self.x_for, get_header(b"x-forwarded-for"))
        if x_for_value:
            scope["client"] = (x_for_value, 0)

        # X-Forwarded-Proto
        x_proto_value = self._get_real_value(self.x_proto, get_header(b"x-forwarded-proto"))
        if x_proto_value:
            scope["scheme"] = x_proto_value

        # X-Forwarded-Host
        x_host_value = self._get_real_value(self.x_host, get_header(b"x-forwarded-host"))
        if x_host_value:
            new_headers = []
            has_host_header = False
            for key, value in scope["headers"]:
                if key == b"host":
                    has_host_header = True
                    new_headers.append((b"host", x_host_value.encode("latin1")))
                else:
                    new_headers.append((key, value))
            if not has_host_header:
                new_headers.append((b"host", x_host_value.encode("latin1")))
            scope["headers"] = new_headers

        # X-Forwarded-Port
        x_port_value = self._get_real_value(self.x_port, get_header(b"x-forwarded-port"))
        if x_port_value:
            host_bytes = dict(scope["headers"]).get(b"host")
            if host_bytes:
                host = host_bytes.decode("latin1")
                # "]" to check for IPv6 address without port
                if ":" in host and not host.endswith("]"):
                    host = host.rsplit(":", 1)[0]
                new_host = f"{host}:{x_port_value}"
                new_headers = []
                for key, value in scope["headers"]:
                    if key == b"host":
                        new_headers.append((b"host", new_host.encode("latin1")))
                    else:
                        new_headers.append((key, value))
                scope["headers"] = new_headers

        # X-Forwarded-Prefix
        x_prefix_value = self._get_real_value(self.x_prefix, get_header(b"x-forwarded-prefix"))
        if x_prefix_value:
            scope["root_path"] = x_prefix_value

        await self.app(scope, receive, send)
