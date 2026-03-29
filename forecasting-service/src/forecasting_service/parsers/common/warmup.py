import time
import random
from typing import TYPE_CHECKING

from loguru import logger

from forecasting_service.parsers.cian.constants import REGIONS, SUBDOMAINS

if TYPE_CHECKING:
    from forecasting_service.parsers.common.browser import BrowserManager


def _build_warmup_urls(location: str) -> dict[str, str]:
    region_id = REGIONS.get(location)
    if not region_id:
        raise ValueError(f"Неизвестный город: {location}")

    subdomain = SUBDOMAINS.get(location, "www")

    return {
        "main": f"https://{subdomain}.cian.ru/",
        "listing": (
            f"https://{subdomain}.cian.ru/cat.php?"
            f"deal_type=sale&engine_version=2"
            f"&offer_type=flat&region={region_id}"
        ),
    }


def perform_warmup(
    browser: "BrowserManager",
    location: str = "Владивосток",
    scroll: bool = True,
) -> None:
    from forecasting_service.parsers.common.browser import CaptchaDetectedError

    urls = _build_warmup_urls(location)

    logger.info("  Warm-up: заходим на ЦИАН...")
    try:
        browser.get_page(urls["main"], scroll=scroll)
        time.sleep(random.uniform(3, 7))

        browser.get_page(urls["listing"], scroll=scroll)
        time.sleep(random.uniform(5, 10))

        logger.info("  Warm-up завершён")
    except CaptchaDetectedError:
        logger.warning("CAPTCHA на warm-up, продолжаем...")
    except Exception as e:
        logger.warning(f"Ошибка warm-up: {e}")


def perform_mini_warmup(
    browser: "BrowserManager",
    location: str = "Владивосток",
) -> None:
    from forecasting_service.parsers.common.browser import CaptchaDetectedError

    urls = _build_warmup_urls(location)

    try:
        browser.get_page(urls["main"], scroll=False)
        time.sleep(random.uniform(3, 7))
    except (CaptchaDetectedError, Exception):
        pass