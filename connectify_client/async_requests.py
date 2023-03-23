import asyncio
import aiohttp
import json
from typing import TypeVar, Callable, List, Any, Dict, Awaitable

T = TypeVar("T")


class AsyncRequests:
    """Class for making parallel async requests to a server"""

    def __init__(
        self,
        parallel_requests: int = 100,
        limit_per_host: int = 100,
        limit: int = 0,
        ttl_dns_cache: int = 300,
    ) -> None:
        self.conn = aiohttp.TCPConnector(
            limit_per_host=limit_per_host,
            limit=limit,
            ttl_dns_cache=ttl_dns_cache,
        )
        self.semaphore = asyncio.Semaphore(parallel_requests)
        self.session = aiohttp.ClientSession(connector=self.conn)

    async def gather_with_concurrency(
        self,
        func: Callable[..., Awaitable[T]],
        reqs: List[Dict[str, Any]],
        resp_dict: Dict[int, T],
    ) -> None:
        n = len(reqs)

        async def get(
            id: int, session: aiohttp.client.ClientSession, **kwargs
        ) -> None:
            async with self.semaphore:
                resp_dict[id] = await func(session, **kwargs)

        await asyncio.gather(
            *(
                get(id, self.session, **kwargs)
                for id, kwargs in enumerate(reqs)
            )
        )

    def run(
        self, func: Callable[..., Awaitable[T]], reqs: List[Dict[str, Any]]
    ) -> List[T]:
        resp_dict: Dict[int, T] = {}
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            self.gather_with_concurrency(func, reqs, resp_dict)
        )
        return [resp_dict[id] for id in range(len(reqs))]
    
    def close(self) -> None:
        self.conn.close()
