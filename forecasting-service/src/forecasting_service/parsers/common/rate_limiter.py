"""
Adaptive rate limiter.
Автоматически увеличивает задержки при частых блокировках.
"""

import time
import random
from collections import deque
from loguru import logger


class AdaptiveRateLimiter:
    """
    Адаптивный ограничитель частоты.

    Увеличивает задержки при частых CAPTCHA/ошибках.
    Уменьшает обратно при стабильной работе.
    """

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
        self.base_page_delay = base_page_delay
        self.base_detail_delay = base_detail_delay
        self.action_delay = action_delay
        self.long_pause_range = long_pause_range
        self.section_pause_range = section_pause_range
        self.max_multiplier = max_multiplier

        self._multiplier = 1.0
        self._request_count = 0
        self._captcha_count = 0

        self._window_size = window_size
        self._captcha_threshold = captcha_threshold
        self._results: deque[bool] = deque(maxlen=window_size)

        self._next_long_pause_at = random.randint(8, 15)

    def record_success(self) -> None:
        """Записать успешный запрос."""
        self._results.append(True)
        if len(self._results) >= self._window_size:
            recent_failures = sum(
                1 for r in self._results if not r
            )
            if recent_failures == 0 and self._multiplier > 1.0:
                self._multiplier = max(
                    1.0, self._multiplier * 0.8
                )
                logger.debug(
                    f" Множитель: {self._multiplier:.1f}x"
                )

    def record_captcha(self) -> None:
        """Записать CAPTCHA."""
        self._results.append(False)
        self._captcha_count += 1

        recent_captchas = sum(
            1 for r in self._results if not r
        )

        if recent_captchas >= self._captcha_threshold:
            old = self._multiplier
            self._multiplier = min(
                self._multiplier * 2.0,
                self.max_multiplier,
            )
            logger.warning(
                f" Множитель: {old:.1f}x → "
                f"{self._multiplier:.1f}x "
                f"({recent_captchas} CAPTCHA)"
            )

    def record_error(self) -> None:
        """Записать ошибку (не CAPTCHA)."""
        self._results.append(False)

    def _apply_multiplier(
        self, delay_range: tuple[float, float]
    ) -> float:
        """Задержка с учётом множителя."""
        base = random.uniform(*delay_range)
        return base * self._multiplier

    def wait_between_pages(self) -> None:
        """Пауза между страницами листинга."""
        self._request_count += 1

        if self._request_count >= self._next_long_pause_at:
            self._long_pause()
            self._next_long_pause_at = (
                self._request_count + random.randint(8, 15)
            )
            return

        delay = self._apply_multiplier(self.base_page_delay)
        logger.debug(
            f" Пауза стр.: {delay:.1f}с "
            f"(×{self._multiplier:.1f})"
        )
        time.sleep(delay)

    def wait_between_details(self) -> None:
        """Пауза между детальными страницами."""
        self._request_count += 1

        if self._request_count >= self._next_long_pause_at:
            self._long_pause()
            self._next_long_pause_at = (
                self._request_count + random.randint(5, 10)
            )
            return

        delay = self._apply_multiplier(self.base_detail_delay)
        logger.debug(
            f" Пауза деталь: {delay:.1f}с "
            f"(×{self._multiplier:.1f})"
        )
        time.sleep(delay)

    def wait_between_actions(self) -> None:
        """Пауза между действиями на странице."""
        delay = random.uniform(*self.action_delay)
        time.sleep(delay)

    def _long_pause(self) -> None:
        """Длинная пауза (передышка)."""
        delay = self._apply_multiplier(self.long_pause_range)
        delay = min(delay, 300)
        logger.info(
            f" Длинная пауза: {delay:.0f}с "
            f"({self._request_count} запросов)"
        )
        time.sleep(delay)

    def wait_on_captcha(self) -> None:
        """Пауза после CAPTCHA."""
        delay = random.uniform(120, 300) * self._multiplier
        delay = min(delay, 600)
        logger.warning(f" Пауза CAPTCHA: {delay:.0f}с")
        time.sleep(delay)

    def wait_between_sections(self) -> None:
        """Пауза между разделами."""
        delay = self._apply_multiplier(self.section_pause_range)
        logger.info(f" Пауза раздел: {delay:.1f}с")
        time.sleep(delay)

    @property
    def total_requests(self) -> int:
        return self._request_count

    @property
    def multiplier(self) -> float:
        return self._multiplier

    @property
    def total_captchas(self) -> int:
        return self._captcha_count