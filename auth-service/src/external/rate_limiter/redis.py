import time

import redis.asyncio as redis

from src.core.exceptions import RateLimitExceededError
from src.core.protocols import RateLimiterProtocol

_RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local max_attempts = tonumber(ARGV[3])
local cutoff = now - window

redis.call('ZREMRANGEBYSCORE', key, 0, cutoff)

local count = redis.call('ZCARD', key)

if count >= max_attempts then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local retry_after = 0
    if #oldest > 0 then
        retry_after = math.ceil(oldest[2] + window - now)
    end
    return {0, retry_after}
end

redis.call('ZADD', key, now, tostring(now) .. ':' .. math.random(100000))
redis.call('EXPIRE', key, window + 1)

local remaining = max_attempts - count - 1
return {1, remaining}
"""


class RedisRateLimiter(RateLimiterProtocol):
    def __init__(self, redis_url: str, prefix: str = "rl:"):
        self._redis = redis.from_url(
            redis_url, decode_responses=True,
        )
        self._prefix = prefix
        self._script = None

    async def _get_script(self):
        if self._script is None:
            self._script = self._redis.register_script(
                _RATE_LIMIT_SCRIPT,
            )
        return self._script

    async def check_rate_limit(
        self, key: str, max_attempts: int, window_seconds: int,
    ) -> None:
        full_key = f"{self._prefix}{key}"
        now = time.time()

        script = await self._get_script()
        result = await script(
            keys=[full_key],
            args=[now, window_seconds, max_attempts],
        )

        allowed = result[0]
        if not allowed:
            retry_after = max(1, result[1])
            raise RateLimitExceededError(retry_after=retry_after)

    async def reset(self, key: str) -> None:
        await self._redis.delete(f"{self._prefix}{key}")

    async def get_remaining(
        self, key: str, max_attempts: int, window_seconds: int,
    ) -> tuple[int, int]:
        full_key = f"{self._prefix}{key}"
        now = time.time()
        cutoff = now - window_seconds

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(full_key, 0, cutoff)
        pipe.zcard(full_key)
        pipe.zrange(full_key, 0, 0, withscores=True)
        results = await pipe.execute()

        count = results[1]
        remaining = max(0, max_attempts - count)
        oldest_entries = results[2]

        if oldest_entries:
            reset_in = int(
                oldest_entries[0][1] + window_seconds - now
            ) + 1
        else:
            reset_in = 0

        return remaining, reset_in

    async def close(self) -> None:
        await self._redis.close()