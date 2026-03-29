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
)