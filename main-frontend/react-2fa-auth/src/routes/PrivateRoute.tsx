import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { FullPageSpinner } from '@/components/ui'
import { ROUTES } from '@/utils/constants'

interface PrivateRouteProps {
  children: React.ReactNode
}

export function PrivateRoute({ children }: PrivateRouteProps) {
  const { isAuthenticated, isInitialized } = useAuth()
  const location = useLocation()

  // Показываем загрузку пока проверяем авторизацию
  if (!isInitialized) {
    return <FullPageSpinner text="Загрузка..." />
  }

  // Если не авторизован — редирект на логин
  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} state={{ from: location }} replace />
  }

  return <>{children}</>
}