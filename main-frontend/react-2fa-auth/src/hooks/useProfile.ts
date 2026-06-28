import { useState } from 'react'
import { toast } from 'sonner'
import { profileApi, authApi } from '@/api'
import { useAuth, useApiError } from '@/hooks'
import type { Session, TwoFactorSetupResponse } from '@/types'
import { storage } from '@/utils/storage'

export function useProfile() {
  const { user, refreshUser } = useAuth()
  const { handleError } = useApiError()

  const [isLoading, setIsLoading] = useState(false)
  const [sessions, setSessions] = useState<Session[]>([])
  const [twoFactorData, setTwoFactorData] = useState<TwoFactorSetupResponse | null>(null)

  // Смена пароля
  const changePassword = async (currentPassword: string, newPassword: string) => {
    setIsLoading(true)
    try {
      await profileApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      toast.success('Пароль успешно изменён')
      return true
    } catch (error) {
      handleError(error, 'Ошибка смены пароля')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Обновление username
  const updateUsername = async (username: string) => {
    setIsLoading(true)
    try {
      await profileApi.updateUsername(username)
      await refreshUser()
      toast.success('Имя пользователя обновлено')
      return true
    } catch (error) {
      handleError(error, 'Ошибка обновления')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Обновление телефона
  const updatePhone = async (phone_number: string) => {
    setIsLoading(true)
    try {
      await profileApi.updatePhone(phone_number)
      await refreshUser()
      toast.success('Телефон обновлён')
      return true
    } catch (error) {
      handleError(error, 'Ошибка обновления')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Загрузка сессий
  const loadSessions = async () => {
    setIsLoading(true)
    try {
      const data = await authApi.getSessions()
      setSessions(data)
    } catch (error) {
      handleError(error, 'Ошибка загрузки сессий')
    } finally {
      setIsLoading(false)
    }
  }

  // Выход со всех устройств
  const logoutAllSessions = async () => {
    setIsLoading(true)
    try {
      await authApi.logoutAll()
      toast.success('Вы вышли со всех устройств!')
      return true
    } catch (error) {
      handleError(error, 'Ошибка выхода')
      return false
    } finally {
      setIsLoading(false)
      storage.clearTokens()
      window.location.href = '/login'
    }
  }

  // Начать настройку 2FA
  const setup2FA = async () => {
    setIsLoading(true)
    try {
      const data = await profileApi.setup2FA()
      setTwoFactorData(data)
      return data
    } catch (error) {
      handleError(error, 'Ошибка настройки 2FA')
      return null
    } finally {
      setIsLoading(false)
    }
  }

  // Подтвердить 2FA
  const confirm2FA = async (code: string) => {
    setIsLoading(true)
    try {
      await profileApi.confirm2FA(code)
      await refreshUser()
      setTwoFactorData(null)
      toast.success('Двухфакторная аутентификация включена')
      return true
    } catch (error) {
      handleError(error, 'Неверный код')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Отключить 2FA
  const disable2FA = async (code: string) => {
    setIsLoading(true)
    try {
      await profileApi.disable2FA(code)
      await refreshUser()
      toast.success('Двухфакторная аутентификация отключена')
      return true
    } catch (error) {
      handleError(error, 'Неверный код')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Сброс данных 2FA
  const reset2FASetup = () => {
    setTwoFactorData(null)
  }

  return {
    user,
    isLoading,
    sessions,
    twoFactorData,
    changePassword,
    updateUsername,
    updatePhone,
    loadSessions,
    logoutAllSessions,
    setup2FA,
    confirm2FA,
    disable2FA,
    reset2FASetup,
  }
}