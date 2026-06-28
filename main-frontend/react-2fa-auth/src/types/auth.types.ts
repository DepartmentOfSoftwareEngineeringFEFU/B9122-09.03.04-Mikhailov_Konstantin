// Запросы
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  username?: string
}

export interface RefreshTokenRequest {
  refresh_token: string
}

export interface PasswordResetRequest {
  email: string
}

export interface PasswordResetConfirmRequest {
  token: string
  new_password: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

// Ответы
export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginResponse {
  // Успешный логин
  access_token?: string
  refresh_token?: string
  token_type?: string
  expires_in?: number
}

export interface TwoFactorSetupResponse {
  qr_code_base64: string
  secret: string
  uri: string
  message?: string
}

export interface AuthTokenResponse {
  requires_2fa: true;
  auth_token: string;
  expires_in: number;
}

export type LoginFinalResponse = AuthTokens | AuthTokenResponse;

export const requires2FA = (response: LoginResponse): response is AuthTokenResponse => {
  return 'requires_2fa' in response && response.requires_2fa === true;
};


export interface Login2FARequest {
  auth_token: string;
  totp_code: string;
}