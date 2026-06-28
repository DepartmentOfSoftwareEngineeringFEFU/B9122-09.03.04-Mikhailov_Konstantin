// src/stores/useAuthStore.ts
import { create } from 'zustand';
import {
  authApi,
  profileApi,
  isTwoFactorRequired,
  type UserResponse,
  type LoginResponse,
  type TwoFactorRequiredResponse,
} from '@/api/auth.api';
import { storage } from '@/utils/storage';

interface PendingTwoFactor {
  auth_token: string;
  expires_in: number;
}

interface AuthState {
  // Состояние
  user: UserResponse | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isInitialized: boolean;
  isLoading: boolean;

  // 2FA промежуточное состояние (при логине)
  pendingTwoFactor: PendingTwoFactor | null;

  // Действия
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<'success' | '2fa_required'>;
  login2FA: (totpCode: string) => Promise<void>;
  cancelTwoFactor: () => void;
  register: (
    username: string,
    email: string,
    password: string,
    phone_number?: string
  ) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  refreshTokens: () => Promise<void>;
  fetchProfile: () => Promise<void>;
  setUser: (user: UserResponse) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isInitialized: false,
  isLoading: false,
  pendingTwoFactor: null,

  initialize: async () => {
    const storedAccessToken = localStorage.getItem('access_token');
    const storedRefreshToken = localStorage.getItem('refresh_token');

    if (!storedAccessToken || !storedRefreshToken) {
      set({ isInitialized: true });
      return;
    }

    set({
      accessToken: storedAccessToken,
      refreshToken: storedRefreshToken,
    });

    try {
      const response = await profileApi.getMe();
      set({
        user: response.data.data,
        isAuthenticated: true,
        isInitialized: true,
      });
    } catch {
      // Токен невалидный — пробуем обновить
      try {
        await get().refreshTokens();
        const response = await profileApi.getMe();
        set({
          user: response.data.data,
          isAuthenticated: true,
          isInitialized: true,
        });
      } catch {
        get().clearAuth();
        set({ isInitialized: true });
      }
    }
  },

  login: async (email, password) => {
    set({ isLoading: true });
    try {
      const response = await authApi.login({ email, password });
      const data = response.data.data;

      if (isTwoFactorRequired(data)) {
        // 2FA required — сохраняем auth_token, НЕ сохраняем пароль
        set({
          pendingTwoFactor: {
            auth_token: data.auth_token,
            expires_in: data.expires_in,
          },
          isLoading: false,
        });
        return '2fa_required';
      }

      // Обычный логин без 2FA
      const tokens = data as LoginResponse;
      _saveTokens(tokens, set);

      // Загружаем профиль
      const profileResponse = await profileApi.getMe();
      set({
        user: profileResponse.data.data,
        isAuthenticated: true,
        isLoading: false,
      });

      return 'success';
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  login2FA: async (totpCode) => {
    const { pendingTwoFactor } = get();
    if (!pendingTwoFactor) {
      throw new Error('No pending 2FA session');
    }

    set({ isLoading: true });
    try {
      const response = await authApi.login2FA({
        auth_token: pendingTwoFactor.auth_token,
        totp_code: totpCode,
      });

      const tokens = response.data.data;
      _saveTokens(tokens, set);

      // Очищаем pendingTwoFactor
      set({ pendingTwoFactor: null });

      // Загружаем профиль
      const profileResponse = await profileApi.getMe();
      set({
        user: profileResponse.data.data,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  cancelTwoFactor: () => {
    set({ pendingTwoFactor: null });
  },

  register: async (email: string, password: string, username?: string) => {
    set({ isLoading: true })
    console.log('1')

    try {
      await authApi.register({ email, password, username })
      console.log('2')
      set({ isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      console.log('3')
      throw error
    }
  },

  logout: async () => {
    const { refreshToken } = get();
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      // Игнорируем ошибки при логауте
    } finally {
      get().clearAuth();
    }
  },

  logoutAll: async () => {
    try {
      await authApi.logoutAll();
    } catch {
      // Ignore
    } finally {
      storage.clearTokens()
      get().clearAuth();
    }
  },

  refreshTokens: async () => {
    const { refreshToken } = get();
    if (!refreshToken) throw new Error('No refresh token');

    const response = await authApi.refresh(refreshToken);
    const tokens = response.data.data;
    _saveTokens(tokens, set);
  },

  fetchProfile: async () => {
    const response = await profileApi.getMe();
    set({ user: response.data.data });
  },

  setUser: (user) => set({ user }),

  clearAuth: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      pendingTwoFactor: null,
    });
  },
}));

// Вспомогательная функция
function _saveTokens(
  tokens: LoginResponse,
  set: (state: Partial<AuthState>) => void
) {
  localStorage.setItem('access_token', tokens.access_token);
  localStorage.setItem('refresh_token', tokens.refresh_token);
  set({
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
  });
}