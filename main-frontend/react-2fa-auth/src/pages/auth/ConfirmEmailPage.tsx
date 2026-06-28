import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authApi } from '@/api'
import { Button, Spinner } from '@/components/ui'
import { ROUTES } from '@/utils/constants'
import { CheckCircle, XCircle, Mail } from 'lucide-react'

type Status = 'loading' | 'success' | 'error' | 'no-token'

export function ConfirmEmailPage() {
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState<Status>('loading')
  const [errorMessage, setErrorMessage] = useState('')

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setStatus('no-token')
      return
    }

    const confirmEmail = async () => {
      try {
        await authApi.confirmEmail(token)
        setStatus('success')
      } catch (error: any) {
        setStatus('error')
        setErrorMessage(
          error?.response?.data?.detail ||
          error?.response?.data?.message ||
          'Ошибка подтверждения email'
        )
      }
    }

    confirmEmail()
  }, [token])

  // Загрузка
  if (status === 'loading') {
    return (
      <div className="card text-center py-12">
        <Spinner size="lg" className="mx-auto mb-4" />
        <p className="text-gray-500">Подтверждаем ваш email...</p>
      </div>
    )
  }

  // Нет токена
  if (status === 'no-token') {
    return (
      <div className="card text-center">
        <div className="mx-auto w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
          <Mail className="h-6 w-6 text-yellow-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Отсутствует токен
        </h1>

        <p className="text-gray-500 mb-6">
          Ссылка для подтверждения email некорректна. Проверьте, что вы перешли по полной ссылке из письма.
        </p>

        <Link to={ROUTES.LOGIN}>
          <Button className="w-full">
            Перейти к входу
          </Button>
        </Link>
      </div>
    )
  }

  // Ошибка
  if (status === 'error') {
    return (
      <div className="card text-center">
        <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <XCircle className="h-6 w-6 text-red-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Ошибка подтверждения
        </h1>

        <p className="text-gray-500 mb-6">
          {errorMessage || 'Не удалось подтвердить email. Возможно, ссылка устарела.'}
        </p>

        <div className="space-y-3">
          <Link to={ROUTES.LOGIN}>
            <Button className="w-full">
              Войти и запросить новую ссылку
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  // Успех
  return (
    <div className="card text-center">
      <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
        <CheckCircle className="h-6 w-6 text-green-600" />
      </div>

      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Email подтверждён
      </h1>

      <p className="text-gray-500 mb-6">
        Ваш email успешно подтверждён. Теперь вы можете пользоваться всеми функциями системы.
      </p>

      <Link to={ROUTES.DASHBOARD}>
        <Button className="w-full">
          Перейти в систему
        </Button>
      </Link>
    </div>
  )
}