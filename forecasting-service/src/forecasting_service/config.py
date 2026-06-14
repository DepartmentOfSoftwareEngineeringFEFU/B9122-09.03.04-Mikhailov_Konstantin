from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATASETS_DIR = BASE_DIR / "datasets"

ARTIFACTS_DIR = BASE_DIR / "artifacts"

DEBUG_DIR = BASE_DIR / "debug"

PROJECT_ROOT = BASE_DIR.parent.parent.parent

LOGS_DIR = PROJECT_ROOT / "logs"

DEFAULT_DB_NAME = "flats.db"

LOCATION = "Владивосток"

DEAL_TYPE = "sale"

ROOMS_TO_PARSE = ("studio", 1, 2, 3, 4, 5, 6)

DEFAULT_START_PAGE = 1

DEFAULT_END_PAGE = 54

DEFAULT_PAGE_DELAY = (5.0, 15.0)

DEFAULT_DETAIL_DELAY = (20.0, 40.0)

DEFAULT_BATCH_SIZE = 30

DEFAULT_RESTART_EVERY = 7

CRITICAL_ML_FIELDS = (

    "price",

    "total_meters",

    "rooms_count",

    "district",

    "floor",

    "floors_count",

    "year_of_construction",

    "house_material_type",

    "finish_type",

)

COVERAGE_FIELDS = (

    "price", "total_meters", "rooms_count",

    "floor", "floors_count", "district",

    "microdistrict", "street", "house_number",

    "living_meters", "kitchen_meters",

    "ceiling_height", "object_type",

    "year_of_construction", "house_material_type",

    "finish_type", "bathroom_type", "bathroom_count",

    "elevator_passenger", "elevator_cargo",

    "parking_type", "floor_type",

    "heating_type", "balcony_count",

    "loggia_count", "window_view",

    "layout_type", "has_furniture",

    "latitude", "longitude",

    "address_guid", "district_guid", "district_slug", "street_guid",

    "locality", "locality_guid",

    "is_apartment", "has_gas", "has_redevelopment",

    "security_features", "yard_features", "infrastructure_features",

    "views_count", "calls_count", "favorites_count",

    "online_show", "chat_available",

    "price_history_json", "market_price",

    "hot_water_type",

    "offer_photos_count",

    "house_photos_count",

    "has_plan_photo",

    "has_window_photo",

    "approve_for_mortgage",

    "without_evaluation",

    "is_individual_seller",

    "tariff_name",

    "area_common_property",

    "area_residential_total",

    "has_family_mortgage",

    "has_domclick_plan",

)

DETAIL_FIELDS = (

    "living_meters", "kitchen_meters", "ceiling_height",

    "object_type", "layout_type",

    "bathroom_type", "bathroom_count",

    "window_view", "finish_type",

    "balcony_count", "loggia_count", "has_furniture",

    "year_of_construction", "house_material_type",

    "floor_type",

    "elevator_passenger", "elevator_cargo",

    "entrances_count",

    "has_garbage_chute", "has_ramp", "has_concierge",

    "parking_type", "heating_type", "is_emergency",

    "jk_name", "jk_class", "jk_deadline", "developer",

    "cadastral_number", "encumbrances", "owners_count",

    "latitude", "longitude",

    "address_guid",

    "district_guid", "district_slug",

    "street_guid",

    "locality", "locality_guid", "province_guid",

    "timezone", "timezone_offset",

    "is_apartment",

    "window_view_json",

    "has_gas",

    "has_redevelopment",

    "quarters_count",

    "living_quarters_count",

    "hot_water_type",

    "cold_water_type",

    "foundation_type",

    "ventilation_type",

    "energy_efficiency",

    "has_intercom",

    "has_closed_territory",

    "has_code_door",

    "has_garage",

    "security_features",

    "yard_features",

    "infrastructure_features",

    "parking_keys_json",

    "security_keys_json",

    "yard_keys_json",

    "infrastructure_keys_json",

    "jk_id",

    "jk_slug",

    "is_owner",

    "owner_minors",

    "residence_minors",

    "years_ownership",

    "sale_type",

    "seller_name",

    "seller_phone_masked",

    "seller_is_agent",

    "seller_is_sbol_verified",

    "seller_is_esia_verified",

    "seller_company_name",

    "seller_company_id",

    "source_type",

    "views_count",

    "calls_count",

    "favorites_count",

    "online_show",

    "chat_available",

    "is_auction",

    "is_exclusive",

    "is_placement_paid",

    "duplicates_offer_count",

    "published_at_source",

    "updated_at_source",

    "description",

    "egrn_area_status",

    "egrn_floor_status",

    "egrn_owners_status",

    "collateral",

    "collateral_sber",

    "market_price_min",

    "market_price_max",

    "market_price",

    "rent_long_predicted",

    "rent_short_predicted",

    "repair_quality_predicted",

    "price_history_json",

    "offer_photos_json",

    "house_photos_json",

    "address_parents_json",

    "discounts_json",

    "offer_photos_count",

    "house_photos_count",

    "has_plan_photo",

    "has_window_photo",

    "house_photo_facade_count",

    "house_photo_lift_count",

    "house_photo_entrance_inside_count",

    "house_photo_entrance_outside_count",

    "house_photo_territory_count",

    "approve_for_mortgage",

    "without_evaluation",

    "is_individual_seller",

    "seller_cas_id",

    "seller_phone_visible",

    "tariff_name",

    "tariff_display_name",

    "area_common_property",

    "area_residential_total",

    "area_non_residential",

    "parking_square",

    "gas_type",

    "sewerage_type",

    "electrical_type",

    "has_family_mortgage",

    "has_domclick_plan",

    "mortgage_badge",

    "base_credit_rate",

)

JSON_DETAIL_FIELDS = (

    "window_view_json",

    "parking_keys_json",

    "security_keys_json",

    "yard_keys_json",

    "infrastructure_keys_json",

    "price_history_json",

    "offer_photos_json",

    "house_photos_json",

    "address_parents_json",

    "discounts_json",

)
