from scrapy import Spider


class SimpleSpider(Spider):
    name = "simple_spider"
    allowed_domains = ["python.org"]
    start_urls = ["https://python.org"]

    def parse(self, response):
        pass
