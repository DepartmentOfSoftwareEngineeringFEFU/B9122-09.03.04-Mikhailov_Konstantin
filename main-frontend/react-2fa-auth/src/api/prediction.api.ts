import { mainClient } from './client';

export interface FlatFeatures {
  total_meters: number;
  living_meters: number;
  kitchen_meters: number;
  rooms_count: number;
  floor: number;
  floors_count: number;
  district: string;
  house_type: string; // monolith, brick, panel...
  renovation_category: string;
  building_age: number;
  // ... остальные поля из FlatFeaturesSchema бэкенда
}

export interface PredictionResult {
  id: string;
  predicted_price: number;
  predicted_price_per_sqm: number;
  horizon: string;
  confidence: number;
  model_version: string;
  created_at: string;
}

export const predictionApi = {
  predict: async (features: FlatFeatures, horizon: string = 'now') => {
    const response = await mainClient.post<{ data: PredictionResult }>(
      '/predictions/',
      { features, horizon }
    );
    return response.data.data;
  },

  getHistory: async (limit = 20, offset = 0) => {
    const response = await mainClient.get('/predictions/', {
      params: { limit, offset },
    });
    return response.data.data;
  },

  deletePrediction: async (id: string) => {
    await mainClient.delete(`/predictions/${id}`);
  },
};