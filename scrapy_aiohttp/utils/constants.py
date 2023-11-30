from urllib.parse import urlparse

from .types import RequestHeaders

DEFAULT_AIOHTTP_REQUEST_HEADERS_CONFIG: RequestHeaders = {
        # If the header value is a Callable function,
        # the function is executed with the HTTP request object (request: aiohttp.web.Request)
        # as an argument when constructing the header.
        "Host": lambda request: urlparse(request.match_info.get("url")).hostname,

        # If the header value is a string, it is used as a static value for the header.
        "Content-Type": "text/html",

        # If the header value is set to None, it implies that the header should be
        # inherited from the request headers. In other words, the server will use the
        # same value for this header as it receives in the incoming request.
        "User-Agent": None,
}
