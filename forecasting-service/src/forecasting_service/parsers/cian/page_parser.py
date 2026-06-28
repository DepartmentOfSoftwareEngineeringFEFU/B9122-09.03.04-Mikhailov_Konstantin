import re

from typing import Optional

from bs4 import BeautifulSoup, Tag

from loguru import logger

from forecasting_service.parsers.cian.models import CianFlat

_REGION_MARKERS = ("край", "область", "республика", "округ", "автономн")

_STREET_MARKERS = (

    "улица", "проспект", "бульвар", "переулок", "шоссе",

    "набережная", "проезд", "аллея", "тупик", "площадь", "дорога",

)

def parse_listing_page(html: str) -> list[CianFlat]:

    soup = BeautifulSoup(html, "lxml")

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

    geo = _extract_geo_labels(card)

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

        district=geo.get("district", ""),

        microdistrict=geo.get("microdistrict", ""),

        street=geo.get("street", ""),

        house_number=geo.get("house", ""),

        underground=underground,

        residential_complex=residential_complex,

        title_raw=title,

        address_raw=geo.get("full_address", ""),

    )

def _extract_url(card: Tag) -> str:

    link = (

        card.select_one('[data-name="LinkArea"] a[href*="/flat/"]')

        or card.select_one('a[href*="/flat/"]')

        or card.select_one('a[href*="cian.ru"]')

    )

    if not link:

        return ""

    href = link.get("href", "")

    return re.sub(r'\?mlSearchSessionGuid=[^&]*', '', href)

def _extract_cian_id(url: str) -> Optional[int]:

    match = re.search(r'/flat/(\d+)', url)

    return int(match.group(1)) if match else None

def _extract_title(card: Tag) -> str:

    title_el = card.select_one('[data-mark="OfferTitle"]')

    return title_el.get_text(strip=True) if title_el else ""

def _extract_price(card: Tag) -> Optional[int]:

    price_el = card.select_one('[data-mark="MainPrice"]')

    if not price_el:

        return None

    digits = re.sub(r'[^\d]', '', price_el.get_text(strip=True))

    return int(digits) if digits else None

def _extract_jk(card: Tag) -> str:

    jk_link = card.select_one('a[class*="jk"]')

    if not jk_link:

        return ""

    text = jk_link.get_text(strip=True)

    text = re.sub(r'^ЖК\s*[«""]?\s*', '', text)

    text = re.sub(r'[»""]$', '', text)

    return text.strip()

def _extract_underground(card: Tag) -> str:

    el = card.select_one(

        '[data-name*="nderground"], [class*="underground"]'

    )

    if not el:

        return ""

    text = el.get_text(strip=True)

    return re.sub(r'\d+\s*мин.*$', '', text).strip()

def _parse_title(

    title: str,

) -> tuple[Optional[int], Optional[float], Optional[int], Optional[int]]:

    rooms = None

    total_meters = None

    floor = None

    floors_count = None

    rooms_match = re.search(r'(\d+)-комн', title)

    if rooms_match:

        rooms = int(rooms_match.group(1))

    elif "студия" in title.lower():

        rooms = 0

    meters_match = re.search(r'([\d]+[,.]?\d*)\s*м²', title)

    if meters_match:

        total_meters = float(meters_match.group(1).replace(',', '.'))

    floor_match = re.search(r'(\d+)\s*/\s*(\d+)\s*эт', title)

    if floor_match:

        floor = int(floor_match.group(1))

        floors_count = int(floor_match.group(2))

    return rooms, total_meters, floor, floors_count

def _extract_geo_labels(card: Tag) -> dict:

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

    if len(region_items) >= 2:

        result["region"] = region_items[0]

        result["city"] = region_items[1]

    elif len(region_items) == 1:

        text = region_items[0]

        if _is_region_name(text):

            result["region"] = text

        else:

            result["city"] = text

    if len(district_items) >= 2:

        result["district"] = district_items[0]

        result["microdistrict"] = district_items[1]

    elif len(district_items) == 1:

        result["district"] = district_items[0]

    result["street"] = street_item

    result["house"] = house_item

    if not result["district"] and len(labels) >= 3:

        _parse_geo_by_position(labels, result)

    return result

def _is_region_name(text: str) -> bool:

    lower = text.lower()

    return any(marker in lower for marker in _REGION_MARKERS)

def _is_street_name(text_lower: str) -> bool:

    return any(marker in text_lower for marker in _STREET_MARKERS)

def _looks_like_house_number(text: str) -> bool:

    return bool(

        re.match(r'^[\d]+[а-яА-Яa-zA-Z/к\s]*\d*$', text.strip())

    )

def _parse_geo_by_position(labels: list[str], result: dict) -> None:

    for i, label in enumerate(labels):

        lower = label.lower()

        if i == 0 and _is_region_name(label):

            if not result["region"]:

                result["region"] = label

            continue

        if i == 1 and not result["city"] and result["region"]:

            result["city"] = label

            continue

        if ("р-н " in lower or "район" in lower) and not result["district"]:

            result["district"] = label

            continue

        if ("мкр." in lower or "микрорайон" in lower) and not result["microdistrict"]:

            result["microdistrict"] = label

            continue

        if _is_street_name(lower) and not result["street"]:

            result["street"] = label

            continue

        if (

            i == len(labels) - 1

            and not result["house"]

            and _looks_like_house_number(label)

        ):

            result["house"] = label
