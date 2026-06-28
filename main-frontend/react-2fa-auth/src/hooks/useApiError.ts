// hooks/useApiError.ts - добавьте обработку специфичных ошибок 2FA

import { AxiosError } from 'axios';
import { toast } from 'sonner';

interface ApiErrorResponse {
  detail?: string | { msg: string }[];
  message?: string;
  error?: {
    code: string;
    message: string;
  };
}

export function useApiError() {
  const handleError = (error: unknown, fallbackMessage = 'Произошла ошибка') => {
    if (error instanceof AxiosError) {
      const data = error.response?.data as ApiErrorResponse | undefined;
      const status = error.response?.status;

      // Специфичные ошибки 2FA
      if (data?.error?.code === 'INVALID_TOTP_CODE') {
        toast.error('Неверный код подтверждения. Попробуйте ещё раз.');
        return 'Неверный код подтверждения';
      }

      if (data?.error?.code === 'TWO_FACTOR_REQUIRED') {
        toast.error('Требуется двухфакторная аутентификация');
        return 'Требуется 2FA';
      }

      if (data?.error?.code === 'AUTH_TOKEN_EXPIRED') {
        toast.error('Время на ввод кода истекло. Войдите заново.');
        return 'Время истекло';
      }

      // Общие ошибки
      if (data?.error?.message) {
        toast.error(data.error.message);
        return data.error.message;
      }

      if (status === 401) {
        toast.error('Неверные учётные данные');
        return 'Неверные учётные данные';
      }

      if (status === 429) {
        toast.error('Слишком много попыток. Подождите немного.');
        return 'Слишком много попыток';
      }
    }

    toast.error(fallbackMessage);
    return fallbackMessage;
  };

  return { handleError };
}