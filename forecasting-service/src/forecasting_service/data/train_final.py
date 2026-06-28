import pandas as pd

import numpy as np

from sklearn.model_selection import train_test_split, GridSearchCV

from sklearn.preprocessing import StandardScaler

from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

import xgboost as xgb

import joblib

from pathlib import Path

print("="*70)

print("🚀 СРАВНЕНИЕ МОДЕЛЕЙ: XGBoost vs Random Forest (total_price)")

print("="*70)

df = pd.read_csv('datasets/ml_dataset_final_v4.csv')

print(f"\n📥 Загружено: {len(df)} записей")

initial_count = len(df)

df = df[df['rooms_count'] <= 3].copy()

print(f"🗑️ Удалено 4+ комнатных: {initial_count - len(df)} записей")

print(f"✓ Осталось: {len(df)} записей")

print("\n📊 Распределение комнат:")

for rooms in [0, 1, 2, 3]:

    count = (df['rooms_count'] == rooms).sum()

    label = 'studio' if rooms == 0 else f'{rooms}room'

    print(f"  {label}: {count} ({count*100/len(df):.1f}%)")

meta_cols = ['id', 'url', 'price', 'price_per_sqm']

X = df.drop([col for col in meta_cols if col in df.columns] + ['total_price'], axis=1, errors='ignore')

if 'total_price' not in df.columns:

    df['total_price'] = df['price_per_sqm'] * df['total_meters']

    print(f"\n⚠️ Восстановлена total_price из price_per_sqm * total_meters")

y = df['total_price']

print(f"\n✓ Признаков: {X.shape[1]}")

print(f"✓ Целевая переменная: total_price")

print(f"  Min: {y.min():,.0f} руб")

print(f"  Max: {y.max():,.0f} руб")

print(f"  Mean: {y.mean():,.0f} руб")

print(f"  Median: {y.median():,.0f} руб")

y_log = np.log1p(y)

print(f"\n✓ Применено логарифмирование")

X_train, X_test, y_train, y_test = train_test_split(

    X, y_log, test_size=0.2, random_state=42

)

print(f"✓ Train: {len(X_train)}, Test: {len(X_test)}")

scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)

X_test_scaled = scaler.transform(X_test)

print("\n" + "="*70)

print("🌲 ОБУЧЕНИЕ XGBoost")

print("="*70)

param_grid_xgb = {

    'n_estimators': [200, 300, 500],

    'max_depth': [6, 8, 10],

    'learning_rate': [0.01, 0.05, 0.1],

    'subsample': [0.8, 1.0],

    'colsample_bytree': [0.8, 1.0]

}

xgb_model = xgb.XGBRegressor(

    objective='reg:squarederror',

    random_state=42,

    n_jobs=-1

)

grid_search_xgb = GridSearchCV(

    xgb_model, param_grid_xgb, cv=3,

    scoring='neg_mean_absolute_error',

    n_jobs=-1, verbose=1

)

grid_search_xgb.fit(X_train_scaled, y_train)

best_xgb = grid_search_xgb.best_estimator_

print(f"\n✓ Лучшие параметры XGBoost: {grid_search_xgb.best_params_}")

y_pred_xgb_log = best_xgb.predict(X_test_scaled)

y_pred_xgb = np.expm1(y_pred_xgb_log)

y_test_original = np.expm1(y_test)

r2_xgb = r2_score(y_test_original, y_pred_xgb)

mae_xgb = mean_absolute_error(y_test_original, y_pred_xgb)

rmse_xgb = np.sqrt(mean_squared_error(y_test_original, y_pred_xgb))

mape_xgb = np.mean(np.abs((y_test_original - y_pred_xgb) / y_test_original)) * 100

importance_xgb = pd.DataFrame({

    'feature': X.columns,

    'importance': best_xgb.feature_importances_

}).sort_values('importance', ascending=False)

print("\n" + "="*70)

print("🌳 ОБУЧЕНИЕ Random Forest")

print("="*70)

param_grid_rf = {

    'n_estimators': [100, 200, 300],

    'max_depth': [10, 15, 20, None],

    'min_samples_split': [2, 5, 10],

    'min_samples_leaf': [1, 2, 4]

}

rf_model = RandomForestRegressor(

    random_state=42,

    n_jobs=-1

)

grid_search_rf = GridSearchCV(

    rf_model, param_grid_rf, cv=3,

    scoring='neg_mean_absolute_error',

    n_jobs=-1, verbose=1

)

grid_search_rf.fit(X_train_scaled, y_train)

best_rf = grid_search_rf.best_estimator_

print(f"\n✓ Лучшие параметры Random Forest: {grid_search_rf.best_params_}")

y_pred_rf_log = best_rf.predict(X_test_scaled)

y_pred_rf = np.expm1(y_pred_rf_log)

r2_rf = r2_score(y_test_original, y_pred_rf)

mae_rf = mean_absolute_error(y_test_original, y_pred_rf)

rmse_rf = np.sqrt(mean_squared_error(y_test_original, y_pred_rf))

mape_rf = np.mean(np.abs((y_test_original - y_pred_rf) / y_test_original)) * 100

importance_rf = pd.DataFrame({

    'feature': X.columns,

    'importance': best_rf.feature_importances_

}).sort_values('importance', ascending=False)

print("\n" + "="*70)

print("📊 СРАВНЕНИЕ МОДЕЛЕЙ")

print("="*70)

print(f"\n{'Метрика':<20} {'XGBoost':<25} {'Random Forest':<25} {'Разница':<15}")

print("-" * 85)

print(f"{'R²':<20} {r2_xgb:<25.4f} {r2_rf:<25.4f} {r2_xgb - r2_rf:+.4f}")

print(f"{'MAE':<20} {mae_xgb:<25,.0f} {mae_rf:<25,.0f} {mae_xgb - mae_rf:+,.0f}")

print(f"{'RMSE':<20} {rmse_xgb:<25,.0f} {rmse_rf:<25,.0f} {rmse_xgb - rmse_rf:+,.0f}")

print(f"{'MAPE':<20} {mape_xgb:<25.2f}% {mape_rf:<25.2f}% {mape_xgb - mape_rf:+.2f}%")

print("\n" + "="*70)

print("🎯 ТОП-15 ВАЖНЫХ ПРИЗНАКОВ")

print("="*70)

print("\n🌲 XGBoost:")

print(importance_xgb.head(15).to_string(index=False))

print("\n🌳 Random Forest:")

print(importance_rf.head(15).to_string(index=False))

print("\n" + "="*70)

print("📈 СРАВНЕНИЕ ВАЖНОСТИ ПРИЗНАКОВ")

print("="*70)

comparison = pd.DataFrame({

    'feature': importance_xgb['feature'],

    'xgb_importance': importance_xgb['importance'],

    'rf_importance': importance_rf['importance']

}).head(20)

comparison['rank_diff'] = (

    comparison['rf_importance'].rank(ascending=False) - 

    comparison['xgb_importance'].rank(ascending=False)

)

print(comparison.to_string(index=False))

Path('models').mkdir(exist_ok=True)

joblib.dump(best_xgb, 'models/xgboost_total_price_final.pkl')

joblib.dump(best_rf, 'models/random_forest_total_price_final.pkl')

joblib.dump(scaler, 'models/scaler_total_price_final.pkl')

importance_xgb.to_csv('models/feature_importance_xgb_total_price.csv', index=False)

importance_rf.to_csv('models/feature_importance_rf_total_price.csv', index=False)

print("\n✅ Модели сохранены:")

print("  - models/xgboost_total_price_final.pkl")

print("  - models/random_forest_total_price_final.pkl")

print("  - models/scaler_total_price_final.pkl")

print("\n" + "="*70)

print("🏆 ИТОГОВОЕ СРАВНЕНИЕ")

print("="*70)

if r2_xgb > r2_rf:

    print(f"🥇 Лучшая модель: XGBoost (R²={r2_xgb:.4f})")

    print(f"   Превосходство над RF: +{r2_xgb - r2_rf:.4f} по R²")

    print(f"   MAE лучше на: {mae_rf - mae_xgb:,.0f} руб")

    print(f"   MAPE лучше на: {mape_rf - mape_xgb:.2f}%")

else:

    print(f"🥇 Лучшая модель: Random Forest (R²={r2_rf:.4f})")

    print(f"   Превосходство над XGBoost: +{r2_rf - r2_xgb:.4f} по R²")

print("\n✅ Готово!")

import json

feature_names = list(X.columns)

with open('models/feature_names.json', 'w') as f:

    json.dump(feature_names, f)

print(f"✅ Имена признаков сохранены: models/feature_names.json")

print(f"   Всего признаков: {len(feature_names)}")
