from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from forecasting_service.data.storage import FlatStorage


DATASETS_DIR = Path(__file__).resolve().parent.parent / "datasets"


class DataCollector:
    """
    Высокоуровневый оркестратор сбора данных.



  
    Объединяет:
    - Фаза 1: сбор листинга (CianListingParser)
    - Фаза 2: сбор деталей (detail_runner)
    - Экспорт данных
    - Отчёты о покрытии
    """

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
        """
        Фаза 1: Сбор листинга → SQLite.
        """
        from forecasting_service.parsers.cian.parser import (
            CianListingParser,
        )

        logger.info("═" * 60)
        logger.info(" ФАЗА 1: СБОР ЛИСТИНГА")
        logger.info(f"   Город:    {self.location}")
        logger.info(f"   Стр.:     {start_page}–{end_page}")
        logger.info(f"   Комнаты:  {rooms}")
        logger.info("═" * 60)

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

        self._print_stats()

    def collect_details(
        self,
        batch_size: int = 30,
        detail_delay: tuple[float, float] = (20.0, 40.0),
        restart_every: int = 7,
        headless: bool = False,
        reset_blocked: bool = False,
    ) -> None:


  
        """
        Фаза 2: Сбор деталей из SQLite.
        Resume-safe: можно вызывать многократно.
        """
        import time
        import random

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

        if reset_blocked:
            self.storage.reset_blocked()

        stats = self.storage.get_stats()

        logger.info("═" * 60)
        logger.info(" ФАЗА 2: СБОР ДЕТАЛЕЙ")
        logger.info(f"   Pending:  {stats['pending']}")
        logger.info(f"   Done:     {stats['done']}")
        logger.info(f"   Failed:   {stats['failed']}")
        logger.info(f"   Blocked:  {stats['blocked']}")
        logger.info(f"   Батч:     {batch_size}")
        logger.info(
            f"   Задержка: {detail_delay[0]}–{detail_delay[1]}с"
        )
        logger.info("═" * 60)

        if stats["pending"] == 0 and stats["failed"] == 0:
            logger.info(" Все объявления обработаны!")
            return

        browser = BrowserManager(
            headless=headless,
            manual_captcha=True,
            captcha_wait_timeout=300,
        )

        rate_limiter = AdaptiveRateLimiter(
            base_detail_delay=detail_delay,
        )

        processed = 0
        success = 0

        try:
            browser.start()

            # Warm-up
            self._warmup(browser)

            while processed < batch_size:
                flat = self.storage.get_next_for_detail()


  
                if not flat:
                    logger.info(" Нет объявлений для обработки")
                    break

                flat_id = flat["id"]
                url = flat["url"]
                processed += 1

                logger.info(
                    f"  [{processed}/{batch_size}] "
                    f"id={flat_id} {url[:50]}..."
                )

                # Рестарт браузера периодически
                if (
                    processed > 1
                    and processed % restart_every == 0
                ):
                    logger.info(" Рестарт браузера...")
                    browser.restart_with_new_ua()
                    time.sleep(random.uniform(3, 5))
                    self._mini_warmup(browser)

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
                    logger.info(f"   {filled} полей")

                except CaptchaDetectedError:
                    self.storage.mark_blocked(flat_id)
                    rate_limiter.record_captcha()
                    logger.warning(
                        f"   CAPTCHA "
                        f"(×{rate_limiter.multiplier:.1f})"
                    )

                    if rate_limiter.multiplier >= 4.0:
                        logger.error("Слишком много CAPTCHA")
                        break

                except Exception as e:
                    self.storage.mark_failed(flat_id)
                    rate_limiter.record_error()
                    logger.warning(f"   {e}")

        finally:
            browser.stop()

        self._print_session_report(


  
            processed, success, rate_limiter
        )

    def _warmup(self, browser: "BrowserManager") -> None:
        """Warm-up: имитация захода на сайт."""
        import time
        import random

        from forecasting_service.parsers.common.browser import (
            CaptchaDetectedError,
        )

        logger.info(" Warm-up: заходим на ЦИАН...")
        try:
            browser.get_page(
                "https://vladivostok.cian.ru/",
                scroll=True,
            )
            time.sleep(random.uniform(3, 7))

            browser.get_page(
                "https://vladivostok.cian.ru/cat.php?"
                "deal_type=sale&engine_version=2"
                "&offer_type=flat&region=4701",
                scroll=True,
            )
            time.sleep(random.uniform(5, 10))

            logger.info(" Warm-up завершён")
        except CaptchaDetectedError:
            logger.warning("CAPTCHA на warm-up, продолжаем...")
        except Exception as e:
            logger.warning(f"Ошибка warm-up: {e}")

    def _mini_warmup(self, browser: "BrowserManager") -> None:
        """Мини warm-up после рестарта браузера."""
        import time
        import random

        from forecasting_service.parsers.common.browser import (
            CaptchaDetectedError,
        )

        try:
            browser.get_page(
                "https://vladivostok.cian.ru/",
                scroll=False,
            )
            time.sleep(random.uniform(3, 7))
        except (CaptchaDetectedError, Exception):
            pass

    def export_csv(
        self,
        filename: Optional[str] = None,
        only_done: bool = False,
    ) -> Path:
        """Экспорт данных в CSV."""
        DATASETS_DIR.mkdir(parents=True, exist_ok=True)



  
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = "_done" if only_done else "_all"
            filename = (
                f"vladivostok{suffix}_{timestamp}.csv"
            )

        filepath = DATASETS_DIR / filename

        if only_done:
            self.storage.export_done_to_csv(str(filepath))
        else:
            self.storage.export_to_csv(str(filepath))

        return filepath

    def print_coverage(self) -> None:
        """Печатает отчёт о покрытии полей."""
        stats = self.storage.get_stats()
        coverage = self.storage.get_coverage()
        total = stats["total"]

        print("\n" + "═" * 60)
        print(" ОТЧЁТ О ПОКРЫТИИ ДАТАСЕТА")
        print("═" * 60)

        print(f"\n Всего: {total}")
        print(f"    Done:    {stats['done']}")
        print(f"    Pending: {stats['pending']}")
        print(f"    Failed:  {stats['failed']}")
        print(f"    Blocked: {stats['blocked']}")

        if not coverage:
            print("\n Нет данных")
            return

        done_pct = stats["done"] / total * 100 if total else 0
        print(f"\n Детали собраны: {done_pct:.1f}%")

        print(f"\n{'Поле':<25} {'Покрытие':>10}")
        print("─" * 50)

        for field, pct in sorted(
            coverage.items(), key=lambda x: -x[1]
        ):
            filled = int(pct / 100 * total)
            bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
            print(
                f"   {field:<22} {bar} "
                f"{filled:>4}/{total} {pct:>5.1f}%"
            )

        # Критичные поля для ML
        critical = [
            "price", "total_meters", "rooms_count",
            "district", "floor", "floors_count",
            "year_of_construction", "house_material_type",
            "finish_type",
        ]



  
        print(f"\n Критичные поля для ML:")
        for field in critical:
            pct = coverage.get(field, 0)
            icon = "" if pct >= 75 else "" if pct >= 50 else ""
            print(f"   {icon} {field:<25} {pct:.1f}%")

    def _print_stats(self) -> None:
        """Печатает статистику БД."""
        stats = self.storage.get_stats()
        logger.info(f"\n{'═' * 50}")
        logger.info(f" СОСТОЯНИЕ БД:")
        logger.info(f"   Всего:   {stats['total']}")
        logger.info(f"   Pending: {stats['pending']}")
        logger.info(f"   Done:    {stats['done']}")
        logger.info(f"   Failed:  {stats['failed']}")
        logger.info(f"   Blocked: {stats['blocked']}")
        logger.info(f"{'═' * 50}")

    def _print_session_report(
        self,
        processed: int,
        success: int,
        rate_limiter,
    ) -> None:
        """Печатает отчёт по сессии Фазы 2."""
        stats = self.storage.get_stats()

        logger.info(f"\n{'═' * 60}")
        logger.info(" РЕЗУЛЬТАТ СЕССИИ")
        logger.info(f"   Обработано: {processed}")
        logger.info(f"   Успешно:    {success}")
        logger.info(f"   CAPTCHA:    {rate_limiter.total_captchas}")
        logger.info(f"   Множитель:  ×{rate_limiter.multiplier:.1f}")
        logger.info(f"\n СОСТОЯНИЕ БД")
        logger.info(f"   Всего:   {stats['total']}")
        logger.info(f"   Done:    {stats['done']}")
        logger.info(f"   Pending: {stats['pending']}")
        logger.info(f"   Failed:  {stats['failed']}")
        logger.info(f"   Blocked: {stats['blocked']}")

        coverage = self.storage.get_coverage()
        if coverage:
            logger.info(f"\n ПОКРЫТИЕ ПОЛЕЙ")
            for field, pct in sorted(
                coverage.items(), key=lambda x: -x[1]
            ):
                bar = (
                    "█" * int(pct / 5)
                    + "░" * (20 - int(pct / 5))
                )
                logger.info(
                    f"   {field:<25} {bar} {pct}%"
                )

        logger.info(f"{'═' * 60}")

    def close(self) -> None:
        """Закрывает соединение с БД."""
        self.storage.close()