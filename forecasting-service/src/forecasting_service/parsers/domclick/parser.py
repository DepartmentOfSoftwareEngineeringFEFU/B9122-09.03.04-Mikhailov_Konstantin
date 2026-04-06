"""
основной оркестратор парсинга DomClick.

использование:
  python -m forecasting_service.scripts.collect_listings \
      --source domclick \
      --dc-cookie "v2.0.1774767..." \
      --rooms studio 1 2 3 4 5
"""

import time
import random
from typing import Optional

from loguru import logger

from forecasting_service.parsers.domclick.constants import (
    SEARCH_URL,
    VLADIVOSTOK_AID,
    ROOM_PARAMS,
    CARDS_PER_PAGE,
)
from forecasting_service.parsers.domclick.http_client import (
    DomclickClient,
    QratorBlockedError,
)
from forecasting_service.parsers.domclick.page_parser import (
    parse_listing_page,
    is_empty_listing,
    get_total_count,
)
from forecasting_service.parsers.domclick.detail_parser import (
    parse_detail_page,
)
from forecasting_service.data.storage import FlatStorage
from forecasting_service.utils.formatting import format_stats_block


class DomclickListingParser:
    def __init__(
        self,
        qrator_cookie: str,
        location_id: str = VLADIVOSTOK_AID,
        storage: Optional[FlatStorage] = None,
        page_delay: tuple[float, float] = (2.0, 5.0),
        detail_delay: tuple[float, float] = (1.5, 4.0),
    ):
        self.client = DomclickClient(qrator_cookie)
        self.location_id = location_id
        self.storage = storage or FlatStorage()
        self._page_delay = page_delay
        self._detail_delay = detail_delay

    def _build_search_url(
        self, rooms: int | str, offset: int = 0
    ) -> str:
        room_param = ROOM_PARAMS.get(rooms, str(rooms))

        url = (
            f"{SEARCH_URL}?"
            f"deal_type=sale&category=living"
            f"&offer_type=flat&offer_type=layout"
            f"&aids={self.location_id}"
            f"&rooms={room_param}"
            f"&offset={offset}"
        )
        return url

    def collect(
        self,
        rooms: tuple = ("studio", 1, 2, 3),
        start_page: int = 1,
        end_page: int = 100,
    ) -> None:
        if isinstance(rooms, (int, str)):
            rooms = (rooms,)

        if not self.client.test_connection():
            logger.error(
                "Cookie невалидна! "
                "Получите новую из браузера."
            )
            return

        logger.info("✓ Cookie валидна, начинаем сбор")

        for room_type in rooms:
            logger.info(f"\n{'═' * 50}")
            logger.info(f"  ДомКлик: комнатность {room_type}")
            logger.info(f"{'═' * 50}")

            self._collect_room_type(
                room_type, start_page, end_page
            )

        stats = self.storage.get_stats()
        logger.info(
            format_stats_block(stats, title="ИТОГО В БД (DomClick)")
        )

    def _collect_room_type(
        self,
        room_type: int | str,
        start_page: int,
        end_page: int,
    ) -> None:
        consecutive_empty = 0
        total_offers = None

        for page in range(start_page, end_page + 1):
            offset = (page - 1) * CARDS_PER_PAGE

            if total_offers and offset >= total_offers:
                logger.info(
                    f"  Достигнут конец: offset={offset} >= {total_offers}"
                )
                break

            if page > start_page:
                delay = random.uniform(*self._page_delay)
                time.sleep(delay)

            url = self._build_search_url(room_type, offset)

            try:
                html = self.client.get_page(url)

                if total_offers is None:
                    total_offers = get_total_count(html)
                    if total_offers:
                        max_pages = (total_offers // CARDS_PER_PAGE) + 1
                        logger.info(
                            f"  Всего: {total_offers} объявлений "
                            f"(~{max_pages} стр.)"
                        )

                if is_empty_listing(html):
                    logger.info(f"  Стр. {page}: пустая выдача")
                    break

                flats = parse_listing_page(html)

                if not flats:
                    consecutive_empty += 1
                    logger.info(
                        f"  Стр. {page} (offset={offset}): "
                        f"0 карточек (empty={consecutive_empty})"
                    )
                    if consecutive_empty >= 2:
                        logger.info(
                            "  2 пустые подряд → "
                            "следующая комнатность"
                        )
                        break
                    continue

                consecutive_empty = 0

                new, updated = (
                    self.storage.bulk_upsert_from_listing(flats)
                )
                logger.info(
                    f"  Стр. {page} (offset={offset}): "
                    f"{len(flats)} карточек → "
                    f"+{new} новых, ~{updated} обновл."
                )

            except QratorBlockedError:
                logger.error(
                    "  Qrator заблокировал! "
                    "Cookie протухла, нужна новая."
                )
                return

            except Exception as e:
                logger.error(f"  Стр. {page}: ошибка {e}")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    logger.error("  3 ошибки подряд, стоп")
                    break


    def collect_details(
        self,
        batch_size: int = 100,
        source_filter: str = "domclick",
    ) -> None:
        logger.info(f"\n{'═' * 50}")
        logger.info(f"  ДомКлик: сбор деталей (batch={batch_size})")
        logger.info(f"{'═' * 50}")

        processed = 0
        success = 0

        while processed < batch_size:
            flat = self.storage.get_next_for_detail()
            if not flat:
                logger.info("  Нет объявлений для обработки")
                break

            flat_id = flat["id"]
            url = flat["url"]

            if source_filter and "domclick" not in url:
                continue

            processed += 1
            logger.info(
                f"  [{processed}/{batch_size}] id={flat_id}"
            )

            if processed > 1:
                time.sleep(random.uniform(*self._detail_delay))

            try:
                html = self.client.get_page(url)
                details = parse_detail_page(html)

                self.storage.update_detail(flat_id, details)
                success += 1

                filled = sum(
                    1 for v in details.values()
                    if v is not None and v != ""
                )
                logger.info(f"    ✓ {filled} полей")

            except QratorBlockedError:
                self.storage.mark_blocked(flat_id)
                logger.error("  Qrator заблокировал! Стоп.")
                break

            except Exception as e:
                self.storage.mark_failed(flat_id)
                logger.warning(f"    ✗ Ошибка: {e}")

        logger.info(
            f"\n  Итого: обработано={processed}, "
            f"успешно={success}"
        )


    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "DomclickListingParser":
        return self

    def __exit__(self, *args) -> None:
        self.close()