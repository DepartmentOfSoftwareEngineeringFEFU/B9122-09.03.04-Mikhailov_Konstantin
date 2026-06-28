import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { FullPageSpinner } from '@/components/ui'
import { ROUTES } from '@/utils/constants'

interface AdminRouteProps {
  children: React.ReactNode
}

export function AdminRoute({ children }: AdminRouteProps) {
  const { isAuthenticated, isInitialized, isAdmin } = useAuth()

  // Показываем загрузку пока проверяем авторизацию
  if (!isInitialized) {
    return <FullPageSpinner text="Загрузка..." />
  }

  // Если не авторизован — редирект на логин
  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />
  }

  // Если не админ — редирект на дашборд
  if (!isAdmin) {
    return <Navigate to={ROUTES.DASHBOARD} replace />
  }

  return <>{children}</>
}