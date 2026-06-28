import axios from 'axios';
import { useAuthStore } from '@/store/auth.store';

const createClient = (baseURL: string) => {
  const client = axios.create({
    baseURL,
    headers: { 'Content-Type': 'application/json' },
  });

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        try {
          await useAuthStore.getState().refreshTokens();
          const newToken = useAuthStore.getState().accessToken;
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return client(originalRequest);
        } catch (refreshError) {
          useAuthStore.getState().clearAuth();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
      return Promise.reject(error);
    }
  );

  return client;
};

export const authClient = createClient(import.meta.env.VITE_API_AUTH_URL);
export const mainClient = createClient(import.meta.env.VITE_API_MAIN_URL);