class HSTSResponse:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message) -> None:
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
