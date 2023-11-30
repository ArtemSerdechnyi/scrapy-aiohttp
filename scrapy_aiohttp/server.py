import logging

from typing import Callable
from urllib.parse import urlparse
from functools import partial
from multiprocessing import Process

from aiohttp import web, ClientSession, ClientResponseError, ClientError
from aiohttp.web import middleware, Request
from multidict import CIMultiDictProxy, CIMultiDict

from scrapy_aiohttp.utils import RequestHeaders


class AiohttpServer:
    """
    Aiohttp-based proxy server for forwarding HTTP requests to another server
    """
    __request_headers_config: RequestHeaders = {}

    def __init__(self, host=None, port=None, *, server_url=None):
        self.handlers: set = None
        self._process: Process = None
        self.app = web.Application()
        self.app.middlewares.extend((
            self._handler_validation_middleware,
        ))
        self.app.add_routes((
            web.RouteDef('GET', '/request/{url:https?.*}', self._handle_request, {}),
        ))
        if server_url is not None:
            parsed_url = urlparse(server_url)
            self._host = parsed_url.hostname
            self._port = parsed_url.port
        elif host and port:
            self._host = host
            self._port = port
        else:
            raise AttributeError("Either 'server_url' or both 'host' and 'port' must be specified.")

    def _prerun_configurator(self):
        """
        Configuration before server is started.
        """
        self.handlers = {route.handler for route in self.app.router.routes()}

    def run(self):
        """
        Start server in a separate process.
        """
        self._prerun_configurator()
        self._process = Process(
            target=web.run_app,
            args=(self.app,),
            kwargs={"host": self._host, "port": self._port},
            name="AiohttpServer",
            daemon=True)
        self._process.start()

    def stop(self):
        """
        Terminate server process.
        """
        self._process.terminate()
        self._process.join()
        self._process = None
        server_info = f"Server at http://{self._host}:{self._port}"
        logging.info(f"{server_info} has been stopped.")

    @property
    def request_header_config(self) -> RequestHeaders:
        return self.__request_headers_config

    def add_request_header_config(self, name: str, value: str | Callable[[Request], str] | None = None):
        """
        Add a request header configuration to be included in aiohttp requests.

        This method allows you to specify and configure custom HTTP headers to be added to
        outgoing requests made by the proxy server. You can set the header's name and choose
        its value from various options:

        :param name: Header name (e.g., 'User-Agent', 'Authorization', 'Accept-Language').
        :param value: Header value, which can be one of the string, callable, None.

        - A string: Set a static value for the header (e.g., 'Mozilla/5.0', 'application/json').
        - A callable function: Define a function that takes the current HTTP request object as an argument and returns the dynamic header value.
        - None: Inherit the header value from the incoming request's headers. The proxy server will pass along the same value it receives.
        """
        self.__request_headers_config[name] = value

    def extract_request_header_config(self, request_headers: RequestHeaders):
        """
        Extract request_headers to request_headers_config.
        """
        self.__request_headers_config.update(request_headers)

    @middleware
    async def _handler_validation_middleware(self, request: Request, handler: Callable | partial):
        """
        Middleware to validate the request handler.
        """
        if request.match_info.handler in self.handlers:
            return await handler(request)
        return web.Response(status=404, text="Handler not found in the list of allowed handlers")

    async def _handle_request(self, request: Request) -> web.Response:
        """
        Handle incoming proxy requests by forwarding them to the target server and returning the response.
        """
        url = request.match_info.get("url")
        request_headers = self._get_request_headers(request)
        try:
            async with ClientSession(headers=request_headers, trust_env=True) as session:
                async with session.get(url=url) as response:
                    body = await response.read()
                    status = response.status
        except ClientResponseError as cre:
            logging.warning(f"ClientResponseError: {cre}")
            return web.Response(status=cre.status, text=f"ClientResponseError: {cre}")
        except ClientError as ce:
            logging.warning(f"ClientError: {ce}")
            return web.Response(status=500, text=f"ClientError: {ce}")
        else:
            web_response = web.Response(
                body=body,
                status=status,
                content_type="text/html",
            )
            return web_response

    def _get_request_headers(self, request: Request) -> CIMultiDictProxy:
        """
        Get the request headers, including any custom headers added by the application.
        """
        request_headers = request.headers
        saved_headers = []
        for head, value in self.__request_headers_config.items():
            if head in request_headers:
                if value is None:
                    values = request_headers.getall(head)
                    saved_headers.extend((head, val) for val in values)
                    continue

            if value is None:
                continue
            elif isinstance(value, Callable):
                saved_headers.append((head, value(request)))
            elif isinstance(value, str):
                saved_headers.append((head, value))
            else:
                raise TypeError(f'Value {type(value)} error for head: {head}')

        return CIMultiDictProxy(CIMultiDict(saved_headers))
