import requests
from loguru import logger


class QratorBlockedError(Exception):
    def __init__(self, url: str):
        self.url = url
        super().__init__(f"Qrator blocked: {url}")


class DomclickClient:
    def __init__(self, qrator_cookie: str):
        from forecasting_service.parsers.domclick.constants import (
            DEFAULT_HEADERS,
        )

        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)

        self._session.cookies.set(
            "qrator_jsid2",
            qrator_cookie,
            domain=".domclick.ru",
        )

    def get_page(self, url: str, timeout: int = 30) -> str:
        logger.debug(f"  GET {url[:80]}...")

        resp = self._session.get(url, timeout=timeout)

        if self._is_qrator_block(resp):
            raise QratorBlockedError(url)

        resp.raise_for_status()
        return resp.text

    def test_connection(self) -> bool:
        from forecasting_service.parsers.domclick.constants import (
            SEARCH_URL,
            VLADIVOSTOK_AID,
        )

        test_url = (
            f"{SEARCH_URL}?deal_type=sale&category=living"
            f"&offer_type=flat&aids={VLADIVOSTOK_AID}"
            f"&rooms=1&offset=0"
        )

        try:
            resp = self._session.get(test_url, timeout=15)

            if self._is_qrator_block(resp):
                return False

            if resp.status_code == 200 and len(resp.text) > 50000:
                return True

            return False

        except Exception as e:
            logger.debug(f"Тест соединения: {e}")
            return False

    @staticmethod
    def _is_qrator_block(resp: requests.Response) -> bool:
        text_lower = resp.text[:5000].lower()

        if len(resp.text) < 10000:
            if "qrator" in text_lower:
                return True
            if "необычно" in text_lower:
                return True

        if resp.status_code == 403:
            return True

        return False

    def close(self) -> None:
        self._session.close()

    def __enter__(self) -> "DomclickClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()