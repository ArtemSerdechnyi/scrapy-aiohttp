from typing import TypeAlias, Callable

import aiohttp.web

RequestHeaders: TypeAlias = dict[str, str | Callable[[aiohttp.web.Request], str] | None]
