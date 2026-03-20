import re
import json
from typing import Optional

from bs4 import BeautifulSoup, Tag
from loguru import logger

from forecasting_service.parsers.cian.models import CianFlat

from forecasting_service.parsers.cian.detail_parser import (


    parse_detail_page,
)


def parse_listing_page(html: str) -> list[CianFlat]:
    """
    Парсит страницу листинга ЦИАН.
    Извлекает все карточки объявлений.
    """
    soup = BeautifulSoup(html, "lxml")

    # ищем карточки
    cards = soup.select('[data-name="CardComponent"]')

    if not cards:
        logger.warning("Карточки CardComponent не найдены")
        return []

    flats = []
    for card in cards:
        try:
            flat = _parse_card(card)
            if flat and flat.url:
                flats.append(flat)
        except Exception as e:
            logger.debug(f"Ошибка парсинга карточки: {e}")

    return flats


def is_empty_listing(html: str) -> bool:
    html_lower = html[:10000].lower()
    empty_indicators = [
        "по вашему запросу ничего не найдено",
        "нет объявлений",
        "объявления не найдены",
        "попробуйте изменить параметры",
        "ничего не нашлось",
    ]
    return any(ind in html_lower for ind in empty_indicators)


def _parse_card(card: Tag) -> Optional[CianFlat]:
    url = _extract_url(card)
    cian_id = _extract_cian_id(url)

    title = _extract_title(card)
    rooms, total_meters, floor, floors_count = _parse_title(title)

    price = _extract_price(card)

    geo_data = _extract_geo_labels(card)

    residential_complex = _extract_jk(card)

    underground = _extract_underground(card)

    return CianFlat(
        url=url,
        cian_id=cian_id,


        price=price,
        total_meters=total_meters,
        rooms_count=rooms,
        floor=floor,
        floors_count=floors_count,
        district=geo_data.get("district", ""),
        microdistrict=geo_data.get("microdistrict", ""),
        street=geo_data.get("street", ""),
        house_number=geo_data.get("house", ""),
        underground=underground,
        residential_complex=residential_complex,
        title_raw=title,
        address_raw=geo_data.get("full_address", ""),
    )


def _extract_url(card: Tag) -> str:
    link = (
        card.select_one(
            '[data-name="LinkArea"] a[href*="/flat/"]'
        )
        or card.select_one('a[href*="/flat/"]')
        or card.select_one('a[href*="cian.ru"]')
    )

    if not link:
        return ""

    href = link.get("href", "")

    clean_url = re.sub(r'\?mlSearchSessionGuid=[^&]*', '', href)

    return clean_url


def _extract_cian_id(url: str) -> Optional[int]:
    match = re.search(r'/flat/(\d+)', url)
    if match:
        return int(match.group(1))
    return None


def _extract_title(card: Tag) -> str:
    title_el = card.select_one('[data-mark="OfferTitle"]')
    if title_el:
        return title_el.get_text(strip=True)
    return ""


def _extract_price(card: Tag) -> Optional[int]:
    price_el = card.select_one('[data-mark="MainPrice"]')
    if not price_el:
        return None

    price_text = price_el.get_text(strip=True)
    digits = re.sub(r'[^\d]', '', price_text)
    return int(digits) if digits else None
    
def _is_region_name(text: str) -> bool:
    """Определяет, является ли текст названием региона (а не города)."""


    lower = text.lower()
    region_markers = [
        "край", "область", "республика",
        "округ", "автономн",
    ]
    return any(marker in lower for marker in region_markers)

def _extract_geo_labels(card: Tag) -> dict:
    """
    Извлекает адрес из цепочки GeoLabel.

    Реальная структура href:
      region=4604  → Приморский край
      region=4701  → Владивосток
      district%5B0%5D=971  → р-н Первомайский
      district%5B0%5D=1634 → мкр. Чуркин
      street%5B0%5D=80823  → Харьковская улица
      house%5B0%5D=10896094 → 1к1
    """
    geo_links = card.select('[data-name="GeoLabel"]')

    result = {
        "region": "",
        "city": "",
        "district": "",
        "microdistrict": "",
        "street": "",
        "house": "",
        "full_address": "",
    }

    if not geo_links:
        return result

    labels = [link.get_text(strip=True) for link in geo_links]
    result["full_address"] = ", ".join(labels)

    # Парсим по href — классифицируем каждый элемент
    region_items = []
    district_items = []
    street_item = ""
    house_item = ""

    for link in geo_links:
        text = link.get_text(strip=True)
        href = link.get("href", "")

        if "house%5B" in href or "house[" in href:
            house_item = text
        elif "street%5B" in href or "street[" in href:
            street_item = text
        elif "district%5B" in href or "district[" in href:
            district_items.append(text)
        elif "region=" in href:
            region_items.append(text)

    # region_items обычно: ["Приморский край", "Владивосток"]
    if len(region_items) >= 2:
        result["region"] = region_items[0]
        result["city"] = region_items[1]


    elif len(region_items) == 1:
        # Определяем: край или город
        text = region_items[0]
        if _is_region_name(text):
            result["region"] = text
        else:
            result["city"] = text

    # district_items: ["р-н Первомайский", "мкр. Чуркин"]
    if len(district_items) >= 2:
        result["district"] = district_items[0]
        result["microdistrict"] = district_items[1]
    elif len(district_items) == 1:
        result["district"] = district_items[0]

    result["street"] = street_item
    result["house"] = house_item

    # Fallback: если href-парсинг не дал результата
    if not result["district"] and len(labels) >= 3:
        _parse_geo_by_position(labels, result)

    return result

def _is_street_name(text_lower: str) -> bool:
    """Проверяет, содержит ли текст название улицы."""
    street_markers = [
        "улица", "проспект", "бульвар",
        "переулок", "шоссе", "набережная",
        "проезд", "аллея", "тупик",
        "площадь", "дорога",
    ]
    return any(marker in text_lower for marker in street_markers)

def _parse_geo_by_position(
    labels: list[str], result: dict
) -> None:
    """
    Fallback: парсинг адреса по позиции + содержимому.

    Типичные паттерны:
    [край, город, район, улица, дом]
    [край, город, район, микрорайон, улица, дом]
    """
    for i, label in enumerate(labels):
        lower = label.lower()

        # Регион (первый элемент, содержит "край"/"область")
        if i == 0 and _is_region_name(label):
            if not result["region"]:
                result["region"] = label
            continue

        # Город (второй элемент, после региона)
        if i == 1 and not result["city"] and result["region"]:
            result["city"] = label
            continue

        # Район
        if "р-н " in lower or "район" in lower:


            if not result["district"]:
                result["district"] = label
            continue

        # Микрорайон
        if "мкр." in lower or "микрорайон" in lower:
            if not result["microdistrict"]:
                result["microdistrict"] = label
            continue

        # Улица
        if _is_street_name(lower):
            if not result["street"]:
                result["street"] = label
            continue

        # Дом (последний элемент, если похож на номер)
        if (
            i == len(labels) - 1
            and not result["house"]
            and _looks_like_house_number(label)
        ):
            result["house"] = label


def _looks_like_house_number(text: str) -> bool:
    """Проверяет, похоже ли на номер дома."""
    # "1к1", "15", "23А", "5/2", "10 к2" и т.д.
    return bool(
        re.match(
            r'^[\d]+[а-яА-Яa-zA-Z/к\s]*\d*$',
            text.strip()
        )
    )


def _extract_jk(card: Tag) -> str:
    """Извлекает название ЖК."""
    jk_link = card.select_one('a[class*="jk"]')
    if jk_link:
        text = jk_link.get_text(strip=True)
        text = re.sub(r'^ЖК\s*[«""]?\s*', '', text)
        text = re.sub(r'[»""]$', '', text)
        return text.strip()
    return ""


def _extract_underground(card: Tag) -> str:
    """Извлекает название станции метро."""
    underground_el = card.select_one(
        '[data-name*="nderground"], [class*="underground"]'
    )
    if underground_el:
        text = underground_el.get_text(strip=True)
        text = re.sub(r'\d+\s*мин.*$', '', text).strip()
        return text

    return ""


def _parse_title(title: str) -> tuple[
    Optional[int],
    Optional[float],
    Optional[int],
    Optional[int],
]:
    """
    Парсит заголовок объявления.

    Примеры:
      "1-комн. квартира, 32 м², 7/24 этаж" → (1, 32.0, 7, 24)
      "Студия, 25,5 м², 3/9 этаж" → (0, 25.5, 3, 9)
      "Гостинка с шикарным видом" → (None, None, None, None)
      "2-комн. кв., 54,3 м², 5/9 этаж" → (2, 54.3, 5, 9)

    Returns:
        (rooms_count, total_meters, floor, floors_count)
    """
    rooms = None
    total_meters = None
    floor = None
    floors_count = None

    rooms_match = re.search(r'(\d+)-комн', title)
    if rooms_match:
        rooms = int(rooms_match.group(1))
    elif 'студия' in title.lower():
        rooms = 0

    meters_match = re.search(r'([\d]+[,.]?\d*)\s*м²', title)
    if meters_match:
        meters_str = meters_match.group(1).replace(',', '.')
        total_meters = float(meters_str)

    floor_match = re.search(r'(\d+)\s*/\s*(\d+)\s*эт', title)
    if floor_match:
        floor = int(floor_match.group(1))
        floors_count = int(floor_match.group(2))

    return rooms, total_meters, floor, floors_count