import json

import re

from typing import Any, Optional

from loguru import logger

_SSR_STATE_PATTERN = re.compile(

    r"window\.__SSR_STATE__\s*=\s*(\{.*?\})\s*;\s*window\.__SSR_CONTEXT__",

    re.S,

)

def extract_ssr_state(html: str) -> dict[str, Any]:

    match = _SSR_STATE_PATTERN.search(html)

    if not match:

        raise ValueError("window.__SSR_STATE__ не найден в HTML")

    raw_json = match.group(1)

    valid_json_data = raw_json.replace("undefined", "null")

    try:

        return json.loads(valid_json_data)

    except json.JSONDecodeError as e:

        logger.error(f"Ошибка парсинга SSR_STATE JSON: {e}")

        raise

def extract_ssr_state_safe(html: str) -> Optional[dict[str, Any]]:

    try:

        return extract_ssr_state(html)

    except Exception as e:

        logger.debug(f"Не удалось извлечь SSR_STATE: {e}")

        return None

def deep_get(data: dict[str, Any], path: list[str], default: Any = None) -> Any:

    current: Any = data

    for key in path:

        if not isinstance(current, dict):

            return default

        current = current.get(key)

        if current is None:

            return default

    return current

def extract_detail_coordinates(state: dict[str, Any]) -> dict[str, Optional[float]]:

    position = deep_get(

        state,

        ["productCard", "originalProduct", "address", "position"],

        default=None,

    )

    if not isinstance(position, dict):

        position = deep_get(

            state,

            ["productCard", "address", "position"],

            default=None,

        )

    if not isinstance(position, dict):

        return {"latitude": None, "longitude": None}

    lat = position.get("lat")

    lon = position.get("lon")

    return {

        "latitude": _to_float(lat),

        "longitude": _to_float(lon),

    }

def _to_float(value: Any) -> Optional[float]:

    try:

        if value is None:

            return None

        return float(value)

    except (TypeError, ValueError):

        return None

def extract_listing_coordinates(entity: dict[str, Any]) -> dict[str, Optional[float]]:

    location = entity.get("location")

    if not isinstance(location, dict):

        return {"latitude": None, "longitude": None}

    return {

        "latitude": _to_float(location.get("lat")),

        "longitude": _to_float(location.get("lon")),

    }
