import { PasswordResetRequest } from '@/types/auth.types';
import { authClient } from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface TwoFactorRequiredResponse {
  requires_2fa: boolean;
  auth_token: string;
  expires_in: number;
}

export interface Login2FARequest {
  auth_token: string;
  totp_code: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  phone_number?: string;
}

export interface UserResponse {
  uid: string;
  username: string;
  email: string;
  phone_number: string | null;
  role: string;
  is_active: boolean;
  is_email_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface Setup2FAResponse {
  qr_code_base64: string;
  secret: string;
  uri: string;
  message: string;
}

export interface ApiResponse<T> {
  status: string;
  data: T;
  meta: Record<string, any>;
  timestamp: string;
}

export interface ApiErrorResponse {
  status: string;
  error: {
    code: string;
    message: string;
    details: any;
  };
  timestamp: string;
}

// === Функция определения типа ответа логина ===

export function isTwoFactorRequired(
  data: LoginResponse | TwoFactorRequiredResponse
): data is TwoFactorRequiredResponse {
  return 'requires_2fa' in data && data.requires_2fa === true;
}

// === API вызовы ===

export const authApi = {
  register: (data: RegisterRequest) =>
    authClient.post<ApiResponse<UserResponse>>('/auth/register', data),

  login: (data: LoginRequest) =>
    authClient.post<ApiResponse<LoginResponse | TwoFactorRequiredResponse>>(
      '/auth/login',
      data
    ),

  login2FA: (data: Login2FARequest) =>
    authClient.post<ApiResponse<LoginResponse>>('/auth/login/2fa', data),

  refresh: (refresh_token: string) =>
    authClient.post<ApiResponse<LoginResponse>>('/auth/refresh', {
      refresh_token,
    }),

  logout: (refresh_token: string) =>
    authClient.post<ApiResponse<{ message: string }>>('/auth/logout', {
      refresh_token,
    }),

  logoutAll: () =>
    authClient.post<ApiResponse<{ message: string }>>('/auth/logout-all'),

  getSessions: () =>
    authClient.get<
      ApiResponse<
        Array<{
          device: string;
          ip_address: string | null;
          created_at: string;
          last_used_at: string | null;
        }>
      >
    >('/auth/sessions'),

  confirmEmail: async (token: string): Promise<void> => {
    await authClient.post('/auth/email-confirm', { token })
  },

  // Повторная отправка письма подтверждения
  resendConfirmation: async (email: string): Promise<void> => {
    await authClient.post('/auth/resend-confirmation', { email })
  },

  // Запрос сброса пароля
  requestPasswordReset: async (data: PasswordResetRequest): Promise<void> => {
    await authClient.post('/auth/password-reset', data)
  },

  // Подтверждение сброса пароля
  confirmPasswordReset: async (data: PasswordResetRequest): Promise<void> => {
    await authClient.post('/auth/password-reset/confirm', data)
  },
};

export const profileApi = {
  getMe: () => authClient.get<ApiResponse<UserResponse>>('/profile/me'),

  changePassword: (current_password: string, new_password: string) =>
    authClient.patch<ApiResponse<{ message: string }>>('/profile/me/password', {
      current_password,
      new_password,
    }),

  changeUsername: (new_username: string) =>
    authClient.patch<ApiResponse<UserResponse>>('/profile/me/username', {
      new_username,
    }),

  changePhone: (new_phone_number: string | null) =>
    authClient.patch<ApiResponse<UserResponse>>('/profile/me/phone', {
      new_phone_number,
    }),

  setup2FA: () =>
    authClient.post<ApiResponse<Setup2FAResponse>>('/profile/me/2fa/setup'),

  confirm2FA: (code: string) =>
    authClient.post<ApiResponse<{ message: string }>>('/profile/me/2fa/confirm', {
      code,
    }),

  disable2FA: (code: string, password: string) =>
    authClient.post<ApiResponse<{ message: string }>>('/profile/me/2fa/disable', {
      code,
      password,
    }),
};