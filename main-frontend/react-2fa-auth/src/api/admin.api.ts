import { authClient } from "./client"
import type {
  User,
  UsersFilter,
  ChangeRoleRequest,
  AuditLogEntry,
  AuditLogFilter,
  PaginatedResponse,
} from '@/types'

// Тип обёртки ответа от бэкенда
interface ApiResponse<T> {
  status: string
  data: T
  meta?: Record<string, unknown>
  timestamp?: string
}

export const adminApi = {
  // Получить список пользователей
  getUsers: async (params?: UsersFilter): Promise<PaginatedResponse<User>> => {
    const response = await authClient.get<ApiResponse<PaginatedResponse<User>>>('/admin/users', {
      params,
    })
    return response.data.data
  },

  // Получить пользователя по ID
  getUser: async (userId: string): Promise<User> => {
    const response = await authClient.get<ApiResponse<User>>(`/admin/users/${userId}`)
    return response.data.data
  },

  // Изменить роль пользователя
  changeRole: async (userId: string, data: ChangeRoleRequest): Promise<User> => {
    const response = await authClient.patch<ApiResponse<User>>(
      `/admin/users/${userId}/role`,
      data
    )
    return response.data.data
  },

  // Удалить пользователя
  deleteUser: async (userId: string): Promise<void> => {
    await authClient.delete(`/admin/users/${userId}`)
  },

  // Деактивировать (заблокировать) пользователя
  deactivateUser: async (userId: string): Promise<User> => {
    const response = await authClient.patch<ApiResponse<User>>(
      `/admin/users/${userId}/deactivate`
    )
    return response.data.data
  },

  // Активировать (разблокировать) пользователя
  activateUser: async (userId: string): Promise<User> => {
    const response = await authClient.patch<ApiResponse<User>>(
      `/admin/users/${userId}/activate`
    )
    return response.data.data
  },

  // Получить аудит-лог
  getAuditLog: async (
    params?: AuditLogFilter
  ): Promise<PaginatedResponse<AuditLogEntry>> => {
    const response = await authClient.get<ApiResponse<PaginatedResponse<AuditLogEntry>>>(
      '/admin/audit-log',
      { params }
    )
    return response.data.data
  },
}