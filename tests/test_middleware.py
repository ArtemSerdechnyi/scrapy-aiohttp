from unittest import TestCase

from scrapy import Request
from scrapy.crawler import Crawler
from scrapy.http import Response

from scrapy_aiohttp import AiohttpRequest, AiohttpMiddleware, AiohttpServer
from scrapy_aiohttp.utils import SimpleSpider, ServerNotAliveError, DEFAULT_REQUEST_HEADERS_CONFIG


class TestAiohttpMiddleware(TestCase):
    middleware: AiohttpMiddleware

    spider_inst = SimpleSpider()
    crawler = Crawler(
        spidercls=SimpleSpider,
        settings={
            "AIOHTTP_SERVER_URL": "http://localhost:8080/",
            "AIOHTTP_REQUEST_HEADERS_CONFIG": DEFAULT_REQUEST_HEADERS_CONFIG,
        },
    )

    @classmethod
    def setUpClass(cls):
        cls.middleware = AiohttpMiddleware.from_crawler(cls.crawler)
        cls.middleware._force_stop_server()

    @classmethod
    def tearDown(cls):
        if cls.middleware._server is not None:
            cls.middleware._force_stop_server()

    def test_run_server(self):
        middleware = AiohttpMiddleware.from_crawler(self.crawler)
        self.assertIsInstance(middleware._server, AiohttpServer)
        self.assertTrue(middleware._server._process.is_alive())

    def test_force_stop_server(self):
        middleware = AiohttpMiddleware.from_crawler(self.crawler)
        middleware._force_stop_server()
        self.assertIsNone(middleware._server)
        with self.assertRaises(ServerNotAliveError):
            middleware._force_stop_server()

    def test_from_crawler(self):
        self.assertIsInstance(self.middleware, AiohttpMiddleware)
        self.assertEqual(self.middleware.server_url, self.crawler.settings["AIOHTTP_SERVER_URL"])

    def test_convert_request(self):
        url = "https://www.python.org/"
        meta = {"test_meta": "test_meta"}
        requests = (
            Request(url=url, meta=meta),
            AiohttpRequest(url=url, meta=meta),
        )
        for request in requests:
            result = self.middleware._convert_request(request)
            self.assertIsInstance(result, AiohttpRequest)
            self.assertEqual(result.__dict__, request.__dict__)

    def test_convert_url(self):
        url = "https://www.python.org/"
        expected_result = f"http://localhost:8080/handler/{url}"
        self.assertEqual(self.middleware._convert_url("/handler", url), expected_result)
        self.assertEqual(self.middleware._convert_url("handler", url), expected_result)
        self.assertEqual(self.middleware._convert_url("handler/", url), expected_result)

    def test_process_request_valid(self):
        url = "https://www.python.org/"
        server_url = "http://localhost:8080/"
        valid_requests = (
            Request(url=url, meta={"aiohttp": True}),
            AiohttpRequest(url=url),
        )
        for request in valid_requests:
            process_request_result = self.middleware.process_request(request, self.spider_inst)
            self.assertIsInstance(process_request_result, AiohttpRequest)
            self.assertEqual(
                process_request_result.meta.get("_original_url"),
                request.url
            )
            self.assertEqual(
                process_request_result.meta.get("_target_url"),
                server_url + "request"
            )

    def test_process_request_invalid(self):
        url = "https://www.python.org/"
        invalid_requests = (
            Request(url=url),
            Request(url=url, meta={"aiohttp": False}),
            AiohttpRequest(url=f"http://localhost:8080/handler/{url}", meta={"_original_url": url})
        )
        for request in invalid_requests:
            result = self.middleware.process_request(request, self.spider_inst)
            self.assertIsNone(result)

    def test_process_response_valid(self):
        url = "http://localhost:8080/request/https://www.python.org/"
        request = AiohttpRequest(url=url, meta={
            "_original_url": "https://www.python.org/",
            "_target_url": "http://localhost:8080/request"
        })
        response = Response(url=url)
        result = self.middleware.process_response(request, response, self.spider_inst)

        self.assertIsInstance(result, Response)
        self.assertEqual(result.url, "https://www.python.org/")

    def test_process_response_invalid(self):
        url = "https://www.python.org/"
        request = Request(url=url)
        response = Response(url=url)
        result = self.middleware.process_response(request, response, self.spider_inst)
        self.assertEqual(result.url, "https://www.python.org/")
