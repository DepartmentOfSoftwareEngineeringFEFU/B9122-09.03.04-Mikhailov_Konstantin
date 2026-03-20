import sys
import time
import random
import argparse
from pathlib import Path

from loguru import logger

logger.remove()
logger.add(sys.stderr, level="DEBUG")

DEBUG_DIR = Path(__file__).resolve().parent.parent / "debug"
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

DETAIL_URL = (
    "https://vladivostok.cian.ru/sale/flat/327246079/"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--detail", action="store_true")
    parser.add_argument("--url", type=str, default=None)
    args = parser.parse_args()

    # Используем обычный Selenium (он у нас работает!)
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=ru-RU")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=options)

    try:


        if args.detail:
            url = args.url or DETAIL_URL

            # Warm-up
            logger.info("Warm-up: главная ЦИАН...")
            driver.get("https://vladivostok.cian.ru/")
            time.sleep(random.uniform(4, 7))

            # Переход на объявление
            logger.info(f"Переход: {url}")
            driver.get(url)
            time.sleep(10)

            html = driver.page_source

            # Сохраняем HTML
            filepath = DEBUG_DIR / "cian_detail_page.html"
            filepath.write_text(html, encoding="utf-8")
            logger.info(f"HTML сохранён: {filepath}")
            logger.info(f"Размер: {len(html)} символов")

            # Проверяем ВСЕ наши индикаторы CAPTCHA
            indicators = [
                "captcha",
                "я не робот",
                "i'm not a robot",
                "проверка безопасности",
                "access denied",
                "заблокирован",
                "подозрительная активность",
                "security check",
                "чтобы продолжить",
                "подтвердите",
                "cloudflare",
            ]

            html_lower = html.lower()

            logger.info("\n ПРОВЕРКА ИНДИКАТОРОВ CAPTCHA:")
            for ind in indicators:
                count = html_lower.count(ind)
                if count > 0:
                    # Находим ВСЕ контексты
                    start_pos = 0
                    found = 0
                    while found < min(count, 3):
                        idx = html_lower.find(ind, start_pos)
                        if idx == -1:
                            break
                        s = max(0, idx - 100)
                        e = min(len(html), idx + len(ind) + 100)
                        context = html[s:e].replace("\n", " ").replace("\r", "").strip()
                        logger.warning(
                            f"   '{ind}' [#{found+1}]: "
                            f"позиция {idx}"
                        )
                        logger.warning(
                            f"     ...{context}..."
                        )
                        start_pos = idx + len(ind)
                        found += 1
                    if count > 3:
                        logger.warning(
                            f"     ...и ещё {count - 3} вхождений"
                        )
                else:
                    logger.info(f"   '{ind}': 0")

            # Проверяем контент страницы
            content_indicators = [
                "OfferSummaryInfoGroup",
                "OfferSummaryInfoItem",
                "О квартире",
                "О доме",
                "Общая площадь",
                "Жилая площадь",
                "Год постройки",
                "Тип дома",
                "Санузел",
                "Балкон",
                "Ремонт",
                "Отделка",
                "Высота потолков",
                "Лифт",
                "Парковка",
            ]

            logger.info("\n КОНТЕНТ СТРАНИЦЫ:")
            for ind in content_indicators:
                count = html.count(ind)
                status = "" if count > 0 else ""
                logger.info(f"  {status} '{ind}': {count}")

        else:
            url = args.url or (
                "https://cian.ru/cat.php?"
                "engine_version=2&p=1&with_neighbors=0"
                "&region=4701&deal_type=sale"
                "&offer_type=flat&room1=1&only_flat=1"
            )
            logger.info(f"Загрузка листинга: {url}")
            driver.get(url)
            time.sleep(10)

            html = driver.page_source
            filepath = DEBUG_DIR / "cian_listing_page.html"
            filepath.write_text(html, encoding="utf-8")
            logger.info(f"HTML сохранён: {filepath}")

        input("\n  Нажми Enter чтобы закрыть браузер...")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
