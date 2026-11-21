from httpx import AsyncClient

http_client: AsyncClient | None = None


def set_http_client(client: AsyncClient | None) -> None:
    global http_client
    http_client = client


def get_http_client() -> AsyncClient:
    if http_client is None:
        raise RuntimeError("HTTP client has not been initialized by application lifespan")
    return http_client
