import os
import asyncio
from typing import Dict, List, AsyncGenerator

USE_REDIS = os.environ.get("USE_REDIS_STREAM", "false").lower() == "true"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

class RunStreamHub:
    def __init__(self):
        self.queues: Dict[int, List[asyncio.Queue]] = {}

    # --- Local in-memory mode ---
    def subscribe_local(self, run_id: int) -> asyncio.Queue:
        q = asyncio.Queue()
        self.queues.setdefault(run_id, []).append(q)
        return q

    async def publish_local(self, run_id: int, message: str):
        for q in self.queues.get(run_id, []):
            await q.put(message)

    def unsubscribe_local(self, run_id: int, q: asyncio.Queue):
        if run_id in self.queues and q in self.queues[run_id]:
            self.queues[run_id].remove(q)

    # --- Redis-backed mode ---
    async def publish(self, run_id: int, message: str):
        if USE_REDIS:
            from redis import asyncio as aioredis  # lazy import
            r = aioredis.from_url(REDIS_URL, decode_responses=True)
            await r.publish(f"runs:{run_id}", message)
        else:
            await self.publish_local(run_id, message)

    async def stream(self, run_id: int) -> AsyncGenerator[str, None]:
        """Yield SSE messages from local queue or Redis pubsub."""
        if USE_REDIS:
            from redis import asyncio as aioredis
            r = aioredis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(f"runs:{run_id}")
            try:
                async for msg in pubsub.listen():
                    if msg.get("type") == "message":
                        data = msg.get("data")
                        if isinstance(data, bytes):
                            data = data.decode("utf-8", errors="ignore")
                        yield data
            finally:
                try:
                    await pubsub.unsubscribe(f"runs:{run_id}")
                except Exception:
                    pass
        else:
            q = self.subscribe_local(run_id)
            try:
                while True:
                    msg = await q.get()
                    yield msg
            finally:
                self.unsubscribe_local(run_id, q)

hub = RunStreamHub()
