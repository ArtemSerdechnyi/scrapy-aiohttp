import asyncio
from unittest import TestCase, IsolatedAsyncioTestCase

from multidict import CIMultiDictProxy
from aiohttp import web, ClientConnectorError, ClientSession, ClientResponse
from aiohttp.test_utils import make_mocked_request, AppRunner, AioHTTPTestCase

from scrapy_aiohttp import AiohttpServer

mock_request = make_mocked_request(
    method="GET",
    path=f"/request/https://www.python.org/",
    headers={},
    match_info={"url": "https://www.python.org/"}
)


class TestAiohttpServer(TestCase):

    def test_init_with_server_url(self):
        server = AiohttpServer(server_url="http://localhost:8080/")
        self.assertEqual(server._host, "localhost")
        self.assertEqual(server._port, 8080)

    def test_init_with_host_and_port(self):
        server = AiohttpServer(host="localhost", port=8080)
        self.assertEqual(server._host, "localhost")
        self.assertEqual(server._port, 8080)

    def test_init_missing_args(self):
        with self.assertRaises(AttributeError):
            AiohttpServer()

    def test_add_and_get_request_header(self):
        server = AiohttpServer(host="localhost", port=8080)
        self.assertNotIn("test_add_and_get_request_header", server.request_header_config)
        server.add_request_header_config("test_add_and_get_request_header", "test")
        self.assertIn("test_add_and_get_request_header", server.request_header_config)

    def test_extract_request_header_config(self):
        server = AiohttpServer(host="localhost", port=8080)
        self.assertNotIn("test_extract_request_header_config", server.request_header_config)
        server.extract_request_header_config({"test_extract_request_header_config": "test"})
        self.assertIn("test_extract_request_header_config", server.request_header_config)

    def test_get_request_headers(self):
        server = AiohttpServer(host="localhost", port=8080)
        server.add_request_header_config("test None", None)

        request = make_mocked_request(
            method="GET",
            path=f"/request/https://www.python.org/",
            headers={"User-Agent": "test user agent", "must delete": "", },
            match_info={"url": "https://www.python.org/"}
        )
        result: CIMultiDictProxy = server._get_request_headers(request)
        self.assertIsInstance(result, CIMultiDictProxy)
        self.assertEqual(result.get("User-Agent"), "test user agent")
        self.assertEqual(result.get("Host"), "www.python.org")
        self.assertEqual(result.get("Content-Type"), "text/html")
        self.assertFalse("test None" in result)
        self.assertFalse("must delete" in result)

        server.add_request_header_config("raise type error", [])
        self.assertTrue("raise type error" in server.request_header_config)
        with self.assertRaises(TypeError):
            server._get_request_headers(request)


class AsyncTestAiohttpServer(IsolatedAsyncioTestCase):

    async def test_run_and_stop(self):
        async def send_request_get_status(url):
            async with ClientSession() as session:
                async with session.get(url=url) as r:
                    pass
            return r.status

        server = AiohttpServer(server_url="http://localhost:8080/")
        server.run()
        await asyncio.sleep(0.1)
        self.assertTrue(server.handlers)
        status = await send_request_get_status("http://localhost:8080/error")
        self.assertEqual(status, 404)
        server.stop()
        with self.assertRaises(ClientConnectorError):
            await send_request_get_status("http://localhost:8080/error")

    async def test_handler_validation_middleware_valid(self):
        async def handler(r):
            return True

        server = AiohttpServer(host="localhost", port=8080)
        server.handlers = {mock_request.match_info.handler}
        result = await server._handler_validation_middleware(mock_request, handler)
        self.assertTrue(result)

    async def test_handler_validation_middleware_invalid(self):
        server = AiohttpServer(host="localhost", port=8080)
        server.handlers = {}
        result = await server._handler_validation_middleware(mock_request, lambda request: True)
        self.assertIsInstance(result, web.Response)
        self.assertEqual(result.status, 404)

    async def test_handle_request_valid(self):
        server = AiohttpServer(host="localhost", port=8080)
        response = await server._handle_request(mock_request)
        self.assertIsInstance(response, web.Response)
        self.assertEqual(response.status, 200)

    async def test_handle_request_invalid(self):
        server = AiohttpServer(host="localhost", port=8080)
        request = make_mocked_request(
            method="GET",
            path=f"/request/https://www.python.org/",
            headers={},
            match_info={"url": "https://www.%.org/"}
        )
        response = await server._handle_request(request)
        ce = "ClientError: Cannot connect to host www.%.org:443 ssl:default [Name or service not known]"
        self.assertEqual(response.text, ce)
