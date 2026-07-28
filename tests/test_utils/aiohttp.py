import json
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Self, TypedDict

import aiohttp
from multidict import CIMultiDict, CIMultiDictProxy
from yarl import URL

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Generator

    from aiohttp.pytest_plugin import AiohttpServer
    from pytest_mock import MockerFixture  # pragma: no cover
else:
    MockerFixture = object
    AiohttpServer = object
    AsyncIterator = object
    Generator = object


class FakeResponseDef(TypedDict):
    status: int
    data: bytes | str


class FakeContent:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._position = 0

    async def read(self, size: int = -1) -> bytes:
        if size == -1:
            result = self._data[self._position :]
            self._position = len(self._data)
            return result
        result = self._data[self._position : self._position + size]
        self._position += size
        return result

    async def iter_chunked(self, n: int) -> AsyncIterator[bytes]:
        while chunk := await self.read(n):
            yield chunk


class FakeResponse:
    def __init__(self, data: str | bytes, status: int = 200, url: str = "") -> None:
        if isinstance(data, str):
            self._data = data.encode()
        else:
            self._data = data
        self.status = status
        self.content = FakeContent(self._data)
        self.url = URL(url)
        self.headers = CIMultiDictProxy(CIMultiDict([("content-type", "application/octet-stream")]))

    def raise_for_status(self) -> None:
        if self.status >= HTTPStatus.BAD_REQUEST:
            # Create a minimal request_info to avoid AttributeError when converting to string
            request_info = aiohttp.RequestInfo(
                url=self.url,
                method="GET",
                headers=CIMultiDictProxy(CIMultiDict()),
                real_url=self.url,
            )
            raise aiohttp.ClientResponseError(
                request_info=request_info,
                history=(),
                status=self.status,
            )

    async def json(self) -> Any:
        return json.loads(self._data.decode())

    async def text(self, encoding: str = "utf-8") -> str:
        return self._data.decode(encoding)

    async def read(self) -> bytes:
        return self._data

    async def raw_headers(self) -> bytes:
        return b""

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    def __await__(self) -> Generator[Any, None, Self]:
        # aiohttp's session.get() is both awaitable and an async context manager
        async def _coro() -> Self:
            return self

        return _coro().__await__()

    def close(self) -> None:
        pass


class FakeSession:
    def __init__(self, responses: dict[str, FakeResponseDef]) -> None:
        self.responses = responses
        self.closed = False

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        response_def = self.responses.get(url)
        if response_def is None:
            return FakeResponse(data=b"", status=404, url=url)

        return FakeResponse(data=response_def["data"], status=response_def["status"], url=url)

    async def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        response_def = self.responses.get(url)
        if response_def is None:
            return FakeResponse(data=b"", status=404, url=url)

        return FakeResponse(data=response_def["data"], status=response_def["status"], url=url)

    async def send(self, *args: object, **kwargs: object) -> FakeResponse:
        return FakeResponse(data=b"", status=404)

    async def __aenter__(self) -> Self:
        self.closed = False
        return self

    async def __aexit__(self, *args: object) -> None:
        self.closed = True

    async def close(self) -> None:
        self.closed = True
