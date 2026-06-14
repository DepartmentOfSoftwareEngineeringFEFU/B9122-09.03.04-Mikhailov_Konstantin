from functools import lru_cache

from pathlib import Path

from ..ml.predictor import PricePredictor

MODELS_DIR = Path(__file__).parent.parent.parent.parent / "src" / "forecasting_service" / "data" / "models"

@lru_cache

def get_predictor() -> PricePredictor:

    model_path = MODELS_DIR / "xgboost_total_price_final.pkl"

    scaler_path = MODELS_DIR / "scaler_total_price_final.pkl"

    feature_names_path = MODELS_DIR / "feature_names.json"

    return PricePredictor(

        model_path=model_path,

        scaler_path=scaler_path,

        feature_names_path=feature_names_path,

    )
