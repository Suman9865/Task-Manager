
import uuid

from app.request_context import request_id_context


class RequestIDMiddleware:

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):

        # Skip non-HTTP requests
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Set request ID in the current context
        token = request_id_context.set(request_id)

        async def send_with_request_id(message):

            if message["type"] == "http.response.start":

                headers = list(message.get("headers", []))

                headers.append(
                    (
                        b"x-request-id",
                        request_id.encode("ascii")
                    )
                )

                message = {
                    **message,
                    "headers": headers
                }

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)

        finally:
            # Restore the previous context
            request_id_context.reset(token)
