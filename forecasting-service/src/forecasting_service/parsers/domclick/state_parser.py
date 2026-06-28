from __future__ import annotations

import json

from typing import Any, Optional

from forecasting_service.parsers.domclick.ssr_state import deep_get

def _count_house_photo_types(items: list[Any]) -> dict[str, int]:

    counts = {

        "facade": 0,

        "lift": 0,

        "entrance_inside": 0,

        "entrance_outside": 0,

        "territory": 0,

        "other": 0,

    }

    if not isinstance(items, list):

        return counts

    for item in items:

        if not isinstance(item, dict):

            continue

        photo_type = item.get("type")

        if photo_type == "Facade":

            counts["facade"] += 1

        elif photo_type == "Lift":

            counts["lift"] += 1

        elif photo_type == "EntranceInside":

            counts["entrance_inside"] += 1

        elif photo_type == "EntranceOutside":

            counts["entrance_outside"] += 1

        elif photo_type == "Territory":

            counts["territory"] += 1

        else:

            counts["other"] += 1

    return counts

def parse_detail_state(raw_state: dict[str, Any]) -> dict[str, Any]:

    state = raw_state

    product = _get_product_card(state)

    original = product.get("originalProduct", {}) if isinstance(product, dict) else {}

    address_orig = original.get("address", {}) if isinstance(original, dict) else {}

    address_norm = product.get("address", {}) if isinstance(product, dict) else {}

    object_orig = original.get("object_info", {}) if isinstance(original, dict) else {}

    object_norm = product.get("objectInfo", {}) if isinstance(product, dict) else {}

    house_orig = original.get("house", {}) if isinstance(original, dict) else {}

    house_norm = deep_get(product, ["house", "info"], default=None)

    if not isinstance(house_norm, dict):

        raw_house = product.get("house", {})

        house_norm = raw_house if isinstance(raw_house, dict) else {}

    if not isinstance(house_norm, dict):

        house_norm = {}

    house_state = deep_get(state, ["houseInfo", "info"], default={}) or {}

    if not isinstance(house_state, dict):

        house_state = {}

    offer_photos = product.get("photos") or original.get("photos") or []

    if not isinstance(offer_photos, list):

        offer_photos = []

    house_photos = deep_get(state, ["houseInfo", "photos"], default=[]) or []

    if not isinstance(house_photos, list):

        house_photos = []

    has_plan_photo = any(

        isinstance(photo, dict) and photo.get("isPlan") is True

        for photo in offer_photos

    )

    raw_original_photos = original.get("photos", [])

    if not isinstance(raw_original_photos, list):

        raw_original_photos = []

    has_window_photo = any(

        isinstance(photo, dict) and photo.get("class_name") == "FromWindow"

        for photo in raw_original_photos

    )

    house_photo_counts = _count_house_photo_types(house_photos)

    legal_orig = original.get("legal_options", {}) if isinstance(original, dict) else {}

    legal_norm = product.get("legalOptions", {}) if isinstance(product, dict) else {}

    seller_orig = original.get("seller", {}) if isinstance(original, dict) else {}

    seller_norm = product.get("seller", {}) if isinstance(product, dict) else {}

    stats_orig = original.get("offer_stat", {}) if isinstance(original, dict) else {}

    egrn_orig = original.get("egrn_data", {}) if isinstance(original, dict) else {}

    egrn_norm = product.get("egrnData", {}) if isinstance(product, dict) else {}

    flat_complex_orig = original.get("flat_complex", {}) if isinstance(original, dict) else {}

    flat_complex_norm = product.get("flatComplex", {}) if isinstance(product, dict) else {}

    price_orig = original.get("price_info", {}) if isinstance(original, dict) else {}

    price_norm = product.get("priceInfo", {}) if isinstance(product, dict) else {}

    price_prediction = state.get("pricePrediction", {}) if isinstance(state, dict) else {}

    source_id = _first_not_none(

        original.get("id"),

        product.get("id"),

        product.get("_id"),

    )

    lat = _first_not_none(

        deep_get(address_orig, ["position", "lat"]),

        deep_get(address_norm, ["position", "lat"]),

    )

    lon = _first_not_none(

        deep_get(address_orig, ["position", "lon"]),

        deep_get(address_norm, ["position", "lon"]),

    )

    district_name, district_guid, district_slug = _extract_district(address_orig, address_norm)

    street_name, street_guid = _extract_street(address_orig, address_norm)

    house_number = _extract_house_number(address_orig, address_norm)

    province_guid = _extract_parent_guid(address_orig, address_norm, "province")

    locality_guid = _first_not_none(

        deep_get(address_orig, ["locality", "guid"]),

        address_norm.get("localityGuid"),

        _extract_parent_guid(address_orig, address_norm, "locality"),

    )

    parking_keys, parking_labels = _extract_named_items(

        _first_non_empty_list(house_orig.get("parking"), house_norm.get("parkingWithKey"))

    )

    security_keys, security_labels = _extract_named_items(

        _first_non_empty_list(house_orig.get("security"), house_norm.get("securityWithKey"))

    )

    yard_keys, yard_labels = _extract_named_items(

        _first_non_empty_list(house_orig.get("yard"), house_norm.get("yardWithKey"))

    )

    infra_keys, infra_labels = _extract_named_items(

        _first_non_empty_list(house_orig.get("infrastructure"), house_norm.get("infrastructureWithKey"))

    )

    window_view_labels = _extract_window_view_labels(

        _first_not_none(object_orig.get("window_view"), object_norm.get("windowView"))

    )

    seller_agent_orig = seller_orig.get("agent", {}) if isinstance(seller_orig, dict) else {}

    seller_agent_norm = seller_norm.get("agent", {}) if isinstance(seller_norm, dict) else {}

    seller_company_orig = seller_orig.get("company", {}) if isinstance(seller_orig, dict) else {}

    seller_company_norm = seller_norm.get("company", {}) if isinstance(seller_norm, dict) else {}

    is_owner = _first_not_none(

        legal_orig.get("is_owner"),

        legal_norm.get("isOwner"),

        product.get("isOwner"),

    )

    is_agent = _first_not_none(

        seller_agent_orig.get("is_agent"),

        seller_agent_norm.get("isAgent"),

    )

    author_type = _detect_author_type(

        source=original.get("source"),

        is_owner=is_owner,

        is_agent=is_agent,

        company=seller_company_orig or seller_company_norm,

    )

    tariff_orig = original.get("tariff_options", {}) if isinstance(original, dict) else {}

    tariff_norm = product.get("tariffOptions", {}) if isinstance(product, dict) else {}

    parsed = {

        "source": "domclick",

        "source_id": str(source_id) if source_id is not None else None,

        "url": _first_not_none(

            product.get("href"),

            original.get("href"),

        ),

        "price": _to_int(_first_not_none(

            price_orig.get("price"),

            price_norm.get("price"),

        )),

        "price_per_sqm": _to_float(_first_not_none(

            price_orig.get("square_price"),

            price_norm.get("squarePrice"),

        )),

        "total_meters": _to_float(_first_not_none(

            object_orig.get("area"),

            object_norm.get("area"),

        )),

        "living_meters": _to_float(_first_not_none(

            object_orig.get("living_area"),

            object_norm.get("livingArea"),

        )),

        "kitchen_meters": _to_float(_first_not_none(

            object_orig.get("kitchen_area"),

            object_norm.get("kitchenArea"),

        )),

        "rooms_count": _to_int(_first_not_none(

            object_orig.get("rooms"),

            object_norm.get("rooms"),

        )),

        "floor": _to_int(_first_not_none(

            object_orig.get("floor"),

            object_norm.get("floor"),

        )),

        "floors_count": _to_int(_first_not_none(

            house_orig.get("floors"),

            house_norm.get("floors"),

        )),

        "latitude": _to_float(lat),

        "longitude": _to_float(lon),

        "address_raw": _first_not_none(

            address_orig.get("short_display_name"),

            address_norm.get("displayNameShort"),

            address_orig.get("display_name"),

            address_norm.get("displayName"),

        ),

        "address_guid": _first_not_none(

            address_orig.get("guid"),

            address_norm.get("guid"),

        ),

        "district": district_name,

        "district_guid": district_guid,

        "district_slug": district_slug,

        "street": street_name,

        "street_guid": street_guid,

        "house_number": house_number,

        "locality": _first_not_none(

            deep_get(address_orig, ["locality", "name"]),

            address_norm.get("locality"),

        ),

        "locality_guid": locality_guid,

        "province_guid": province_guid,

        "timezone": _first_not_none(

            deep_get(address_orig, ["info", "timezone"]),

            address_norm.get("timezone"),

        ),

        "timezone_offset": _to_int(_first_not_none(

            deep_get(address_orig, ["info", "timezone_offset"]),

            address_norm.get("timezoneOffset"),

        )),

        "is_apartment": _to_bool(_first_not_none(

            object_orig.get("is_apartment"),

            object_norm.get("isApartment"),

        )),

        "finish_type": _extract_display_name_or_value(

            object_orig.get("renovation"),

            object_norm.get("renovation"),

        ),

        "bathroom_type": _extract_display_name_or_value(

            object_orig.get("bathroom"),

            object_norm.get("bathroom"),

        ),

        "bathroom_count": _calc_bathroom_count(

            object_orig,

            object_norm,

        ),

        "balcony_count": _to_int(_first_not_none(

            object_orig.get("balconies"),

            object_norm.get("balconies"),

        )),

        "loggia_count": _to_int(_first_not_none(

            object_orig.get("loggias"),

            object_norm.get("loggias"),

        )),

        "window_view": ", ".join(window_view_labels) if window_view_labels else None,

        "window_view_json": window_view_labels,

        "has_gas": _to_bool(_first_not_none(

            object_orig.get("has_gas"),

            object_norm.get("hasGas"),

        )),

        "has_redevelopment": _to_bool(_first_not_none(

            object_orig.get("redevelopment"),

            object_norm.get("redevelopment"),

        )),

        "year_of_construction": _to_int(_first_not_none(

            house_orig.get("build_year"),

            house_norm.get("buildYear"),

        )),

        "house_material_type": _extract_display_name_or_value(

            house_orig.get("wall_type"),

            house_norm.get("wallType"),

        ),

        "floor_type": _first_not_none(

            house_norm.get("floorType"),

            house_state.get("floorType"),

        ),

        "elevator_passenger": _to_int(_first_not_none(

            house_orig.get("lifts_passenger"),

            house_norm.get("liftsPassenger"),

        )),

        "elevator_cargo": _to_int(_first_not_none(

            house_orig.get("lifts_freight"),

            house_norm.get("liftsFreight"),

        )),

        "has_garbage_chute": _to_bool(_first_not_none(

            house_orig.get("has_garbage_disposer"),

            house_norm.get("hasGarbageDisposer"),

        )),

        "entrances_count": _to_int(_first_not_none(

            house_norm.get("entranceCount"),

            house_state.get("entranceCount"),

        )),

        "quarters_count": _to_int(_first_not_none(

            house_norm.get("quartersCount"),

            house_state.get("quartersCount"),

        )),

        "living_quarters_count": _to_int(_first_not_none(

            house_norm.get("livingQuartersCount"),

            house_state.get("livingQuartersCount"),

        )),

        "heating_type": _first_not_none(

            house_norm.get("heatingType"),

            house_state.get("heatingType"),

        ),

        "hot_water_type": _first_not_none(

            house_norm.get("hotWaterType"),

            house_state.get("hotWaterType"),

        ),

        "cold_water_type": _first_not_none(

            house_norm.get("coldWaterType"),

            house_state.get("coldWaterType"),

        ),

        "foundation_type": _first_not_none(

            house_norm.get("foundationType"),

            house_state.get("foundationType"),

        ),

        "ventilation_type": _first_not_none(

            house_norm.get("ventilationType"),

            house_state.get("ventilationType"),

        ),

        "energy_efficiency": _first_not_none(

            house_norm.get("energyEfficiency"),

            house_state.get("energyEfficiency"),

        ),

        "has_intercom": "intercom" in parking_or_security_keys(security_keys),

        "has_concierge": "concierge" in parking_or_security_keys(security_keys),

        "has_closed_territory": "closed_area" in parking_or_security_keys(security_keys),

        "has_code_door": "code_door" in parking_or_security_keys(security_keys),

        "has_garage": "garage" in parking_or_security_keys(parking_keys),

        "parking_type": ", ".join(parking_labels) if parking_labels else None,

        "parking_keys_json": parking_keys,

        "security_features": ", ".join(security_labels) if security_labels else None,

        "security_keys_json": security_keys,

        "yard_features": ", ".join(yard_labels) if yard_labels else None,

        "yard_keys_json": yard_keys,

        "infrastructure_features": ", ".join(infra_labels) if infra_labels else None,

        "infrastructure_keys_json": infra_keys,

        "jk_id": _to_int(_first_not_none(

            flat_complex_orig.get("id"),

            flat_complex_norm.get("id"),

        )),

        "jk_name": _first_not_none(

            flat_complex_orig.get("name"),

            flat_complex_norm.get("name"),

        ),

        "jk_slug": _first_not_none(

            flat_complex_orig.get("slug"),

            flat_complex_norm.get("slug"),

        ),

        "is_owner": _to_bool(is_owner),

        "author_type": author_type,

        "owner_count": _to_int(_first_not_none(

            legal_orig.get("owner_count"),

            legal_norm.get("ownerCount"),

        )),

        "owner_minors": _to_bool(_first_not_none(

            legal_orig.get("owner_minors"),

            legal_norm.get("ownerMinors"),

        )),

        "residence_minors": _to_bool(_first_not_none(

            legal_orig.get("residence_minors"),

            legal_norm.get("residenceMinors"),

        )),

        "years_ownership": _extract_display_name_or_value(

            legal_orig.get("years_ownership"),

            legal_norm.get("yearsOwnership"),

        ),

        "sale_type": _extract_display_name_or_value(

            legal_orig.get("sale_type"),

            legal_norm.get("saleType"),

        ),

        "seller_name": _first_not_none(

            seller_agent_orig.get("full_name"),

            seller_agent_norm.get("fullName"),

        ),

        "seller_phone_masked": _first_not_none(

            seller_agent_orig.get("phone"),

            seller_agent_norm.get("phone"),

        ),

        "seller_is_agent": _to_bool(is_agent),

        "seller_is_sbol_verified": _to_bool(_first_not_none(

            seller_agent_orig.get("is_sbol_verified"),

            seller_agent_norm.get("isSbolVerified"),

        )),

        "seller_is_esia_verified": _to_bool(_first_not_none(

            seller_agent_orig.get("is_esia_verified"),

            seller_agent_norm.get("isEsiaVerified"),

        )),

        "seller_company_name": _first_not_none(

            seller_company_orig.get("trade_name"),

            seller_company_orig.get("displayName"),

            seller_company_norm.get("tradeName"),

            seller_company_norm.get("displayName"),

        ),

        "seller_company_id": _to_int(_first_not_none(

            seller_company_orig.get("id"),

            seller_company_norm.get("id"),

        )),

        "source_type": original.get("source"),

        "views_count": _to_int(_first_not_none(

            stats_orig.get("views_count"),

            product.get("viewsCount"),

        )),

        "calls_count": _to_int(_first_not_none(

            stats_orig.get("calls_count"),

            product.get("callsCount"),

        )),

        "favorites_count": _to_int(_first_not_none(

            stats_orig.get("favorite_offer_users_count"),

            product.get("favoriteOfferUsersCount"),

        )),

        "online_show": _to_bool(_first_not_none(

            original.get("online_show"),

            product.get("onlineShow"),

        )),

        "chat_available": _to_bool(_first_not_none(

            original.get("chat_available"),

            product.get("chatAvailable"),

        )),

        "is_auction": _to_bool(_first_not_none(

            original.get("is_auction"),

            product.get("isAuction"),

        )),

        "is_exclusive": _to_bool(original.get("is_exclusive")),

        "is_placement_paid": _to_bool(_first_not_none(

            original.get("is_placement_paid"),

            product.get("isPlacementPaid"),

        )),

        "duplicates_offer_count": _to_int(_first_not_none(

            product.get("duplicatesOfferCount"),

            original.get("duplicatesOfferCount"),

        )),

        "published_at_source": _first_not_none(

            original.get("published_dt"),

            product.get("publishedDate"),

        ),

        "updated_at_source": _first_not_none(

            original.get("updated_dt"),

            product.get("updatedDate"),

        ),

        "description": _normalize_text(_first_not_none(

            original.get("description"),

            object_orig.get("description"),

            object_norm.get("description"),

        )),

        "egrn_area_status": _first_not_none(

            deep_get(egrn_orig, ["area", "status"]),

            deep_get(egrn_norm, ["area", "status"]),

        ),

        "egrn_floor_status": _first_not_none(

            deep_get(egrn_orig, ["floor", "status"]),

            deep_get(egrn_norm, ["floor", "status"]),

        ),

        "egrn_owners_status": _first_not_none(

            deep_get(egrn_orig, ["owners_count", "status"]),

            deep_get(egrn_norm, ["owners_count", "status"]),

        ),

        "collateral": _to_bool(_first_not_none(

            egrn_orig.get("collateral"),

            egrn_norm.get("collateral"),

        )),

        "collateral_sber": _to_bool(_first_not_none(

            egrn_orig.get("collateral_sber"),

            egrn_norm.get("collateral_sber"),

        )),

        "market_price_min": _to_int(price_prediction.get("minMarketPrice")),

        "market_price_max": _to_int(price_prediction.get("maxMarketPrice")),

        "market_price": _to_int(price_prediction.get("marketPrice")),

        "rent_long_predicted": _to_int(price_prediction.get("rentLongPricePredicted")),

        "rent_short_predicted": _to_int(price_prediction.get("rentShortPricePredicted")),

        "repair_quality_predicted": _to_int(price_prediction.get("repairQuality")),

        "price_history_json": _first_not_none(

            price_orig.get("price_history"),

            price_norm.get("priceHistory"),

        ),

        "offer_photos_json": product.get("photos") or original.get("photos"),

        "house_photos_json": deep_get(state, ["houseInfo", "photos"], default=[]),

        "address_parents_json": _first_not_none(

            address_orig.get("parents"),

            address_norm.get("parents"),

        ),

        "discounts_json": _first_not_none(

            original.get("discount_status"),

            product.get("discountStatus"),

        ),

        "offer_photos_count": len(offer_photos),

        "house_photos_count": len(house_photos),

        "has_plan_photo": has_plan_photo,

        "has_window_photo": has_window_photo,

        "house_photo_facade_count": house_photo_counts["facade"],

        "house_photo_lift_count": house_photo_counts["lift"],

        "house_photo_entrance_inside_count": house_photo_counts["entrance_inside"],

        "house_photo_entrance_outside_count": house_photo_counts["entrance_outside"],

        "house_photo_territory_count": house_photo_counts["territory"],

        "approve_for_mortgage": _to_bool(_first_not_none(

            legal_orig.get("approve"),

            legal_norm.get("approve"),

        )),

        "without_evaluation": _to_bool(_first_not_none(

            legal_orig.get("without_evaluation"),

            legal_norm.get("withoutEvaluation"),

        )),

        "is_individual_seller": _to_bool(_first_not_none(

            legal_orig.get("is_individual"),

            legal_norm.get("isIndividual"),

        )),

        "seller_cas_id": _to_int(_first_not_none(

            seller_agent_orig.get("cas_id"),

            seller_agent_norm.get("casId"),

        )),

        "seller_phone_visible": _to_bool(_first_not_none(

            seller_agent_orig.get("show_original_phone"),

            seller_agent_norm.get("showOriginalPhone"),

        )),

        "tariff_name": _first_not_none(

            tariff_orig.get("name"),

            tariff_norm.get("name"),

        ),

        "tariff_display_name": _first_not_none(

            tariff_orig.get("display_name"),

            tariff_norm.get("displayName"),

        ),

        "area_common_property": _to_float(_first_not_none(

            house_state.get("areaCommonProperty"),

        )),

        "area_residential_total": _to_float(_first_not_none(

            house_state.get("areaResidential"),

        )),

        "area_non_residential": _to_float(_first_not_none(

            house_state.get("areaNonResidential"),

        )),

        "parking_square": _to_float(_first_not_none(

            house_state.get("parkingSquare"),

        )),

        "gas_type": _to_bool(_first_not_none(

            house_state.get("gasType"),

        )),

        "sewerage_type": _first_not_none(

            house_state.get("sewerageType"),

        ),

        "electrical_type": _first_not_none(

            house_state.get("electricalType"),

        ),

        "has_family_mortgage": _to_bool(_first_not_none(

            original.get("has_family_mortgage"),

            product.get("hasFamilyMortgage"),

        )),

        "has_domclick_plan": bool(_first_not_none(

            deep_get(original, ["domclick_plan", "url"]),

            deep_get(product, ["domclickPlan", "url"]),

        )),

        "mortgage_badge": _to_bool(

            deep_get(product, ["mortgageBadge", "has_badge_info"])

        ),

        "base_credit_rate": _to_float(

            deep_get(product, ["mortgageBadge", "base_credit_rate"])

        ),

    }

    return parsed

def _get_product_card(state: dict[str, Any]) -> dict[str, Any]:

    product = state.get("productCard")

    return product if isinstance(product, dict) else {}

def _first_not_none(*values: Any) -> Any:

    for value in values:

        if value is not None:

            return value

    return None

def _first_non_empty_list(*values: Any) -> list[Any]:

    for value in values:

        if isinstance(value, list) and value:

            return value

    return []

def _to_int(value: Any) -> Optional[int]:

    try:

        if value is None or value == "":

            return None

        return int(float(value))

    except (TypeError, ValueError):

        return None

def _to_float(value: Any) -> Optional[float]:

    try:

        if value is None or value == "":

            return None

        return float(value)

    except (TypeError, ValueError):

        return None

def _to_bool(value: Any) -> Optional[bool]:

    if value is None:

        return None

    if isinstance(value, bool):

        return value

    if isinstance(value, (int, float)):

        return bool(value)

    if isinstance(value, str):

        low = value.strip().lower()

        if low in {"true", "1", "yes", "да", "есть"}:

            return True

        if low in {"false", "0", "no", "нет"}:

            return False

    return None

def _extract_display_name_or_value(*values: Any) -> Optional[str]:

    for value in values:

        if value is None:

            continue

        if isinstance(value, dict):

            display_name = value.get("display_name") or value.get("displayName")

            if display_name:

                return str(display_name)

        elif isinstance(value, str) and value.strip():

            return value.strip()

    return None

def _extract_named_items(items: list[Any]) -> tuple[list[str], list[str]]:

    keys: list[str] = []

    labels: list[str] = []

    for item in items:

        if isinstance(item, dict):

            key = item.get("key")

            label = item.get("display_name") or item.get("displayName")

            if key:

                keys.append(str(key))

            if label:

                labels.append(str(label))

        elif isinstance(item, str):

            labels.append(item)

    return keys, labels

def _extract_window_view_labels(value: Any) -> list[str]:

    result: list[str] = []

    if isinstance(value, list):

        for item in value:

            if isinstance(item, dict):

                label = item.get("display_name") or item.get("displayName")

                if label:

                    result.append(str(label))

            elif isinstance(item, str):

                result.append(item)

    return result

def _extract_parent_guid(address_orig: dict[str, Any], address_norm: dict[str, Any], kind: str) -> Optional[str]:

    parents = _first_not_none(address_orig.get("parents"), address_norm.get("parents"))

    if not isinstance(parents, list):

        return None

    for parent in parents:

        if isinstance(parent, dict) and parent.get("kind") == kind:

            guid = parent.get("guid")

            if guid:

                return str(guid)

    return None

def _extract_district(

    address_orig: dict[str, Any],

    address_norm: dict[str, Any],

) -> tuple[Optional[str], Optional[str], Optional[str]]:

    district_name = None

    district_guid = None

    district_slug = None

    parents = _first_not_none(

        address_orig.get("parents"),

        address_norm.get("parents"),

    )

    if isinstance(parents, list):

        for parent in parents:

            if isinstance(parent, dict) and parent.get("kind") == "district":

                district_name = parent.get("name")

                district_guid = parent.get("guid")

                break

    districts = _first_not_none(

        address_orig.get("districts"),

        address_norm.get("districts"),

    )

    if isinstance(districts, list) and districts:

        item = districts[0]

        if isinstance(item, dict):

            district_slug = item.get("slug")

            if district_name is None:

                district_name = item.get("short_name")

    return district_name, district_guid, district_slug

def _normalize_text(value: Any) -> Optional[str]:

    if not isinstance(value, str):

        return None

    return value.replace("\\n", "\n").strip()

def _extract_street(address_orig: dict[str, Any], address_norm: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:

    parents = _first_not_none(address_orig.get("parents"), address_norm.get("parents"))

    if not isinstance(parents, list):

        return None, None

    for parent in parents:

        if isinstance(parent, dict) and parent.get("kind") == "street":

            return parent.get("name"), parent.get("guid")

    return None, None

def _extract_house_number(address_orig: dict[str, Any], address_norm: dict[str, Any]) -> Optional[str]:

    name = _first_not_none(address_orig.get("name"), address_norm.get("name"))

    street = _extract_street(address_orig, address_norm)[0]

    if not isinstance(name, str):

        return None

    if street and isinstance(street, str) and name.startswith(street):

        raw = name[len(street):].strip(", ").strip()

        return raw or None

    parts = [p.strip() for p in name.split(",")]

    return parts[-1] if parts else None

def _calc_bathroom_count(object_orig: dict[str, Any], object_norm: dict[str, Any]) -> Optional[int]:

    connected = _to_int(_first_not_none(

        object_orig.get("connected_bathrooms"),

        object_norm.get("connectedBathrooms"),

    )) or 0

    separated = _to_int(_first_not_none(

        object_orig.get("separated_bathrooms"),

        object_norm.get("separatedBathrooms"),

    )) or 0

    total = connected + separated

    return total if total > 0 else None

def _detect_author_type(

    source: Any,

    is_owner: Any,

    is_agent: Any,

    company: Any,

) -> Optional[str]:

    if _to_bool(is_owner) is True and _to_bool(is_agent) is not True:

        return "owner"

    if _to_bool(is_agent) is True:

        return "agent"

    if source == "individual":

        return "owner"

    if isinstance(company, dict) and company:

        return "agency"

    return None

def parking_or_security_keys(keys: list[str]) -> set[str]:

    return set(keys or [])
