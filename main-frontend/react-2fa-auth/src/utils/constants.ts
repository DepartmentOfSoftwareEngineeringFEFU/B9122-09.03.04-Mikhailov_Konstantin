export const APP_NAME = 'REFS'

export const ROUTES = {
  // Public
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  CONFIRM_EMAIL: '/confirm-email',
  
  // Protected
  DASHBOARD: '/dashboard',
  PROFILE: '/profile',
  
  // Admin
  ADMIN: '/admin',
  ADMIN_USERS: '/admin/users',
  ADMIN_USER_DETAIL: '/admin/users/:id',
  ADMIN_AUDIT_LOG: '/admin/audit-log',
} as const

export const ROLES = {
  USER: 'USER',
  MODERATOR: 'MODERATOR',
  ADMIN: 'ADMIN',
  OWNER: 'OWNER',
} as const

export const ROLE_LABELS: Record<string, string> = {
  USER: 'Пользователь',
  MODERATOR: 'Модератор',
  ADMIN: 'Администратор',
  OWNER: 'Владелец',
}

export const TOKEN_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
} as const