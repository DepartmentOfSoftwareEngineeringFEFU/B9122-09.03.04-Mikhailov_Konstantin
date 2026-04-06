import re
from typing import Optional

from bs4 import BeautifulSoup, Tag

_FLAT_MAPPING = {
    "тип жилья": ("object_type", "_str"),
    "общая площадь": ("total_meters", "_parse_area"),
    "жилая площадь": ("living_meters", "_parse_area"),
    "площадь кухни": ("kitchen_meters", "_parse_area"),
    "высота потолков": ("ceiling_height", "_parse_area"),
    "санузел": ("_bathroom_raw", "_str"),
    "вид из окон": ("window_view", "_str"),
    "вид из окна": ("window_view", "_str"),
    "отделка": ("finish_type", "_str"),
    "ремонт": ("finish_type", "_str"),
    "балкон/лоджия": ("_balcony_raw", "_str"),
    "балкон": ("_balcony_raw", "_str"),
    "планировка": ("layout_type", "_str"),
    "мебель": ("has_furniture", "_parse_furniture"),
}

_BUILDING_MAPPING = {
    "год постройки": ("year_of_construction", "_parse_year"),
    "количество лифтов": ("_elevator_raw", "_str"),
    "лифт": ("_elevator_raw", "_str"),
    "тип дома": ("house_material_type", "_str"),
    "тип перекрытий": ("floor_type", "_str"),
    "подъезды": ("entrances_count", "_parse_int"),
    "о подъезде": ("_entrance_info_raw", "_str"),
    "о\xa0подъезде": ("_entrance_info_raw", "_str"),
    "парковка": ("parking_type", "_str"),
    "отопление": ("heating_type", "_str"),
    "аварийность": ("is_emergency", "_parse_emergency"),
}

_PARSERS: dict[str, callable] = {}


def parse_detail_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    details = {}

    _parse_about_flat(soup, details)
    _parse_about_building(soup, details)
    _parse_about_jk(soup, details)
    _parse_rosreestr(soup, details)

    return details



def _parse_about_flat(soup: BeautifulSoup, details: dict) -> None:
    group = _find_info_group(soup, "квартир")
    if not group:
        return

    items = _extract_info_items(group)
    _apply_mapping(items, _FLAT_MAPPING, details)

    if "_bathroom_raw" in details:
        _parse_bathroom(details.pop("_bathroom_raw"), details)
    if "_balcony_raw" in details:
        _parse_balcony(details.pop("_balcony_raw"), details)


def _parse_about_building(soup: BeautifulSoup, details: dict) -> None:
    group = _find_info_group(soup, "доме")
    if not group:
        return

    items = _extract_info_items(group)
    _apply_mapping(items, _BUILDING_MAPPING, details)

    if "_elevator_raw" in details:
        _parse_elevators(details.pop("_elevator_raw"), details)
    if "_entrance_info_raw" in details:
        _parse_entrance_info(details.pop("_entrance_info_raw"), details)


def _parse_about_jk(soup: BeautifulSoup, details: dict) -> None:
    jk_section = None
    for h2 in soup.select("h2"):
        text = h2.get_text(strip=True)
        if text.startswith("О ЖК") or text.startswith("О\xa0ЖК"):
            jk_section = h2.find_parent("div", class_=re.compile("inner"))
            break

    if not jk_section:
        return

    for h2 in jk_section.select("h2"):
        text = h2.get_text(strip=True)
        jk_match = re.search(r'[«""](.+?)[»""]', text)
        if jk_match:
            details["jk_name"] = jk_match.group(1)

    for li in jk_section.select("li"):
        spans = li.select("span")
        if len(spans) >= 2:
            name = spans[0].get_text(strip=True).lower()
            value = spans[-1].get_text(strip=True)

            if "сдача" in name:
                details["jk_deadline"] = value
            elif "класс" in name:
                details["jk_class"] = value
            elif "тип дома" in name:
                details.setdefault("house_material_type", value)
            elif "парковка" in name:
                details.setdefault("parking_type", value)
            elif "отделка" in name:
                details.setdefault("finish_type", value)

        link = li.select_one('a[data-mark="Link"]')
        if link:
            label = li.select_one("span")
            if label and "застройщик" in label.get_text(strip=True).lower():
                details["developer"] = link.get_text(strip=True)


def _parse_rosreestr(soup: BeautifulSoup, details: dict) -> None:
    rosreestr = soup.select_one('[data-name="RosreestrSection"]')
    if not rosreestr:
        return

    items = rosreestr.select('[data-name="NameValueListItem"]')

    for item in items:
        name_el = item.select_one("dt")
        value_el = item.select_one("dd")
        if not name_el or not value_el:
            continue

        name = name_el.get_text(strip=True).lower()
        value = value_el.get_text(strip=True)

        if "обременен" in name:
            details["encumbrances"] = value
        elif "собственник" in name:
            details["owners_count"] = _parse_int(value)
        elif "кадастровый" in name:
            details["cadastral_number"] = value



def _find_info_group(soup: BeautifulSoup, keyword: str) -> Optional[Tag]:
    groups = soup.select('[data-name="OfferSummaryInfoGroup"]')
    for group in groups:
        header = group.select_one("h2")
        if header and keyword in header.get_text(strip=True).lower():
            return group
    return None


def _extract_info_items(container: Tag) -> list[tuple[str, str]]:
    items = []
    info_divs = container.select('[data-name="OfferSummaryInfoItem"]')

    for div in info_divs:
        paragraphs = div.select("p")
        if len(paragraphs) >= 2:
            name = paragraphs[0].get_text(strip=True)
            value = paragraphs[1].get_text(strip=True)
            items.append((name, value))

    return items


def _apply_mapping(
    items: list[tuple[str, str]],
    mapping: dict[str, tuple[str, str]],
    details: dict,
) -> None:
    for name, value in items:
        name_lower = name.lower()
        for key, (field, parser_name) in mapping.items():
            if key in name_lower:
                parser_func = _PARSERS[parser_name]
                details[field] = parser_func(value)
                break



def _str(value: str) -> str:
    return value.strip()


def _parse_area(value: str) -> Optional[float]:
    match = re.search(r'([\d]+[,.]?\d*)', value)
    if match:
        return float(match.group(1).replace(",", "."))
    return None


def _parse_year(value: str) -> Optional[int]:
    match = re.search(r'((?:19|20)\d{2})', value)
    if match:
        return int(match.group(1))
    return None


def _parse_int(value: str) -> Optional[int]:
    match = re.search(r'(\d+)', value)
    if match:
        return int(match.group(1))
    return None


def _parse_emergency(value: str) -> Optional[bool]:
    lower = value.lower()
    if "нет" in lower:
        return False
    if "да" in lower or "есть" in lower:
        return True
    return None


def _parse_furniture(value: str) -> Optional[bool]:
    lower = value.lower()
    if "с мебелью" in lower or "есть" in lower:
        return True
    if "без мебели" in lower or "нет" in lower:
        return False
    return None



def _parse_bathroom(raw: str, details: dict) -> None:
    lower = raw.lower()
    details["bathroom_count"] = _parse_int(raw) or 1

    if "раздельн" in lower:
        details["bathroom_type"] = "раздельный"
    elif "совмещ" in lower:
        details["bathroom_type"] = "совмещённый"
    else:
        details["bathroom_type"] = raw


def _parse_balcony(raw: str, details: dict) -> None:
    lower = raw.lower()

    balcony_match = re.search(r'(\d+)\s*балкон', lower)
    if balcony_match:
        details["balcony_count"] = int(balcony_match.group(1))
    elif "балкон" in lower:
        details["balcony_count"] = 1

    loggia_match = re.search(r'(\d+)\s*лоджи', lower)
    if loggia_match:
        details["loggia_count"] = int(loggia_match.group(1))
    elif "лоджи" in lower:
        details["loggia_count"] = 1


def _parse_elevators(raw: str, details: dict) -> None:
    lower = raw.lower()

    pass_match = re.search(r'(\d+)\s*пассажирск', lower)
    if pass_match:
        details["elevator_passenger"] = int(pass_match.group(1))

    cargo_match = re.search(r'(\d+)\s*грузов', lower)
    if cargo_match:
        details["elevator_cargo"] = int(cargo_match.group(1))

    if not pass_match and not cargo_match and "есть" in lower:
        details["elevator_passenger"] = 1


def _parse_entrance_info(raw: str, details: dict) -> None:
    lower = raw.lower()
    if "мусоропровод" in lower:
        details["has_garbage_chute"] = True
    if "консьерж" in lower:
        details["has_concierge"] = True
    if "пандус" in lower:
        details["has_ramp"] = True



_PARSERS = {
    "_str": _str,
    "_parse_area": _parse_area,
    "_parse_year": _parse_year,
    "_parse_int": _parse_int,
    "_parse_emergency": _parse_emergency,
    "_parse_furniture": _parse_furniture,
}