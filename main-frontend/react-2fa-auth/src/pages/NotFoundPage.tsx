import { Link } from 'react-router-dom'
import { Button } from '@/components/ui'
import { ROUTES } from '@/utils/constants'
import { Home } from 'lucide-react'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <p className="text-2xl font-semibold text-gray-900 mt-4">
          Страница не найдена
        </p>
        <p className="text-gray-500 mt-2">
          Запрашиваемая страница не существует или была удалена
        </p>
        <Link to={ROUTES.DASHBOARD} className="inline-block mt-6">
          <Button leftIcon={<Home className="h-4 w-4" />}>
            На главную
          </Button>
        </Link>
      </div>
    </div>
  )
}