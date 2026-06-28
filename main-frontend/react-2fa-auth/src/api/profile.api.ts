import { authClient } from "./client"
import type { Profile, ChangePasswordRequest, TwoFactorSetupResponse } from '@/types'

// Тип обёртки ответа от бэкенда
interface ApiResponse<T> {
  status: string
  data: T
  meta?: Record<string, unknown>
  timestamp?: string
}

export const profileApi = {
  // Получить профиль текущего пользователя
  getMe: async (): Promise<Profile> => {
    const response = await authClient.get<ApiResponse<Profile>>('/profile/me')
    return response.data.data
  },

  // Сменить пароль
  changePassword: async (data: ChangePasswordRequest): Promise<void> => {
    await authClient.patch('/profile/me/password', data)
  },

  // Обновить username
  updateUsername: async (username: string): Promise<Profile> => {
    const response = await authClient.patch<ApiResponse<Profile>>('/profile/me/username', {
      new_username: username,
    })
    return response.data.data
  },

  // Обновить телефон
  updatePhone: async (phone_number: string): Promise<Profile> => {
    const response = await authClient.patch<ApiResponse<Profile>>('/profile/me/phone', {
      new_phone_number: phone_number,
    })
    return response.data.data
  },

  // Настройка 2FA — получить QR код
  setup2FA: async (): Promise<TwoFactorSetupResponse> => {
    const response = await authClient.post<ApiResponse<TwoFactorSetupResponse>>(
      '/profile/me/2fa/setup'
    )
    return response.data.data
  },

  // Подтвердить и активировать 2FA
  confirm2FA: async (code: string): Promise<void> => {
    await authClient.post('/profile/me/2fa/confirm', { code })
  },

  // Отключить 2FA
  disable2FA: async (code: string): Promise<void> => {
    await authClient.post('/profile/me/2fa/disable', { code })
  },
}