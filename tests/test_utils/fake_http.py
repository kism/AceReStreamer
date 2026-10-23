from typing import Any, Self, TypedDict

import httpx2


class FakeResponseDef(TypedDict):
    status: int
    data: bytes | str


class FakeSession:
    """Stand-in for httpx2.AsyncClient, serving canned responses by URL (404 for unknown URLs)."""

    def __init__(self, responses: dict[str, FakeResponseDef]) -> None:
        self.responses = responses
        self.closed = False

    def build_request(self, method: str, url: str, **kwargs: Any) -> httpx2.Request:
        return httpx2.Request(method, url)

    async def send(self, request: httpx2.Request, **kwargs: Any) -> httpx2.Response:
        response_def = self.responses.get(str(request.url), {"status": 404, "data": b""})
        return httpx2.Response(
            response_def["status"],
            content=response_def["data"],
            headers={"content-type": "application/octet-stream"},
            request=request,
        )

    async def get(self, url: str, **kwargs: Any) -> httpx2.Response:
        return await self.send(self.build_request("GET", url))

    async def __aenter__(self) -> Self:
        self.closed = False
        return self

    async def __aexit__(self, *args: object) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.closed = True
