import time
import random
import argparse

from loguru import logger

from forecasting_service.config import DEBUG_DIR
from forecasting_service.utils.logging_setup import setup_logging
from forecasting_service.parsers.common.browser import BrowserManager


DETAIL_URL = "https://vladivostok.cian.ru/sale/flat/327246079/"
DEFAULT_LISTING_URL = (
    "https://cian.ru/cat.php?"
    "engine_version=2&p=1&with_neighbors=0"
    "&region=4701&deal_type=sale"
    "&offer_type=flat&room1=1&only_flat=1"
)

_CAPTCHA_INDICATORS = (
    "captcha", "я не робот", "i'm not a robot",
    "проверка безопасности", "access denied", "заблокирован",
    "подозрительная активность", "security check",
    "чтобы продолжить", "подтвердите", "cloudflare",
)

_CONTENT_INDICATORS = (
    "OfferSummaryInfoGroup", "OfferSummaryInfoItem",
    "О квартире", "О доме", "Общая площадь",
    "Жилая площадь", "Год постройки", "Тип дома",
    "Санузел", "Балкон", "Ремонт", "Отделка",
    "Высота потолков", "Лифт", "Парковка",
)


def _check_captcha_indicators(html: str) -> None:
    html_lower = html.lower()
    logger.info("\n  ПРОВЕРКА ИНДИКАТОРОВ CAPTCHA:")

    for ind in _CAPTCHA_INDICATORS:
        count = html_lower.count(ind)
        if count > 0:
            _log_indicator_occurrences(html, html_lower, ind, count)
        else:
            logger.info(f"    '{ind}': 0")


def _check_content_indicators(html: str) -> None:
    logger.info("\n  КОНТЕНТ СТРАНИЦЫ:")
    for ind in _CONTENT_INDICATORS:
        count = html.count(ind)
        status = "Good" if count > 0 else "Bad"
        logger.info(f"    {status} '{ind}': {count}")


def _log_indicator_occurrences(
    html: str, html_lower: str, ind: str, count: int,
) -> None:
    start_pos = 0
    for found_idx in range(min(count, 3)):
        idx = html_lower.find(ind, start_pos)
        if idx == -1:
            break
        s = max(0, idx - 100)
        e = min(len(html), idx + len(ind) + 100)
        context = html[s:e].replace("\n", " ").replace("\r", "").strip()
        logger.warning(f"    '{ind}' [#{found_idx + 1}]: позиция {idx}")
        logger.warning(f"      ...{context}...")
        start_pos = idx + len(ind)

    if count > 3:
        logger.warning(f"    ...и ещё {count - 3} вхождений")


def main():
    setup_logging(log_prefix="debug", console_level="DEBUG")

    DEBUG_DIR.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser(
        description="Отладка: сохранение и анализ HTML ЦИАН"
    )
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--url", type=str, default=None)
    args = parser.parse_args()

    browser = BrowserManager(headless=False, manual_captcha=True)

    try:
        browser.start()

        if args.detail:
            url = args.url or DETAIL_URL

            logger.info("Warm-up: главная ЦИАН...")
            browser.get_page("https://vladivostok.cian.ru/", scroll=False)
            time.sleep(random.uniform(4, 7))

            logger.info(f"Переход: {url}")
            html = browser.get_page(url, scroll=True)

            filepath = DEBUG_DIR / "cian_detail_page.html"
        else:
            url = args.url or DEFAULT_LISTING_URL
            logger.info(f"Загрузка листинга: {url}")
            html = browser.get_page(url, scroll=True)

            filepath = DEBUG_DIR / "cian_listing_page.html"

        filepath.write_text(html, encoding="utf-8")
        logger.info(f"HTML сохранён: {filepath}")
        logger.info(f"Размер: {len(html)} символов")

        _check_captcha_indicators(html)
        if args.detail:
            _check_content_indicators(html)

        input("\n  Нажми Enter чтобы закрыть браузер...")

    finally:
        browser.stop()


if __name__ == "__main__":
    main()