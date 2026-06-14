from __future__ import annotations

import json

import logging

from pathlib import Path

from typing import Optional

import joblib

import numpy as np

import pandas as pd

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class FlatFeatures(BaseModel):

    total_meters: float

    living_meters: float

    kitchen_meters: float

    rooms_count: int

    floor: int

    floors_count: int

    floor_ratio: float

    living_ratio: float

    kitchen_ratio: float

    building_age: float

    year_of_construction: float

    latitude: float

    longitude: float

    dist_to_center_km: float

    dist_to_sea_km: float

    infrastructure_count: int

    security_score: int

    has_intercom: int

    has_closed_territory: int

    has_code_door: int

    has_garage: int

    has_concierge: int

    offer_photos_count: int

    house_photos_count: int

    has_plan_photo: int

class PredictionResult(BaseModel):

    predicted_price: float

    predicted_price_per_sqm: float

    confidence: float

    model_version: str

class PricePredictor:

    def __init__(self, model_path: str | Path, scaler_path: str | Path, feature_names_path: str | Path):

        self._model_path = Path(model_path)

        self._scaler_path = Path(scaler_path)

        self._feature_names_path = Path(feature_names_path)

        self._model = None

        self._scaler = None

        self._feature_names: list[str] = []

        self._model_version: str = "xgboost_total_price_v1"

        self._load_model()

    def _load_model(self) -> None:

        try:

            logger.info(f"Loading model from {self._model_path}")

            self._model = joblib.load(self._model_path)

            logger.info(f"Loading scaler from {self._scaler_path}")

            self._scaler = joblib.load(self._scaler_path)

            logger.info(f"Loading feature names from {self._feature_names_path}")

            if self._feature_names_path.exists():

                with open(self._feature_names_path, 'r') as f:

                    self._feature_names = json.load(f)

                logger.info(f"✅ Loaded {len(self._feature_names)} feature names from JSON")

            else:

                logger.warning("Feature names JSON not found, trying to extract from model...")

                self._feature_names = self._extract_feature_names_from_model()

            if not self._feature_names:

                raise ValueError("Could not determine feature names")

            logger.info(

                f"✅ Model loaded successfully. "

                f"Features: {len(self._feature_names)}"

            )

        except FileNotFoundError as e:

            logger.error(f"Model file not found: {e}")

            raise

        except Exception as e:

            logger.error(f"Failed to load model: {e}", exc_info=True)

            raise

    def _extract_feature_names_from_model(self) -> list[str]:

        if hasattr(self._model, 'feature_names_in_'):

            names = self._model.feature_names_in_

            if names is not None:

                return list(names)

        if hasattr(self._model, 'get_booster'):

            try:

                booster = self._model.get_booster()

                if booster.feature_names:

                    return booster.feature_names

            except Exception:

                pass

        if hasattr(self._scaler, 'feature_names_in_'):

            names = self._scaler.feature_names_in_

            if names is not None:

                return list(names)

        logger.warning("Could not extract feature names from model/scaler")

        return []

    def predict(self, features: FlatFeatures) -> PredictionResult:

        if self._model is None or self._scaler is None:

            raise RuntimeError("Model not loaded")

        features_dict = features.model_dump()

        df = pd.DataFrame([features_dict])

        for feature_name in self._feature_names:

            if feature_name not in df.columns:

                df[feature_name] = 0

        df = df[self._feature_names]

        X_scaled = self._scaler.transform(df)

        y_pred_log = self._model.predict(X_scaled)

        y_pred = np.expm1(y_pred_log)                           

        predicted_price = float(y_pred[0])

        predicted_price_per_sqm = predicted_price / features.total_meters

        confidence = 0.85                             

        return PredictionResult(

            predicted_price=predicted_price,

            predicted_price_per_sqm=predicted_price_per_sqm,

            confidence=confidence,

            model_version=self._model_version,

        )
