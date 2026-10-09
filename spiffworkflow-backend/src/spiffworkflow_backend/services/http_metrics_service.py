"""Record HTTP metrics after Connexion has converted exceptions into responses."""

from functools import lru_cache
from time import perf_counter

from flask import request
from prometheus_client import CollectorRegistry
from prometheus_client import Counter
from prometheus_client import Histogram
from starlette.types import ASGIApp
from starlette.types import Message
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send

_METADATA_KEY = "spiff.http_metrics"


class HttpMetrics:
    def __init__(self, registry: CollectorRegistry) -> None:
        self.total = Counter("flask_http_request_total", "Total number of HTTP requests", ("method", "status"), registry=registry)
        self.duration = Histogram(
            "flask_http_request_duration_seconds",
            "Flask HTTP request duration in seconds",
            ("method", "endpoint", "status"),
            registry=registry,
        )
        self.exceptions = Counter(
            "flask_http_request_exceptions_total",
            "Total number of HTTP requests which resulted in an exception",
            ("method", "status"),
            registry=registry,
        )


@lru_cache
def http_metrics_for_registry(registry: CollectorRegistry) -> HttpMetrics:
    # Application factories may share a registry within the same process.
    return HttpMetrics(registry)


def capture_http_metric_endpoint() -> None:
    scope = request.environ.get("asgi.scope")
    if scope is not None and _METADATA_KEY in scope:
        scope[_METADATA_KEY]["endpoint"] = str(request.endpoint)


def capture_http_metric_exception(exception: BaseException | None) -> None:
    scope = request.environ.get("asgi.scope")
    if exception is not None and scope is not None and _METADATA_KEY in scope:
        scope[_METADATA_KEY]["exception"] = True


class HttpMetricsMiddleware:
    def __init__(self, app: ASGIApp, metrics: HttpMetrics) -> None:
        self.app = app
        self.metrics = metrics

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] == "/metrics":
            await self.app(scope, receive, send)
            return

        # A shared object survives shallow scope copies made by routing middleware.
        metadata = {"endpoint": "None", "exception": False}
        scope[_METADATA_KEY] = metadata
        started = perf_counter()
        recorded = False

        async def record_response(message: Message) -> None:
            nonlocal recorded
            if message["type"] == "http.response.start" and not recorded:
                recorded = True
                status = str(message["status"])
                method = scope["method"]
                self.metrics.total.labels(method=method, status=status).inc()
                self.metrics.duration.labels(method=method, endpoint=metadata["endpoint"], status=status).observe(
                    max(perf_counter() - started, 0)
                )
                if metadata["exception"]:
                    self.metrics.exceptions.labels(method=method, status=status).inc()
            await send(message)

        await self.app(scope, receive, record_response)
