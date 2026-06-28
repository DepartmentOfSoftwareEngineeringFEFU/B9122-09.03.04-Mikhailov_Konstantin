import pandas as pd

import numpy as np

import json

from pathlib import Path

print("="*70)

print("🚀 FEATURE ENGINEERING FINAL v4 (без GUID-конфликтов)")

print("="*70)

df = pd.read_csv('dataset.csv', sep=',', encoding='utf-8')

print(f"\n📥 Загружено: {len(df)} записей")

df = df[df['detail_status'] == 'done'].copy()

df = df[(df['total_meters'] >= 10) & (df['total_meters'] <= 300)]

df['price_per_sqm'] = df['price'] / df['total_meters']

df = df[(df['price_per_sqm'] >= 30000) & (df['price_per_sqm'] <= 500000)]

print(f"✓ После фильтрации и очистки: {len(df)} записей")

cols_to_drop = [

    'id', 'url', 'source', 'source_id', 'cian_id', 'address_raw',

    'detail_status', 'detail_attempts', 'last_attempt_at', 'created_at', 'updated_at',

    'address_parents_json', 'window_view_json', 'infrastructure_keys_json',

    'house_photos_json', 'parking_keys_json', 'security_keys_json', 'yard_keys_json',

    'discounts_json', 'price_history_json', 'offer_photos_json',

    'district_guid', 'address_guid', 'locality_guid', 'street_guid', 'province_guid',

    'district_slug', 'microdistrict', 'street', 'house_number', 'underground',

    'residential_complex', 'jk_slug', 'jk_id', 'title_raw', 'author', 'author_type',

    'seller_name', 'seller_phone_masked', 'seller_is_agent', 'seller_company_name',

    'seller_company_id', 'source_type', 'tariff_name', 'tariff_display_name',

    'market_price', 'market_price_min', 'market_price_max', 'rent_long_predicted',

    'rent_short_predicted', 'repair_quality_predicted', 'base_credit_rate',

    'has_family_mortgage', 'mortgage_badge', 'approve_for_mortgage', 'without_evaluation',

    'is_auction', 'online_show', 'chat_available', 'is_exclusive', 'is_placement_paid',

    'duplicates_offer_count', 'published_at_source', 'updated_at_source'

]

existing_drop = [c for c in cols_to_drop if c in df.columns]

df = df.drop(columns=existing_drop)

print(f"🗑️ Удалено {len(existing_drop)} служебных колонок")

def extract_district(address_json, slug):

    try:

        if pd.notna(address_json) and address_json != '[]':

            data = json.loads(address_json)

            for item in data:

                if 'район' in item.get('name', '').lower() or item.get('kind') == 'district':

                    return item.get('name')

    except: pass

    if pd.notna(slug):

        slug_map = {'pervomajskij':'Первомайский', 'sovetskij':'Советский', 

                    'leninskij':'Ленинский', 'frunzenskij':'Фрунзенский', 'pervorechenskij':'Первореченский'}

        for k, v in slug_map.items():

            if k in slug.lower(): return v

    return 'unknown'

df['district'] = df.apply(lambda r: extract_district(r.get('address_parents_json'), r.get('district_slug')), axis=1)

df['year_of_construction'] = df.groupby('jk_name')['year_of_construction'].transform('median').fillna(df['year_of_construction'].median())

df['latitude'] = df['latitude'].fillna(df.groupby('district')['latitude'].transform('mean')).fillna(43.1155)

df['longitude'] = df['longitude'].fillna(df.groupby('district')['longitude'].transform('mean')).fillna(131.8855)

CENTER_LAT, CENTER_LON = 43.1155, 131.8855

SEA_LAT, SEA_LON = 43.1000, 131.9200

df['dist_to_center_km'] = np.sqrt((df['latitude']-CENTER_LAT)**2 + (df['longitude']-CENTER_LON)**2) * 111

df['dist_to_sea_km'] = np.sqrt((df['latitude']-SEA_LAT)**2 + (df['longitude']-SEA_LON)**2) * 111

df['building_age'] = 2026 - df['year_of_construction']

df['living_meters'] = df['living_meters'].fillna(df['total_meters'] * 0.70)

df['kitchen_meters'] = df['kitchen_meters'].fillna(df['total_meters'] * 0.15)

bool_cols = ['has_intercom','has_closed_territory','has_code_door','has_garage','has_concierge']

for c in bool_cols:

    if c in df.columns: df[c] = df[c].fillna(0).astype(int)

for c in ['offer_photos_count','house_photos_count','has_plan_photo']:

    if c in df.columns: df[c] = df[c].fillna(0).astype(int)

df['house_material_type'] = df.get('house_material_type', pd.Series()).fillna('unknown')

df['finish_type'] = df.get('finish_type', pd.Series()).fillna('unknown')

df['jk_class'] = df.get('jk_class', pd.Series()).fillna('unknown')

df['infrastructure_keys_json'] = df.get('infrastructure_keys_json', pd.Series()).fillna('[]')

df['living_ratio'] = df['living_meters'] / df['total_meters']

df['kitchen_ratio'] = df['kitchen_meters'] / df['total_meters']

df['floor_ratio'] = df['floor'] / df['floors_count']

def cat_floor(r):

    if r['floor']==1: return 'ground'

    if r['floor']==r['floors_count']: return 'top'

    if r['floor_ratio']<0.33: return 'low'

    if r['floor_ratio']<0.66: return 'mid'

    return 'high'

df['floor_category'] = df.apply(cat_floor, axis=1)

df['rooms_category'] = df['rooms_count'].map({0:'studio',1:'1room',2:'2room',3:'3room'}).fillna('4plus')

df['house_type'] = df['house_material_type'].str.lower().apply(lambda x: 'monolith' if 'монолит' in x else 'brick' if 'кирпич' in x else 'panel' if 'панель' in x else 'block' if 'блоч' in x else 'unknown')

df['renovation_category'] = df['finish_type'].str.lower().apply(lambda x: 'premium' if any(w in x for w in ['дизайнер','евро']) else 'cosmetic' if any(w in x for w in ['косметич','чистов']) else 'pre_finish' if 'предчистов' in x else 'none' if any(w in x for w in ['без','чернов']) else 'standard')

df['jk_class_category'] = df['jk_class'].str.lower().apply(lambda x: 'economy' if 'эконом' in x else 'comfort' if 'комфорт' in x else 'business' if 'бизнес' in x else 'premium' if any(w in x for w in ['премиум','элит']) else 'unknown')

def cat_window(j):

    try:

        if pd.isna(j) or j=='[]': return 'unknown'

        v = json.loads(j)[0].lower()

        return 'yard' if 'двор' in v else 'street' if 'улиц' in v else 'park' if 'парк' in v else 'water' if any(w in v for w in ['вод','мор']) else 'other'

    except: return 'unknown'

df['window_view_category'] = df.get('window_view_json', pd.Series()).apply(cat_window)

def count_infra(j):

    try: return len(json.loads(j)) if pd.notna(j) and j!='[]' else 0

    except: return 0

df['infrastructure_count'] = df.get('infrastructure_keys_json', pd.Series()).apply(count_infra)

df['security_score'] = df['has_intercom'] + df['has_closed_territory'] + df['has_code_door']

df['building_age_category'] = df['building_age'].apply(lambda a: 'new' if a<=5 else 'modern' if a<=15 else 'old' if a<=35 else 'very_old')

categorical_cols = ['rooms_category','floor_category','house_type','renovation_category',

                    'jk_class_category','building_age_category','window_view_category','district']

for c in categorical_cols:

    df[c] = df[c].fillna('unknown').astype(str)

df_encoded = pd.get_dummies(df, columns=categorical_cols, prefix=categorical_cols, dummy_na=False)

prefixes = [f"{cat}_" for cat in categorical_cols]

one_hot_cols = [col for col in df_encoded.columns if any(col.startswith(p) for p in prefixes)]

for col in one_hot_cols:

    df_encoded[col] = df_encoded[col].fillna(0).astype(int)

print(f"✓ One-hot колонок создано: {len(one_hot_cols)}")

ml_features = [

    'price_per_sqm', 'total_meters', 'living_meters', 'kitchen_meters',

    'rooms_count', 'floor', 'floors_count', 'floor_ratio', 'living_ratio', 'kitchen_ratio',

    'building_age', 'year_of_construction', 'latitude', 'longitude',

    'dist_to_center_km', 'dist_to_sea_km', 'infrastructure_count', 'security_score',

    'has_intercom', 'has_closed_territory', 'has_code_door', 'has_garage', 'has_concierge',

    'offer_photos_count', 'house_photos_count', 'has_plan_photo'

] + one_hot_cols

final_df = df_encoded[[c for c in ml_features if c in df_encoded.columns]].copy()

final_df = final_df.fillna(0)            

Path('datasets').mkdir(exist_ok=True)

final_df.to_csv('datasets/ml_dataset_final_v4.csv', index=False)

print(f"\n✅ Сохранено: {len(final_df)} записей, {len(final_df.columns)} признаков")

print(f"\n📊 price_per_sqm: min={final_df['price_per_sqm'].min():.0f}, max={final_df['price_per_sqm'].max():.0f}, mean={final_df['price_per_sqm'].mean():.0f}")

print("✅ Готово к обучению!")
