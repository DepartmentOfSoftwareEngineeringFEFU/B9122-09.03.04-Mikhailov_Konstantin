import { TOKEN_KEYS } from './constants'

export const storage = {
  // Токены
  getAccessToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEYS.ACCESS_TOKEN)
  },
  
  setAccessToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEYS.ACCESS_TOKEN, token)
  },
  
  getRefreshToken: (): string | null => {
    return localStorage.getItem(TOKEN_KEYS.REFRESH_TOKEN)
  },
  
  setRefreshToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEYS.REFRESH_TOKEN, token)
  },
  
  setTokens: (accessToken: string, refreshToken: string): void => {
    storage.setAccessToken(accessToken)
    storage.setRefreshToken(refreshToken)
  },
  
  clearTokens: (): void => {
    localStorage.removeItem(TOKEN_KEYS.ACCESS_TOKEN)
    localStorage.removeItem(TOKEN_KEYS.REFRESH_TOKEN)
  },
  
  // Generic методы
  get: <T>(key: string): T | null => {
    const item = localStorage.getItem(key)
    if (!item) return null
    try {
      return JSON.parse(item) as T
    } catch {
      return null
    }
  },
  
  set: <T>(key: string, value: T): void => {
    localStorage.setItem(key, JSON.stringify(value))
  },
  
  remove: (key: string): void => {
    localStorage.removeItem(key)
  },
  
  clear: (): void => {
    localStorage.clear()
  },
}