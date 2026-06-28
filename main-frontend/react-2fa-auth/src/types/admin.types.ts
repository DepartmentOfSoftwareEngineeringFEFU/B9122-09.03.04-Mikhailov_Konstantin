import type { UserRole } from './user.types'
import type { PaginationParams, SortParams } from './api.types'

// Фильтры для списка пользователей
export interface UsersFilter extends PaginationParams, SortParams {
  search?: string
  role?: UserRole
  is_active?: boolean
}

// Запрос на изменение роли
export interface ChangeRoleRequest {
  role: UserRole
}

// Запись аудит-лога (соответствует бэкенду)
export interface AuditLogEntry {
  id: number
  actor_uid: string | null
  target_uid: string | null
  action: string
  details: Record<string, unknown> | null
  ip_address: string | null
  user_agent: string | null
  request_id: string | null
  success: boolean
  created_at: string
}

// Фильтры аудит-лога
export interface AuditLogFilter extends PaginationParams {
  user_id?: string
  action?: string
  date_from?: string
  date_to?: string
}