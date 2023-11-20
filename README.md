# scrapy-aiohttp

This library allows integration of
[aiohttp](https://github.com/aio-libs/aiohttp) with
[Scrapy](https://github.com/scrapy/scrapy). It was created to solve problems
that arise when working with sites that restrict access for standard Scrapy requests.

## Installation

To install `scrapy-aiohttp`, use the following command:

```
$ pip install scrapy-aiohttp
```

## Configuration

1. Add the [aiohttp server](https://docs.aiohttp.org/en/stable/web.html) address to `settings.py`
   of your Scrapy project like this:

```python
AIOHTTP_SERVER_URL = "http://localhost:8080/"
```

2. Enable the `scrapy-aiohttp` middleware by adding it to [`DOWNLOADER_MIDDLEWARES`](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html) in your `settings.py` file:

```python
DOWNLOAD_HANDLERS = {
    "scrapy_aiohttp.AiohttpMiddleware": 651,
}
```

3. Set up aiohttp request headers configuration to `settings.py` like this:

```python
from urllib.parse import urlparse

DEFAULT_REQUEST_HEADERS_CONFIG = {
    "Host": lambda request: urlparse(request.match_info.get("url")).hostname,
    "Content-Type": "text/html",
    "User-Agent": None,
}
```

Type `dict[str, str | Callable[[aiohttp.web.Request], str] | None]`

The `DEFAULT_REQUEST_HEADERS_CONFIG` serves as an interface for inheriting headers from a Scrapy request and reusing
them to create an aiohttp request.

Here's how you can customize `DEFAULT_REQUEST_HEADERS_CONFIG`:

* If the header value is a `Callable` object (a function), it gets executed with the HTTP request
  object ([`aiohttp.web.Request`](https://docs.aiohttp.org/en/stable/web_reference.html#:~:text=class%20aiohttp.web.Request))
  as an argument during header construction. Result of the executed function becomes the header value.
   ```python
   {"Host": lambda request: urlparse(request.match_info.get("url")).hostname}
   ```
* If the header value is a `str`, it serves as a static value for the header.
   ```python
   {"Content-Type": "text/html"}
   ```
* If the header value is set to `None`, it implies that the header should be inherited from the request headers. In
  other words, the server will use the same value for this header as it receives in the incoming request.
  ```python
   {"User-Agent": None}
   ```

**Note**: Headers missing in `DEFAULT_REQUEST_HEADERS_CONFIG` **will not be applied** to the aiohttp request.

## Usage

The easiest way to send requests with `aiohttp` is to use `scrapy_aiohttp.AiohttpRequest`.
You can also use regular `scrapy.Request` and the *"aiohttp"* Request meta key:

```python
from scrapy import Spider, Request
from scrapy_aiohttp import AiohttpRequest


class ExampleSpider(Spider):
    name = "example"

    def start_requests(self):
        # use case: scrapy_aiohttp.AiohttpRequest
        yield AiohttpRequest(
            url="https://example.com",
            callback=self.parse
        )
        # use case: scrapy.Request with meta key
        yield Request(
            url="https://example.com",
            callback=self.parse,
            meta={"aiohttp": True},
        )

    def parse(self, response, **kwargs):
        return {"url": response.url}
```
