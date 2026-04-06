import re
from typing import Optional

from bs4 import BeautifulSoup, Tag
from loguru import logger

from forecasting_service.parsers.domclick.constants import BASE_URL


def parse_listing_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")

    cards = soup.select('div[data-e2e-id="offers-list__item"]')

    if not cards:
        logger.debug("DomClick: карточки не найдены")
        return []

    flats = []
    seen_urls = set()

    for card in cards:
        try:
            flat = _parse_card(card)
            if flat and flat["url"] and flat["url"] not in seen_urls:
                seen_urls.add(flat["url"])
                flats.append(flat)
        except Exception as e:
            logger.debug(f"Ошибка парсинга карточки DC: {e}")

    return flats


def is_empty_listing(html: str) -> bool:
    html_lower = html[:10000].lower()
    indicators = [
        "ничего не найдено",
        "нет объявлений",
        "попробуйте изменить",
        "ничего не нашлось",
    ]
    return any(ind in html_lower for ind in indicators)


def get_total_count(html: str) -> Optional[int]:
    match = re.search(
        r'(\d[\d\s]*\d)\s*(?:объявлени|предложени|квартир)',
        html[:20000],
    )
    if match:
        digits = re.sub(r'\s', '', match.group(1))
        return int(digits) if digits else None
    return None

def _parse_card(card: Tag) -> Optional[dict]:
    link_el = card.select_one(
        'a[data-test="product-snippet-property-offer"]'
    )
    if not link_el:
        return None

    href = link_el.get("href", "")
    url = f"{BASE_URL}{href}" if href.startswith("/") else href

    source_id = _extract_source_id(url)

    rooms, total_meters, floor, floors_count = _parse_title_spans(
        link_el
    )

    price = _extract_price(card)

    address = _extract_address(card)

    return {
        "source": "domclick",
        "source_id": source_id,
        "url": url,
        "price": price,
        "total_meters": total_meters,
        "rooms_count": rooms,
        "floor": floor,
        "floors_count": floors_count,
        "address_raw": address,
    }


def _extract_source_id(url: str) -> Optional[str]:
    match = re.search(r'flat__(\d+)', url)
    return match.group(1) if match else None


def _parse_title_spans(
    link_el: Tag,
) -> tuple[Optional[int], Optional[float], Optional[int], Optional[int]]:
    rooms = None
    total_meters = None
    floor = None
    floors_count = None

    spans = link_el.select("span.s6KKu.siaB6")

    if len(spans) < 3:
        spans = link_el.select("span")

    if len(spans) < 3:
        return rooms, total_meters, floor, floors_count

    title_text = spans[0].get_text(strip=True)
    if "студия" in title_text.lower():
        rooms = 0
    else:
        r_match = re.search(r'(\d+)-комн', title_text)
        if r_match:
            rooms = int(r_match.group(1))

    meters_text = spans[1].get_text(strip=True)
    m_match = re.search(r'([\d,.]+)', meters_text)
    if m_match:
        total_meters = float(m_match.group(1).replace(',', '.'))

    floor_text = spans[2].get_text(strip=True)
    f_match = re.search(r'(\d+)\s*/\s*(\d+)', floor_text)
    if f_match:
        floor = int(f_match.group(1))
        floors_count = int(f_match.group(2))

    return rooms, total_meters, floor, floors_count


def _extract_price(card: Tag) -> Optional[int]:
    price_el = card.select_one(
        'div[data-e2e-id="product-snippet-price-sale"] p'
    )

    if not price_el:
        price_el = card.select_one('[data-e2e-id*="price"] p')

    if not price_el:
        return None

    digits = re.sub(r'[^\d]', '', price_el.get_text(strip=True))
    return int(digits) if digits else None


def _extract_address(card: Tag) -> str:
    addr_el = card.select_one(
        'span[data-e2e-id="product-snippet-address"]'
    )

    if not addr_el:
        addr_el = card.select_one(
            'span[data-e2-id="product-snippet-address"]'
        )

    if not addr_el:
        addr_el = card.select_one('[class*="address"]')

    return addr_el.get_text(strip=True) if addr_el else ""