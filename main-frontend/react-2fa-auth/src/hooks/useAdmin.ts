import { useState } from 'react'
import { toast } from 'sonner'
import { adminApi } from '@/api'
import { useApiError } from '@/hooks/useApiError'
import type {
  User,
  UserRole,
  UsersFilter,
  AuditLogEntry,
  AuditLogFilter,
} from '@/types'

export function useAdmin() {
  const { handleError } = useApiError()

  const [isLoading, setIsLoading] = useState(false)
  const [users, setUsers] = useState<User[]>([])
  const [usersTotal, setUsersTotal] = useState(0)
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([])
  const [auditLogTotal, setAuditLogTotal] = useState(0)

  // Загрузка пользователей
  const loadUsers = async (params?: UsersFilter) => {
    setIsLoading(true)
    try {
      const response = await adminApi.getUsers(params)
      // Проверяем структуру ответа
      if (Array.isArray(response)) {
        setUsers(response)
        setUsersTotal(response.length)
      } else if (response?.items) {
        setUsers(response.items)
        setUsersTotal(response.total || 0)
      } else {
        setUsers([])
        setUsersTotal(0)
      }
      return response
    } catch (error) {
      handleError(error, 'Ошибка загрузки пользователей')
      setUsers([])
      setUsersTotal(0)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  // Получить одного пользователя
  const getUser = async (userId: string): Promise<User | null> => {
    setIsLoading(true)
    try {
      const user = await adminApi.getUser(userId)
      return user
    } catch (error) {
      handleError(error, 'Ошибка загрузки пользователя')
      return null
    } finally {
      setIsLoading(false)
    }
  }

  // Изменить роль
  const changeRole = async (userId: string, role: UserRole): Promise<boolean> => {
    setIsLoading(true)
    try {
      await adminApi.changeRole(userId, { role })
      toast.success('Роль изменена')
      return true
    } catch (error) {
      handleError(error, 'Ошибка изменения роли')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Заблокировать пользователя
  const deactivateUser = async (userId: string): Promise<boolean> => {
    setIsLoading(true)
    try {
      await adminApi.deactivateUser(userId)
      toast.success('Пользователь заблокирован')
      return true
    } catch (error) {
      handleError(error, 'Ошибка блокировки')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Разблокировать пользователя
  const activateUser = async (userId: string): Promise<boolean> => {
    setIsLoading(true)
    try {
      await adminApi.activateUser(userId)
      toast.success('Пользователь разблокирован')
      return true
    } catch (error) {
      handleError(error, 'Ошибка разблокировки')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Удалить пользователя
  const deleteUser = async (userId: string): Promise<boolean> => {
    setIsLoading(true)
    try {
      await adminApi.deleteUser(userId)
      toast.success('Пользователь удалён')
      return true
    } catch (error) {
      handleError(error, 'Ошибка удаления')
      return false
    } finally {
      setIsLoading(false)
    }
  }

  // Загрузка аудит-лога
  const loadAuditLog = async (params?: AuditLogFilter) => {
    setIsLoading(true)
    try {
      const response = await adminApi.getAuditLog(params)
      if (Array.isArray(response)) {
        setAuditLog(response)
        setAuditLogTotal(response.length)
      } else if (response?.items) {
        setAuditLog(response.items)
        setAuditLogTotal(response.total || 0)
      } else {
        setAuditLog([])
        setAuditLogTotal(0)
      }
      return response
    } catch (error) {
      handleError(error, 'Ошибка загрузки аудит-лога')
      setAuditLog([])
      setAuditLogTotal(0)
      return null
    } finally {
      setIsLoading(false)
    }
  }

  return {
    isLoading,
    users,
    usersTotal,
    auditLog,
    auditLogTotal,
    loadUsers,
    getUser,
    changeRole,
    deactivateUser,
    activateUser,
    deleteUser,
    loadAuditLog,
  }
}