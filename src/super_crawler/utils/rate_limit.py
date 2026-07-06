"""速率限制器"""

from __future__ import annotations

import time
import threading
from collections import deque


class RateLimiter:
    """令牌桶速率限制器（线程安全）。

    用法:
        limiter = RateLimiter(max_per_minute=30)
        limiter.wait()  # 阻塞直到可以发请求
        # ... 发请求 ...
    """

    def __init__(self, max_per_minute: int = 30):
        self.max_per_minute = max_per_minute
        self.min_interval = 60.0 / max_per_minute
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def wait(self) -> float:
        """等待直到可以发送请求。返回实际等待的秒数。"""
        waited = 0.0
        with self._lock:
            now = time.monotonic()
            # 清理超过60秒的记录
            while self._timestamps and self._timestamps[0] < now - 60:
                self._timestamps.popleft()

            if len(self._timestamps) >= self.max_per_minute:
                # 需要等待
                oldest = self._timestamps[0]
                wait_until = oldest + 60
                waited = wait_until - now
                if waited > 0:
                    time.sleep(waited)
                    now = time.monotonic()

            self._timestamps.append(now)
        return waited

    @property
    def available(self) -> int:
        """当前可用请求数"""
        now = time.monotonic()
        with self._lock:
            while self._timestamps and self._timestamps[0] < now - 60:
                self._timestamps.popleft()
            return max(0, self.max_per_minute - len(self._timestamps))
