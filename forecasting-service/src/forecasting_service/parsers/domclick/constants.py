BASE_URL = "https://vladivostok.domclick.ru"
SEARCH_URL = f"{BASE_URL}/search"
CARD_URL_PREFIX = f"{BASE_URL}/card"

VLADIVOSTOK_AID = "57471"

ROOM_PARAMS = {
    "studio": "st",
    0: "st",
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5%2B",
    6: "5%2B",
}

CARDS_PER_PAGE = 20

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) "
        "Gecko/20100101 Firefox/147.0"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Connection": "keep-alive",
}