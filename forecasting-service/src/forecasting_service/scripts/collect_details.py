"""
Фаза 2: Сбор деталей объявлений из SQLite.
Resume-safe: можно запускать многократно.

python -m forecasting_service.scripts.collect_details
python -m forecasting_service.scripts.collect_details --batch 5
python -m forecasting_service.scripts.collect_details --batch 5 --reset-blocked
"""

import argparse
import sys
import time
import random

from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format=(
        "<green>{time:HH:mm:ss}</green> | "
        "<level>{level:<8}</level> | {message}"
    ),
    level="INFO",


)
logger.add(
    "logs/details_{time:YYYY-MM-DD}.log",
    level="DEBUG",
    rotation="10 MB",
)


def main():
    parser = argparse.ArgumentParser(
        description="Фаза 2: Сбор деталей объявлений"
    )
    parser.add_argument(
        "--db", default="flats.db",
    )
    parser.add_argument(
        "--batch", type=int, default=5,
        help="Макс. объявлений за сессию",
    )
    parser.add_argument(
        "--min-delay", type=float, default=10.0,
    )
    parser.add_argument(
        "--max-delay", type=float, default=15.0,
    )
    parser.add_argument(
        "--restart-every", type=int, default=5,
        help="Рестарт браузера каждые N объявлений",
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Headless режим (НЕ рекомендуется для деталей)",
    )
    parser.add_argument(
        "--reset-blocked", action="store_true",
        help="Сбросить blocked → pending перед запуском",
    )
    parser.add_argument(
        "--max-captcha", type=int, default=10,
        help="Макс. CAPTCHA до остановки (по умолчанию: 10)",
    )

    args = parser.parse_args()

    from forecasting_service.data.storage import FlatStorage
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

    storage = FlatStorage(db_name=args.db)

    if args.reset_blocked:
        storage.reset_blocked()



    stats = storage.get_stats()
    logger.info("═" * 60)
    logger.info(" ФАЗА 2: СБОР ДЕТАЛЕЙ")
    logger.info(f"   Всего:    {stats['total']}")
    logger.info(f"   Pending:  {stats['pending']}")
    logger.info(f"   Done:     {stats['done']}")
    logger.info(f"   Failed:   {stats['failed']}")
    logger.info(f"   Blocked:  {stats['blocked']}")
    logger.info(f"   Батч:     {args.batch}")
    logger.info(f"   Задержка: {args.min_delay}–{args.max_delay}с")
    logger.info(f"   Headless: {args.headless}")
    logger.info("═" * 60)

    if args.headless:
        logger.warning(
            " Headless режим! CAPTCHA нельзя пройти вручную. "
            "Рекомендуется запуск БЕЗ --headless"
        )

    if stats["pending"] == 0 and stats["failed"] == 0:
        logger.info(" Все объявления обработаны!")
        return

    browser = BrowserManager(
        headless=args.headless,
        manual_captcha=not args.headless,  # Ручная CAPTCHA только если есть GUI
        captcha_wait_timeout=300,
    )

    rate_limiter = AdaptiveRateLimiter(
        base_detail_delay=(args.min_delay, args.max_delay),
    )

    processed = 0
    success = 0
    captcha_count = 0

    try:
        browser.start()

        # === Warm-up ===
        logger.info(" Warm-up: заходим на ЦИАН...")
        try:
            browser.get_page(
                "https://vladivostok.cian.ru/",
                scroll=True,
            )
            time.sleep(random.uniform(3, 7))

            # Листаем листинг (как обычный пользователь)
            browser.get_page(
                "https://vladivostok.cian.ru/cat.php?"
                "deal_type=sale&engine_version=2"
                "&offer_type=flat&region=4701&room1=1",
                scroll=True,
            )
            time.sleep(random.uniform(5, 10))
            logger.info(" Warm-up завершён")
        except CaptchaDetectedError:


            logger.warning(
                "CAPTCHA на warm-up — "
                "если GUI открыт, она уже пройдена"
            )
        except Exception as e:
            logger.warning(f"Warm-up ошибка: {e}")

        # === Основной цикл ===
        while processed < args.batch:
            flat = storage.get_next_for_detail()
            if not flat:
                logger.info(" Нет объявлений для обработки")
                break

            flat_id = flat["id"]
            url = flat["url"]
            processed += 1

            logger.info(
                f"  [{processed}/{args.batch}] "
                f"id={flat_id} {url[:60]}..."
            )

            # Рестарт браузера периодически
            if (
                processed > 1
                and processed % args.restart_every == 0
            ):
                logger.info(" Рестарт браузера...")
                browser.restart_with_new_ua()
                time.sleep(random.uniform(10, 20))

                # Мини warm-up
                try:
                    browser.get_page(
                        "https://vladivostok.cian.ru/",
                        scroll=False,
                    )
                    time.sleep(random.uniform(3, 7))
                except (CaptchaDetectedError, Exception):
                    pass

            # Пауза перед запросом
            rate_limiter.wait_between_details()

            try:
                html = browser.get_page(url, scroll=True)

                # Парсим детали
                details = parse_detail_page(html)

                # Сохраняем
                storage.update_detail(flat_id, details)
                rate_limiter.record_success()
                success += 1

                filled = sum(
                    1 for v in details.values()
                    if v is not None and v != ""
                )


                logger.info(f"   Извлечено {filled} полей")

                # Логируем что нашли
                if details:
                    found = [
                        f"{k}={v}"
                        for k, v in details.items()
                        if v is not None and v != ""
                    ]
                    if found:
                        logger.debug(
                            f"   {', '.join(found[:5])}..."
                        )

            except CaptchaDetectedError:
                # Если manual_captcha=True и не headless,
                # CAPTCHA уже была показана пользователю.
                # Если мы здесь — значит пользователь НЕ прошёл
                # или мы в headless.
                storage.mark_blocked(flat_id)
                rate_limiter.record_captcha()
                captcha_count += 1

                logger.warning(
                    f"   CAPTCHA #{captcha_count} "
                    f"(×{rate_limiter.multiplier:.1f})"
                )

                if captcha_count >= args.max_captcha:
                    logger.error(
                        f" Достигнут лимит CAPTCHA "
                        f"({args.max_captcha})"
                    )
                    break

            except Exception as e:
                storage.mark_failed(flat_id)
                rate_limiter.record_error()
                logger.warning(f"   Ошибка: {e}")

    except KeyboardInterrupt:
        logger.warning(" Прервано пользователем (Ctrl+C)")
    finally:
        browser.stop()

    # === Итоговый отчёт ===
    stats = storage.get_stats()
    logger.info(f"\n{'═' * 60}")
    logger.info(" РЕЗУЛЬТАТ СЕССИИ")
    logger.info(f"   Обработано: {processed}")
    logger.info(f"   Успешно:    {success}")
    logger.info(f"   CAPTCHA:    {captcha_count}")
    logger.info(f"   Множитель:  ×{rate_limiter.multiplier:.1f}")
    logger.info(f"\n СОСТОЯНИЕ БД")
    logger.info(f"   Всего:   {stats['total']}")
    logger.info(f"   Done:    {stats['done']}")
    logger.info(f"   Pending: {stats['pending']}")
    logger.info(f"   Failed:  {stats['failed']}")
    logger.info(f"   Blocked: {stats['blocked']}")



    coverage = storage.get_coverage()
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

    if captcha_count > 0 and not args.headless:
        logger.info(
            "\n Совет: если CAPTCHA появилась — "
            "пройдите её в окне браузера. "
            "Скрипт подождёт 5 минут."
        )

    storage.close()


if __name__ == "__main__":
    main()