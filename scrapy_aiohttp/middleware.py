from urllib.parse import urljoin

from scrapy import Request
from scrapy.http import Response
from scrapy.crawler import Crawler

from scrapy_aiohttp.utils import (
    RequestHeaders,
    ServerNotAliveError,
    SettingVariableNotFoundError
)
from .request import AiohttpRequest
from .server import AiohttpServer


class AiohttpMiddleware:
    """Middleware for integrating aiohttp with Scrapy."""

    _server: AiohttpServer | None = None

    def __init__(self, server_url, aiohttp_request_headers_config):
        self.server_url = server_url

        if self._server is None:
            self.__run_server(server_url, aiohttp_request_headers_config)

    @classmethod
    def __run_server(cls, server_url, aiohttp_request_headers_config: RequestHeaders):
        cls._server = AiohttpServer(server_url=server_url)
        cls._server.extract_request_header_config(aiohttp_request_headers_config)
        cls._server.run()

    @classmethod
    def _force_stop_server(cls):
        if cls._server is None:
            raise ServerNotAliveError()
        cls._server.stop()
        cls._server = None

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        settings = crawler.settings
        server_url = settings.get("AIOHTTP_SERVER_URL")
        aiohttp_request_headers_config = settings.get("AIOHTTP_REQUEST_HEADERS_CONFIG")

        if server_url is None:
            raise SettingVariableNotFoundError("AIOHTTP_SERVER_URL")
        if aiohttp_request_headers_config is None:
            raise SettingVariableNotFoundError("AIOHTTP_REQUEST_HEADERS_CONFIG")

        return cls(
            server_url,
            aiohttp_request_headers_config,
        )

    def process_request(self, request: AiohttpRequest | Request, spider) -> AiohttpRequest | None:
        """Process the Scrapy request and convert it to an AiohttpRequest."""

        if request.meta.get("_original_url"):
            return
        elif request.meta.get("aiohttp") is True:
            request = self._convert_request(request)

        if not isinstance(request, AiohttpRequest):
            return

        new_request = request.replace(
            url=self._convert_url("/request", request.url)
        )
        new_request.original_url = request.url
        new_request.target_url = new_request.url.replace(request.url, '').rstrip('/')
        return new_request

    @staticmethod
    def _convert_request(request: Request) -> AiohttpRequest:
        """Convert a Scrapy Request to an AiohttpRequest."""

        if isinstance(request, AiohttpRequest):
            return request
        return AiohttpRequest(
            url=request.url,
            callback=request.callback,
            method=request.method,
            headers=request.headers,
            body=request.body,
            cookies=request.cookies,
            meta=request.meta,
        )

    def _convert_url(self, handler: str, url: str) -> str:
        server_url = self.server_url
        target_url = urljoin(server_url, handler).rstrip('/')
        site_url = url.lstrip('/')
        return f"{target_url}/{site_url}"

    def process_response(self, request: Request | AiohttpRequest, response: Response, spider):
        if not isinstance(request, AiohttpRequest):
            return response

        origin_url = request.original_url
        response._set_url(origin_url)
        return response
