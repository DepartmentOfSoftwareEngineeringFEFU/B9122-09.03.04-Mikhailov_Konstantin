import random
from typing import Optional

from loguru import logger
from forecasting_service.parsers.common.browser import (
    BrowserManager,
    CaptchaDetectedError,
)
from forecasting_service.parsers.common.rate_limiter import (
    AdaptiveRateLimiter,
)
from forecasting_service.parsers.cian.constants import (
    BASE_LISTING_URL,
    REGIONS,
    ROOM_PARAMS,
    LISTING_CARD_SELECTOR,
)
from forecasting_service.parsers.cian.page_parser import (
    parse_listing_page,
    is_empty_listing,
)
from forecasting_service.parsers.cian.models import CianFlat
from forecasting_service.data.storage import FlatStorage
from forecasting_service.utils.formatting import format_stats_block


class CianListingParser:

    def __init__(
        self,
        location: str = "Владивосток",
        headless: bool = False,
        page_delay: tuple[float, float] = (1.0, 3.0),
        max_retries: int = 5,
        storage: Optional[FlatStorage] = None,
    ):
        if location not in REGIONS:
            raise ValueError(
                f"Неизвестный город: {location}. "
                f"Доступные: {list(REGIONS.keys())}"
            )

        self.location = location
        self.region_id = REGIONS[location]
        self.max_retries = max_retries

        self.browser = BrowserManager(
            headless=headless,
            manual_captcha=True,
            captcha_wait_timeout=300,
        )
        self.rate_limiter = AdaptiveRateLimiter(
            base_page_delay=page_delay,
        )
        self.storage = storage or FlatStorage()

    def _build_listing_url(self, rooms: int | str, page: int = 1) -> str:
        room_param = ROOM_PARAMS.get(rooms, "")
        params = [
            "engine_version=2",
            f"p={page}",
            "with_neighbors=0",
            f"region={self.region_id}",
            "deal_type=sale",
            "offer_type=flat",
            room_param,
            "only_flat=1",
        ]
        return f"{BASE_LISTING_URL}?{'&'.join(p for p in params if p)}"

    def collect_page(self, rooms: int | str, page: int) -> list[CianFlat]:
        url = self._build_listing_url(rooms=rooms, page=page)

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"  Стр. {page} | rooms={rooms} | "
                    f"попытка {attempt}/{self.max_retries}"
                )

                html = self.browser.get_page(
                    url,
                    wait_selector=LISTING_CARD_SELECTOR,
                    wait_timeout=15,
                    scroll=True,
                )

                if is_empty_listing(html):
                    logger.info(f"  Стр. {page} пуста")
                    return []

                flats = parse_listing_page(html)

                if not flats:
                    logger.warning(f"  Стр. {page}: 0 объявлений")
                    if attempt < self.max_retries:
                        self.rate_limiter.wait_between_pages()
                        continue
                    return []

                self.rate_limiter.record_success()
                logger.info(f"  Стр. {page}: {len(flats)} объявлений")
                return flats

            except CaptchaDetectedError:
                self.rate_limiter.record_captcha()
                if attempt < self.max_retries:
                    self.rate_limiter.wait_on_captcha()
                    self.browser.restart_with_new_ua()
                else:
                    raise

            except Exception as e:
                logger.error(f"  Стр. {page}: {e}")
                self.rate_limiter.record_error()
                if attempt < self.max_retries:
                    self.rate_limiter.wait_between_pages()

        return []

    def collect(
        self,
        rooms: int | str | tuple = (1, 2, 3),
        start_page: int = 1,
        end_page: int = 54,
    ) -> None:
        if isinstance(rooms, (int, str)):
            rooms = (rooms,)

        try:
            self.browser.start()

            for room_idx, room_type in enumerate(rooms):
                logger.info(f"\n{'═' * 50}")
                logger.info(f"  Комнатность: {room_type}")
                logger.info(f"{'═' * 50}")

                consecutive_empty = 0

                for page in range(start_page, end_page + 1):
                    if page > start_page or room_idx > 0:
                        self.rate_limiter.wait_between_pages()

                    page_flats = self.collect_page(
                        rooms=room_type, page=page
                    )

                    if not page_flats:
                        consecutive_empty += 1
                        if consecutive_empty >= 2:
                            logger.info(
                                "  2 пустые подряд → следующая комнатность"
                            )
                            break
                    else:
                        consecutive_empty = 0
                        flat_dicts = [f.model_dump() for f in page_flats]
                        new, updated = self.storage.bulk_upsert_from_listing(
                            flat_dicts
                        )
                        logger.info(
                            f"  БД: +{new} новых, ~{updated} обновлений"
                        )

                    stats = self.storage.get_stats()
                    logger.info(
                        f"  В БД: {stats['total']} "
                        f"(pending: {stats['pending']})"
                    )

                if room_type != rooms[-1]:
                    self.rate_limiter.wait_between_sections()

        except CaptchaDetectedError:
            logger.error("  Остановлено (CAPTCHA). Данные сохранены.")

        finally:
            self.browser.stop()

        logger.info(format_stats_block(
            self.storage.get_stats(), title="ИТОГО В БД"
        ))