// Базовые типы ответов API
export interface ApiResponse<T> {
  status: 'success' | 'error'
  data?: T
  error?: ApiError
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, string[]>
}

// Пагинация
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// Параметры запросов
export interface PaginationParams {
  page?: number
  size?: number
}

export interface SortParams {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}