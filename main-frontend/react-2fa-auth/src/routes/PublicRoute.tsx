import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { FullPageSpinner } from '@/components/ui'
import { ROUTES } from '@/utils/constants'

interface PublicRouteProps {
  children: React.ReactNode
}

export function PublicRoute({ children }: PublicRouteProps) {
  const { isAuthenticated, isInitialized } = useAuth()
  const location = useLocation()

  // Показываем загрузку пока проверяем авторизацию
  if (!isInitialized) {
    return <FullPageSpinner text="Загрузка..." />
  }

  // Если авторизован — редирект на dashboard (или откуда пришёл)
  if (isAuthenticated) {
    const from = (location.state as { from?: { pathname: string } })?.from?.pathname || ROUTES.DASHBOARD
    return <Navigate to={from} replace />
  }

  return <>{children}</>
}