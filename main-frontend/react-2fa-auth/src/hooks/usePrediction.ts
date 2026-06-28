import { useState } from 'react';
import { toast } from 'sonner';
import { predictionApi, type FlatFeatures, type PredictionResult } from '@/api/prediction.api';
import { useApiError } from './useApiError';

export function usePrediction() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [history, setHistory] = useState<PredictionResult[]>([]);
  const { handleError } = useApiError();

  const predict = async (features: FlatFeatures, horizon: string = 'now') => {
    setIsLoading(true);
    try {
      const res = await predictionApi.predict(features, horizon);
      setResult(res);
      toast.success('Прогноз успешно рассчитан');
      return res;
    } catch (error) {
      handleError(error, 'Ошибка расчёта прогноза');
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const loadHistory = async () => {
    setIsLoading(true);
    try {
      const data = await predictionApi.getHistory();
      setHistory(data.items);
    } catch (error) {
      handleError(error, 'Ошибка загрузки истории');
    } finally {
      setIsLoading(false);
    }
  };

  return { isLoading, result, history, predict, loadHistory };
}