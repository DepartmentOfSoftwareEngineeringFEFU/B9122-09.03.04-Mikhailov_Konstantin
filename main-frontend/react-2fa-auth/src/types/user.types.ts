// Роли пользователей
export type UserRole = 'USER' | 'MODERATOR' | 'ADMIN' | 'OWNER'

// Основная сущность пользователя
export interface User {
  uid: string
  email: string
  username: string | null
  phone_number: string | null
  role: UserRole
  is_active: boolean
  is_email_verified: boolean
  two_factor_enabled: boolean
  created_at: string
  updated_at: string
}

// Данные профиля (может отличаться от User)
export interface Profile extends User {
  last_login_at: string | null
}

// Активная сессия (соответствует бэкенду)
export interface Session {
  device: string
  ip_address: string
  created_at: string
  last_used_at: string | null
  is_current?: boolean
}