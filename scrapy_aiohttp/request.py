from typing import Optional, Callable, List, Union

from scrapy import Request


class AiohttpRequest(Request):
    """
    Base on Scrapy Request class for handling Aiohttp requests.
    """

    def __init__(
            self,
            url: str,
            callback: Optional[Callable] = None,
            method: str = "GET",
            headers: Optional[dict] = None,
            body: Optional[Union[bytes, str]] = None,
            cookies: Optional[Union[dict, List[dict]]] = None,
            meta: Optional[dict] = None,
            encoding: str = "utf-8",
            priority: int = 0,
            dont_filter: bool = False,
            errback: Optional[Callable] = None,
            flags: Optional[List[str]] = None,
            cb_kwargs: Optional[dict] = None,
    ) -> None:
        if meta is not None:
            if "aiohttp" in meta:
                if not isinstance(meta.get("aiohttp"), bool):
                    raise ValueError("'aiohttp' key in meta must be a boolean value.")
            if meta.get("aiohttp", None) is False:
                raise ValueError("Aiohttp request should not have 'aiohttp' key set to False in meta.")

        super().__init__(url, callback, method, headers, body, cookies, meta,
                         encoding, priority, dont_filter, errback, flags, cb_kwargs)

    @property
    def original_url(self):
        return self.meta.get("_original_url")

    @original_url.setter
    def original_url(self, value):
        self.meta["_original_url"] = value

    @property
    def target_url(self):
        return self.meta.get("_target_url")

    @target_url.setter
    def target_url(self, value):
        self.meta["_target_url"] = value

    def __repr__(self):
        if self.original_url is None or self.target_url is None:
            return super().__repr__()
        return f"<{self.method} {self.original_url} via {self.target_url}>"
