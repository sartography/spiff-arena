from starlette.types import ASGIApp
from starlette.types import Message
from starlette.types import Receive
from starlette.types import Scope
from starlette.types import Send


class HSTSResponse:
    def __init__(self, app: ASGIApp) -> None:
        self.app: ASGIApp = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))

                headers.append(
                    (
                        b"strict-transport-security",
                        b"max-age=63072000; includeSubDomains; preload",
                    )
                )

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_wrapper)
