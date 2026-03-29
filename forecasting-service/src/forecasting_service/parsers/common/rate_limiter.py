import time
import random
from collections import deque

from loguru import logger


class AdaptiveRateLimiter:
    def __init__(
        self,
        base_page_delay: tuple[float, float] = (5.0, 15.0),
        base_detail_delay: tuple[float, float] = (30.0, 60.0),
        action_delay: tuple[float, float] = (1.0, 3.0),
        long_pause_range: tuple[float, float] = (60.0, 120.0),
        section_pause_range: tuple[float, float] = (20.0, 40.0),
        window_size: int = 15,
        captcha_threshold: int = 2,
        max_multiplier: float = 5.0,
    ):
        self._base_page_delay = base_page_delay
        self._base_detail_delay = base_detail_delay
        self._action_delay = action_delay
        self._long_pause_range = long_pause_range
        self._section_pause_range = section_pause_range
        self._max_multiplier = max_multiplier

        self._multiplier: float = 1.0
        self._request_count: int = 0
        self._captcha_count: int = 0

        self._window_size = window_size
        self._captcha_threshold = captcha_threshold
        self._results: deque[bool] = deque(maxlen=window_size)

        self._next_long_pause_at: int = random.randint(8, 15)

    def record_success(self) -> None:
        self._results.append(True)
        self._try_decrease_multiplier()

    def record_captcha(self) -> None:
        self._results.append(False)
        self._captcha_count += 1
        self._try_increase_multiplier()

    def record_error(self) -> None:
        self._results.append(False)

    def wait_between_pages(self) -> None:
        self._request_count += 1

        if self._should_long_pause():
            self._long_pause()
            self._schedule_next_long_pause(min_interval=8, max_interval=15)
            return

        delay = self._apply_multiplier(self._base_page_delay)
        logger.debug(
            f"  Пауза стр.: {delay:.1f}с (×{self._multiplier:.1f})"
        )
        time.sleep(delay)

    def wait_between_details(self) -> None:
        self._request_count += 1

        if self._should_long_pause():
            self._long_pause()
            self._schedule_next_long_pause(min_interval=5, max_interval=10)
            return

        delay = self._apply_multiplier(self._base_detail_delay)
        logger.debug(
            f"  Пауза деталь: {delay:.1f}с (×{self._multiplier:.1f})"
        )
        time.sleep(delay)

    def wait_between_actions(self) -> None:
        delay = random.uniform(*self._action_delay)
        time.sleep(delay)

    def wait_on_captcha(self) -> None:
        delay = random.uniform(120, 300) * self._multiplier
        delay = min(delay, 600)
        logger.warning(f"  Пауза CAPTCHA: {delay:.0f}с")
        time.sleep(delay)

    def wait_between_sections(self) -> None:
        delay = self._apply_multiplier(self._section_pause_range)
        logger.info(f"  Пауза раздел: {delay:.1f}с")
        time.sleep(delay)

    # ── Свойства ──────────────────────────────────────

    @property
    def total_requests(self) -> int:
        return self._request_count

    @property
    def multiplier(self) -> float:
        return self._multiplier

    @property
    def total_captchas(self) -> int:
        return self._captcha_count


    def _apply_multiplier(
        self, delay_range: tuple[float, float]
    ) -> float:
        base = random.uniform(*delay_range)
        return base * self._multiplier

    def _try_decrease_multiplier(self) -> None:
        if len(self._results) < self._window_size:
            return
        if self._multiplier <= 1.0:
            return

        recent_failures = sum(1 for r in self._results if not r)
        if recent_failures == 0:
            old = self._multiplier
            self._multiplier = max(1.0, self._multiplier * 0.8)
            logger.debug(
                f"  Множитель: {old:.1f}x → {self._multiplier:.1f}x"
            )

    def _try_increase_multiplier(self) -> None:
        recent_captchas = sum(1 for r in self._results if not r)

        if recent_captchas >= self._captcha_threshold:
            old = self._multiplier
            self._multiplier = min(
                self._multiplier * 2.0,
                self._max_multiplier,
            )
            logger.warning(
                f"  Множитель: {old:.1f}x → {self._multiplier:.1f}x "
                f"({recent_captchas} CAPTCHA в окне)"
            )

    def _should_long_pause(self) -> bool:
        return self._request_count >= self._next_long_pause_at

    def _long_pause(self) -> None:
        delay = self._apply_multiplier(self._long_pause_range)
        delay = min(delay, 300)
        logger.info(
            f"  Длинная пауза: {delay:.0f}с "
            f"({self._request_count} запросов)"
        )
        time.sleep(delay)

    def _schedule_next_long_pause(
        self, min_interval: int, max_interval: int
    ) -> None:
        self._next_long_pause_at = (
            self._request_count + random.randint(min_interval, max_interval)
        )