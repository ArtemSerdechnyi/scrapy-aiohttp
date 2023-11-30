# scrapy-aiohttp
[![version](https://img.shields.io/pypi/v/scrapy-aiohttp.svg)](https://pypi.org/project/scrapy_aiohttp/)
[![pyversions](https://img.shields.io/pypi/pyversions/scrapy_aiohttp.svg)](https://pypi.org/project/scrapy_aiohttp/)
[![Tests](https://github.com/ArtemSerdechnyi/scrapy-aiohttp/actions/workflows/test.yaml/badge.svg)](https://github.com/ArtemSerdechnyi/scrapy-aiohttp/actions/workflows/test.yaml)
[![codecov](https://codecov.io/github/ArtemSerdechnyi/scrapy-aiohttp/graph/badge.svg?token=9PQ8BISKN4)](https://codecov.io/github/ArtemSerdechnyi/scrapy-aiohttp)


This library simply integrates
[aiohttp](https://github.com/aio-libs/aiohttp) with
[Scrapy](https://github.com/scrapy/scrapy), 
addressing challenges encountered when dealing with websites imposing 
restrictions on standard Scrapy requests. Specifically, it simply 
resolves the 403 Forbidden issue often encountered when utilizing 
Scrapy's built-in requests.

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
from scrapy_aiohttp.utils import DEFAULT_AIOHTTP_REQUEST_HEADERS_CONFIG

AIOHTTP_REQUEST_HEADERS_CONFIG = DEFAULT_AIOHTTP_REQUEST_HEADERS_CONFIG
```

Type `dict[str, str | Callable[[aiohttp.web.Request], str] | None]`

The `AIOHTTP_REQUEST_HEADERS_CONFIG` serves as an interface for inheriting headers from a Scrapy request and reusing
them to create an aiohttp request.

`DEFAULT_AIOHTTP_REQUEST_HEADERS_CONFIG` is initialized with the values given below in the example.

Here's how you can customize `AIOHTTP_REQUEST_HEADERS_CONFIG` using the following guidelines:

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

**Note**: Headers missing in `AIOHTTP_REQUEST_HEADERS_CONFIG` **will not be applied** to the aiohttp request! 

Ensure that all necessary headers are defined to meet your specific requirements.

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

