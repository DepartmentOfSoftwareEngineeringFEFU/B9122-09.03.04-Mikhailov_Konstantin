import re

from typing import Optional

from bs4 import BeautifulSoup

def parse_detail_page(html: str) -> dict:

    soup = BeautifulSoup(html, "lxml")

    details = {}

    _parse_main_items(soup, details)

    _parse_building_items(soup, details)

    _parse_extra_flags(soup, details)

    _parse_novostroyka(soup, details)

    _parse_jk(soup, details)

    _parse_address(soup, details)

    return details

_MAIN_MAPPING = {

    "Комнат":              ("rooms_count", "int"),

    "Площадь":             ("total_meters", "area"),

    "Жилая":               ("living_meters", "area"),

    "Кухня":               ("kitchen_meters", "area"),

    "Этаж":                ("floor", "int"),

    "Ремонт":              ("finish_type", "text"),

    "Тип жилья":           ("object_type", "text"),

    "Вид из окон":         ("window_view", "text"),

    "Количество балконов": ("balcony_count", "int"),

    "Высота потолков":     ("ceiling_height", "float"),

    "Санузел":             ("bathroom_type", "text"),

    "Количество лифтов":   ("elevator_passenger", "int"),

    "Грузовой лифт":       ("elevator_cargo", "bool"),

    "Газ":                 ("has_gas", "bool"),

    "Мусоропровод":        ("has_garbage_chute", "bool"),

    "Перепланировка":      ("has_redevelopment", "bool"),

}

def _parse_main_items(soup: BeautifulSoup, details: dict) -> None:

    items = soup.select("li.C_L_4[data-e2e-id]")

    for item in items:

        key = item.get("data-e2e-id", "").strip()

        if not key:

            continue

        val_el = item.select_one('span[data-e2e-id="Значение"]')

        if not val_el:

            val_el = item.select_one("span.yNtG9")

        if not val_el:

            continue

        val = val_el.get_text(strip=True)

        if key in _MAIN_MAPPING:

            field, parse_type = _MAIN_MAPPING[key]

            parsed = _parse_value(val, parse_type)

            if parsed is not None:

                details.setdefault(field, parsed)

_BUILDING_MAPPING = {

    "Год постройки":       ("year_of_construction", "year"),

    "Материал стен":       ("house_material_type", "text"),

    "Количество этажей":   ("floors_count", "int"),

    "Тип перекрытий":      ("floor_type", "text"),

    "Высота потолков":     ("ceiling_height", "float"),

    "Мусоропровод":        ("has_garbage_chute", "bool"),

    "Газ":                 ("has_gas", "bool"),

    "Лифт":                ("elevator_passenger", "bool_to_int"),

}

def _parse_building_items(soup: BeautifulSoup, details: dict) -> None:

    section = soup.select_one(

        'section[data-e2e-id="building-info-block"]'

    )

    if not section:

        return

    items = section.select("li.ByFq7[data-e2e-id]")

    for item in items:

        key = item.get("data-e2e-id", "").strip()

        if not key:

            continue

        val_el = (

            item.select_one('span[data-e2e-id="Значение"]')

            or item.select_one("span.upbHP")

        )

        if not val_el:

            continue

        val = val_el.get_text(strip=True)

        if key in _BUILDING_MAPPING:

            field, parse_type = _BUILDING_MAPPING[key]

            parsed = _parse_value(val, parse_type)

            if parsed is not None:

                details.setdefault(field, parsed)

_FLAG_MAPPING = {

    "Консьерж":            "has_concierge",

    "Домофон":             "has_intercom",

    "Закрытая территория": "has_closed_territory",

    "Кодовая дверь":       "has_code_door",

    "Во дворе":            "parking_yard",

    "Подземная":           "parking_underground",

    "Охраняемая":          "parking_guarded",

    "Со шлагбаумом":       "parking_barrier",

    "Есть гараж":          "has_garage",

}

def _parse_extra_flags(soup: BeautifulSoup, details: dict) -> None:

    items = soup.select("li.IY5_T[data-e2e-id]")

    for item in items:

        key = item.get("data-e2e-id", "").strip()

        if key in _FLAG_MAPPING:

            details[_FLAG_MAPPING[key]] = True

    parking_parts = []

    for flag, label in [

        ("parking_yard", "во дворе"),

        ("parking_underground", "подземная"),

        ("parking_guarded", "охраняемая"),

        ("parking_barrier", "со шлагбаумом"),

    ]:

        if details.pop(flag, False):

            parking_parts.append(label)

    if parking_parts:

        details.setdefault("parking_type", ", ".join(parking_parts))

    if details.pop("has_intercom", None):

        pass

    if details.pop("has_code_door", None):

        pass

    if details.pop("has_closed_territory", None):

        pass

def _parse_novostroyka(soup: BeautifulSoup, details: dict) -> None:

    section = soup.select_one('div[data-id="aboutOffer"]')

    if not section:

        return

    for item in section.select("div.ri4j3"):

        key_el = item.select_one("div.K_m3c")

        val_el = item.select_one("div.BCmK9")

        if not key_el or not val_el:

            continue

        key = key_el.get_text(strip=True).lower()

        val = val_el.get_text(strip=True)

        if "жилая" in key:

            details.setdefault("living_meters", _parse_float(val))

        elif "кухня" in key:

            details.setdefault("kitchen_meters", _parse_float(val))

        elif "отделка" in key:

            details.setdefault("finish_type", val.lower())

        elif "класс жилья" in key:

            details.setdefault("jk_class", val.lower())

        elif "санузел" in key:

            details.setdefault("bathroom_type", val.lower())

        elif "окна" in key or "вид" in key:

            details.setdefault("window_view", val.lower())

    section2 = soup.select_one('div[data-id="aboutComplex"]')

    if not section2:

        return

    for item in section2.select("div.nJDVt"):

        key_el = item.select_one("div.Qgi72")

        val_el = item.select_one("div.wib4o")

        if not key_el or not val_el:

            continue

        key = key_el.get_text(strip=True).lower()

        val = val_el.get_text(strip=True)

        if "материал" in key:

            details.setdefault("house_material_type", val.lower())

        elif "этажей" in key:

            details.setdefault("floors_count", _parse_int(val))

def _parse_jk(soup: BeautifulSoup, details: dict) -> None:

    jk_el = soup.select_one(

        'div[data-id="aboutComplex"] h2.tebMt span.UD6h3'

    )

    if jk_el:

        name = jk_el.get_text(strip=True)

        name = re.sub(r'^ЖК\s*[«""]?\s*', '', name)

        name = re.sub(r'[»""]$', '', name)

        details["jk_name"] = name.strip()

def _parse_address(soup: BeautifulSoup, details: dict) -> None:

    location = soup.select_one('div[data-e2e-id="location"]')

    if location:

        addr_el = location.select_one('a[data-e2e-id="building_uri"]')

        if addr_el:

            details.setdefault("address_raw", addr_el.get_text(strip=True))

        district_el = location.select_one("div.ANXSp")

        if district_el:

            details.setdefault("district", district_el.get_text(strip=True))

def _parse_value(val: str, parse_type: str):

    if parse_type == "text":

        return val.lower().strip() if val else None

    elif parse_type == "int":

        return _parse_int(val)

    elif parse_type == "float":

        return _parse_float(val)

    elif parse_type == "area":

        return _parse_float(val)

    elif parse_type == "year":

        m = re.search(r'((?:19|20)\d{2})', val)

        return int(m.group(1)) if m else None

    elif parse_type == "bool":

        lower = val.lower()

        if any(w in lower for w in ("есть", "да")):

            return True

        if any(w in lower for w in ("нет",)):

            return False

        return None

    elif parse_type == "bool_to_int":

        lower = val.lower()

        if any(w in lower for w in ("есть", "да")):

            return 1

        return None

    return val

def _parse_int(val: str) -> Optional[int]:

    m = re.search(r'\d+', val)

    return int(m.group()) if m else None

def _parse_float(val: str) -> Optional[float]:

    m = re.search(r'([\d]+[,.]?\d*)', val)

    if m:

        return float(m.group(1).replace(',', '.'))

    return None
