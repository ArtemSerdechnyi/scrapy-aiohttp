from unittest import TestCase

from scrapy_aiohttp import AiohttpRequest


class TestAiohttpRequest(TestCase):
    def test_init(self):
        url = "https://python.org"
        request = AiohttpRequest(url)
        self.assertEqual(request.url, url)
        self.assertIsNone(request.meta.get("aiohttp"))
        request = AiohttpRequest(url, meta={"aiohttp": True})
        self.assertIsNotNone(request.meta.get("aiohttp"))

    def test_aiohttp_meta_validation(self):
        url = "https://python.org"
        with self.assertRaises(ValueError):
            AiohttpRequest(url=url, meta={'aiohttp': 'invalid'})
        with self.assertRaises(ValueError):
            AiohttpRequest(url=url, meta={'aiohttp': None})
        with self.assertRaises(ValueError):
            AiohttpRequest(url=url, meta={'aiohttp': False})

    def test_original_url_and_target_url(self):
        url = "http://localhost:8080/handler/https://python.org"
        original_url = "https://python.org"
        target_url = "http://localhost:8080/handler"
        request = AiohttpRequest(url)
        self.assertIsNone(request.original_url)
        self.assertIsNone(request.target_url)

        request.original_url = original_url
        request.target_url = target_url
        self.assertEqual(request.original_url, original_url)
        self.assertEqual(request.target_url, target_url)

    def test_repr(self):
        # Test the __repr__ method
        url = "http://localhost:8080/handler/https://python.org"
        request = AiohttpRequest(url)
        self.assertEqual(
            repr(request),
            f"<GET {url}>"
        )

        request.original_url = "https://python.org"
        request.target_url = "http://localhost:8080/handler"
        self.assertEqual(
            repr(request),
            f"<GET https://python.org via http://localhost:8080/handler>"
        )
