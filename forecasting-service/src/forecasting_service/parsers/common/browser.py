import time
import random
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException
from loguru import logger

try:
    from selenium_stealth import stealth

    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
]

_BLOCK_INDICATORS = (
    "я не робот",
    "i'm not a robot",
    "проверка безопасности",
    "access denied",
    "заблокирован",
    "подозрительная активность",
    "security check",
    "доступ ограничен",
    "доступ запрещён",
    "доступ запрещен",
    "blocked",
    "forbidden",
)

_MIN_PAGE_SIZE = 5000


class CaptchaDetectedError(Exception):


    def __init__(self, url: str):
        self.url = url
        super().__init__(f"CAPTCHA detected: {url}")


# ── Менеджер браузера ─────────────────────────────────

class BrowserManager:

    def __init__(
        self,
        headless: bool = True,
        window_size: tuple[int, int] = (1920, 1080),
        page_load_timeout: int = 60,
        implicit_wait: int = 10,
        rotate_ua_every: int = 10,
        manual_captcha: bool = True,
        captcha_wait_timeout: int = 300,
        user_data_dir: Optional[str] = None,
    ):
        self.headless = headless
        self.window_size = window_size
        self.page_load_timeout = page_load_timeout
        self.implicit_wait = implicit_wait
        self.rotate_ua_every = rotate_ua_every
        self.manual_captcha = manual_captcha
        self.captcha_wait_timeout = captcha_wait_timeout
        self.user_data_dir = user_data_dir

        self._driver = None
        self._current_ua: str = random.choice(USER_AGENTS)
        self._page_count = 0

    def start(self):
        if self._driver:
            logger.debug("Браузер уже запущен")
            return self._driver

        logger.info(f"  Запуск Chrome (headless={self.headless})")
        self._driver = self._create_driver()

        try:
            self._driver.set_page_load_timeout(self.page_load_timeout)
            self._driver.implicitly_wait(self.implicit_wait)
        except Exception as e:
            self.stop()
            raise e

        logger.info("  Chrome запущен")
        return self._driver

    def stop(self) -> None:
        if self._driver:
            try:
                self._driver.quit()
                logger.info("Chrome остановлен")
            except Exception as e:
                logger.warning(f"Ошибка при остановке: {e}")
            finally:
                self._driver = None

    def restart_with_new_ua(self) -> None:
        old_ua = self._current_ua
        available = [ua for ua in USER_AGENTS if ua != old_ua]
        self._current_ua = random.choice(available)

        logger.info(f"  Ротация UA: ...{self._current_ua[-30:]}")
        self.stop()
        time.sleep(random.uniform(2, 5))
        self.start()

    @property
    def driver(self):
        if not self._driver:
            return self.start()
        return self._driver

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    def __del__(self):
        try:
            self.stop()
        except Exception:
            pass

    def get_page(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        wait_timeout: int = 15,
        scroll: bool = True,
    ) -> str:
        self._page_count += 1
        if (
            self._page_count > 1
            and self._page_count % self.rotate_ua_every == 0
        ):
            self.restart_with_new_ua()

        driver = self.driver
        logger.debug(f"  Загрузка: {url[:80]}...")
        try:
            driver.get(url)
        except TimeoutException:
            logger.warning("  Таймаут загрузки, пробуем продолжить...")

        if wait_selector:
            self._wait_for_selector(driver, wait_selector, wait_timeout)

        if scroll:
            self._simulate_reading(driver)
            if random.random() < 0.3:
                self._simulate_mouse_movement(driver)

        time.sleep(random.uniform(1.0, 2.5))

        html = driver.page_source
        if self._is_captcha(html):
            logger.warning("  CAPTCHA обнаружена!")

            if self.manual_captcha and not self.headless:
                html = self._wait_for_manual_captcha(driver, url)
            else:
                raise CaptchaDetectedError(url)

        return html

    @staticmethod
    def _is_captcha(html: str) -> bool:
        html_lower = html[:15000].lower()

        has_block = any(ind in html_lower for ind in _BLOCK_INDICATORS)
        if has_block:
            return True
        if len(html) < _MIN_PAGE_SIZE and "cian" in html_lower:
            logger.debug(
                f"Подозрительно маленький HTML: {len(html)} символов"
            )
            return True

        return False

    def _wait_for_manual_captcha(self, driver, url: str) -> str:
        logger.warning("═" * 60)
        logger.warning("  CAPTCHA! Пройдите её в окне браузера")
        logger.warning(f"  URL: {url[:60]}...")
        logger.warning(f"  Ожидание: {self.captcha_wait_timeout} сек")
        logger.warning("═" * 60)

        start_time = time.time()
        check_interval = 5

        while time.time() - start_time < self.captcha_wait_timeout:
            time.sleep(check_interval)
            try:
                html = driver.page_source
                if not self._is_captcha(html):
                    logger.info("  CAPTCHA пройдена! Продолжаем...")
                    time.sleep(random.uniform(3, 6))
                    return html
            except Exception:
                pass

            elapsed = int(time.time() - start_time)
            remaining = self.captcha_wait_timeout - elapsed
            if elapsed % 15 < check_interval:
                logger.info(f"  Жду... ({remaining} сек осталось)")

        logger.error(
            f"  CAPTCHA не пройдена за {self.captcha_wait_timeout} сек"
        )
        raise CaptchaDetectedError(url)

    def _create_driver(self):
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        w, h = self.window_size
        options.add_argument(f"--window-size={w},{h}")
        options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-gpu")
        options.add_argument("--lang=ru-RU")
        options.add_argument(f"user-agent={self._current_ua}")

        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)
        self._apply_stealth(driver)

        return driver

    @staticmethod
    def _apply_stealth(driver) -> None:
        if HAS_STEALTH:
            stealth(
                driver,
                languages=["ru-RU", "ru", "en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
            )
        else:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {
                    "source": """
                        Object.defineProperty(
                            navigator, 'webdriver',
                            { get: () => undefined }
                        );
                        Object.defineProperty(
                            navigator, 'plugins',
                            { get: () => [1, 2, 3, 4, 5] }
                        );
                        Object.defineProperty(
                            navigator, 'languages',
                            { get: () => ['ru-RU', 'ru', 'en-US', 'en'] }
                        );
                        window.chrome = { runtime: {} };
                    """
                },
            )


    @staticmethod
    def _wait_for_selector(
        driver, selector: str, timeout: int
    ) -> None:
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, selector)
                )
            )
        except TimeoutException:
            logger.warning(f"  Элемент '{selector}' не найден")

    @staticmethod
    def _simulate_reading(driver) -> None:
        try:
            viewport_h = driver.execute_script(
                "return window.innerHeight"
            )
            page_h = driver.execute_script(
                "return document.body.scrollHeight"
            )

            if page_h <= viewport_h:
                time.sleep(random.uniform(1.0, 2.0))
                return

            num_scrolls = random.randint(2, 4)
            step = page_h / (num_scrolls + 1)
            pos = 0

            for _ in range(num_scrolls):
                amount = step * random.uniform(0.7, 1.3)
                pos = min(pos + amount, page_h)

                driver.execute_script(
                    f"window.scrollTo({{top: {int(pos)}, "
                    f"behavior: 'smooth'}});"
                )
                time.sleep(random.uniform(1.0, 3.0))

                if random.random() < 0.3:
                    back = pos * random.uniform(0.2, 0.5)
                    driver.execute_script(
                        f"window.scrollTo({{top: {int(back)}, "
                        f"behavior: 'smooth'}});"
                    )
                    time.sleep(random.uniform(0.5, 1.5))

            driver.execute_script(
                "window.scrollTo({top: 0, behavior: 'smooth'});"
            )
            time.sleep(random.uniform(0.5, 1.0))

        except Exception as e:
            logger.debug(f"Ошибка скролла: {e}")

    @staticmethod
    def _simulate_mouse_movement(driver) -> None:
        try:
            actions = ActionChains(driver)
            body = driver.find_element(By.TAG_NAME, "body")

            for _ in range(random.randint(2, 3)):
                x = random.randint(-200, 200)
                y = random.randint(-100, 100)
                try:
                    actions.move_to_element_with_offset(
                        body, x, y
                    ).perform()
                except Exception:
                    pass
                time.sleep(random.uniform(0.3, 0.8))

        except Exception as e:
            logger.debug(f"Ошибка мыши: {e}")