
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from forecasting_service.config import (
    DATASETS_DIR,
    CRITICAL_ML_FIELDS,
    DEFAULT_BATCH_SIZE,
    DEFAULT_DETAIL_DELAY,
    DEFAULT_RESTART_EVERY,
)
from forecasting_service.data.storage import FlatStorage
from forecasting_service.utils.formatting import (
    format_stats_block,
    format_coverage_block,
    format_critical_fields,
    format_session_report,
)


class DataCollector:


    def __init__(
        self,
        location: str = "Владивосток",
        db_name: str = "flats.db",
    ):
        self.location = location
        self.storage = FlatStorage(db_name=db_name)


    def collect_listings(
        self,
        rooms: tuple = ("studio", 1, 2, 3, 4, 5, 6),
        start_page: int = 1,
        end_page: int = 54,
        headless: bool = False,
        page_delay: tuple[float, float] = (5.0, 15.0),
    ) -> None:

        from forecasting_service.parsers.cian.parser import (
            CianListingParser,
        )

        self._log_phase_header(
            phase=1,
            title="СБОР ЛИСТИНГА",
            extra={
                "Город": self.location,
                "Стр.": f"{start_page}–{end_page}",
                "Комнаты": str(rooms),
            },
        )

        parser = CianListingParser(
            location=self.location,
            headless=headless,
            page_delay=page_delay,
            storage=self.storage,
        )

        parser.collect(
            rooms=rooms,
            start_page=start_page,
            end_page=end_page,
        )

        logger.info(format_stats_block(self.storage.get_stats()))


    def collect_details(
        self,
        batch_size: int = DEFAULT_BATCH_SIZE,
        detail_delay: tuple[float, float] = DEFAULT_DETAIL_DELAY,
        restart_every: int = DEFAULT_RESTART_EVERY,
        headless: bool = False,
        reset_blocked: bool = False,
        max_captcha: int = 10,
    ) -> None:

        from forecasting_service.parsers.common.browser import (
            BrowserManager,
            CaptchaDetectedError,
        )
        from forecasting_service.parsers.common.rate_limiter import (
            AdaptiveRateLimiter,
        )
        from forecasting_service.parsers.cian.detail_parser import (
            parse_detail_page,
        )
        from forecasting_service.parsers.common.warmup import (
            perform_warmup,
            perform_mini_warmup,
        )


        if reset_blocked:
            self.storage.reset_blocked()

        self.storage.reset_stale_in_progress()

        stats = self.storage.get_stats()

        self._log_phase_header(
            phase=2,
            title="СБОР ДЕТАЛЕЙ",
            extra={
                "Pending": stats["pending"],
                "Done": stats["done"],
                "Failed": stats["failed"],
                "Blocked": stats["blocked"],
                "Батч": batch_size,
                "Задержка": f"{detail_delay[0]}–{detail_delay[1]}с",
            },
        )

        if stats["pending"] == 0 and stats["failed"] == 0:
            logger.info("  Все объявления обработаны!")
            return

        
        browser = BrowserManager(
            headless=headless,
            manual_captcha=not headless,
            captcha_wait_timeout=300,
        )

        rate_limiter = AdaptiveRateLimiter(
            base_detail_delay=detail_delay,
        )

        processed = 0
        success = 0
        captcha_count = 0

        try:
            browser.start()
            perform_warmup(browser, self.location)

            while processed < batch_size:
                flat = self.storage.get_next_for_detail()
                if not flat:
                    logger.info("  Нет объявлений для обработки")
                    break

                flat_id = flat["id"]
                url = flat["url"]
                processed += 1

                logger.info(
                    f"  [{processed}/{batch_size}] "
                    f"id={flat_id} {url[:50]}..."
                )

                if processed > 1 and processed % restart_every == 0:
                    logger.info("  Рестарт браузера...")
                    browser.restart_with_new_ua()
                    time.sleep(random.uniform(3, 5))
                    perform_mini_warmup(browser, self.location)

                rate_limiter.wait_between_details()

                try:
                    html = browser.get_page(url, scroll=True)
                    details = parse_detail_page(html)

                    self.storage.update_detail(flat_id, details)
                    rate_limiter.record_success()
                    success += 1

                    filled = sum(
                        1 for v in details.values()
                        if v is not None and v != ""
                    )
                    logger.info(f"    {filled} полей")

                except CaptchaDetectedError:
                    self.storage.mark_blocked(flat_id)
                    rate_limiter.record_captcha()
                    captcha_count += 1

                    logger.warning(
                        f"  CAPTCHA #{captcha_count} "
                        f"(×{rate_limiter.multiplier:.1f})"
                    )

                    if captcha_count >= max_captcha:
                        logger.error(
                            f"  Достигнут лимит CAPTCHA ({max_captcha})"
                        )
                        break

                except Exception as e:
                    self.storage.mark_failed(flat_id)
                    rate_limiter.record_error()
                    logger.warning(f"  Ошибка: {e}")

        except KeyboardInterrupt:
            logger.warning("  Прервано пользователем (Ctrl+C)")

        finally:
            browser.stop()

        report = format_session_report(
            processed=processed,
            success=success,
            captcha_count=captcha_count,
            multiplier=rate_limiter.multiplier,
            stats=self.storage.get_stats(),
            coverage=self.storage.get_coverage(),
        )
        logger.info(report)


    def export_csv(
        self,
        filename: Optional[str] = None,
        only_done: bool = False,
    ) -> Path:

        DATASETS_DIR.mkdir(parents=True, exist_ok=True)

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_done" if only_done else "_all"
            filename = f"vladivostok{suffix}_{timestamp}.csv"

        filepath = DATASETS_DIR / filename

        if only_done:
            self.storage.export_done_to_csv(str(filepath))
        else:
            self.storage.export_to_csv(str(filepath))

        return filepath



    def print_coverage(self) -> None:

        stats = self.storage.get_stats()
        coverage = self.storage.get_coverage()
        total = stats["total"]

        print("\n" + "═" * 60)
        print("  ОТЧЁТ О ПОКРЫТИИ ДАТАСЕТА")
        print("═" * 60)

        print(f"\n  Всего: {total}")
        print(f"  Done:    {stats['done']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Failed:  {stats['failed']}")
        print(f"  Blocked: {stats['blocked']}")

        if not coverage:
            print("\n  Нет данных")
            return

        done_pct = stats["done"] / total * 100 if total else 0
        print(f"\n  Детали собраны: {done_pct:.1f}%")

        print(format_coverage_block(coverage, total))
        print(format_critical_fields(coverage, CRITICAL_ML_FIELDS))



    @staticmethod
    def _log_phase_header(
        phase: int,
        title: str,
        extra: dict[str, object],
    ) -> None:
        """Логирует красивый заголовок фазы."""
        logger.info("═" * 60)
        logger.info(f"  ФАЗА {phase}: {title}")
        for key, value in extra.items():
            logger.info(f"  {key:<12} {value}")
        logger.info("═" * 60)


    def close(self) -> None:

        self.storage.close()

    def __enter__(self) -> "DataCollector":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()