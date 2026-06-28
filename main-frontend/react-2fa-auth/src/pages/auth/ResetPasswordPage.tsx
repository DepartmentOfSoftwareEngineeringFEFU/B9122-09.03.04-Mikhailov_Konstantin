import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useApiError } from '@/hooks'
import { authApi } from '@/api'
import { Button, Input, Alert } from '@/components/ui'
import { resetPasswordSchema, type ResetPasswordFormData } from '@/utils/validation'
import { ROUTES } from '@/utils/constants'
import { Lock, ArrowLeft, CheckCircle, XCircle } from 'lucide-react'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { handleError } = useApiError()

  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [tokenError, setTokenError] = useState(false)

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setTokenError(true)
    }
  }, [token])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
  })

  const onSubmit = async (data: ResetPasswordFormData) => {
    if (!token) return

    setIsLoading(true)
    try {
      await authApi.confirmPasswordReset({
        token,
        new_password: data.password,
      })
      setIsSuccess(true)
    } catch (error) {
      handleError(error, 'Ошибка сброса пароля')
    } finally {
      setIsLoading(false)
    }
  }

  // Ошибка токена
  if (tokenError) {
    return (
      <div className="card text-center">
        <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
          <XCircle className="h-6 w-6 text-red-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Недействительная ссылка
        </h1>

        <p className="text-gray-500 mb-6">
          Ссылка для сброса пароля недействительна или устарела.
        </p>

        <Link to={ROUTES.FORGOT_PASSWORD}>
          <Button className="w-full">
            Запросить новую ссылку
          </Button>
        </Link>
      </div>
    )
  }

  // Успех
  if (isSuccess) {
    return (
      <div className="card text-center">
        <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="h-6 w-6 text-green-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Пароль изменён
        </h1>

        <p className="text-gray-500 mb-6">
          Ваш пароль успешно изменён. Теперь вы можете войти с новым паролем.
        </p>

        <Link to={ROUTES.LOGIN}>
          <Button className="w-full">
            Войти в систему
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Новый пароль
        </h1>
        <p className="text-gray-500 mt-2">
          Придумайте новый надёжный пароль
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          {...register('password')}
          type="password"
          label="Новый пароль"
          placeholder="Минимум 8 символов"
          error={errors.password?.message}
          leftIcon={<Lock className="h-4 w-4" />}
          hint="Заглавные, строчные буквы и цифры"
          autoComplete="new-password"
          autoFocus
        />

        <Input
          {...register('confirmPassword')}
          type="password"
          label="Подтверждение пароля"
          placeholder="Повторите пароль"
          error={errors.confirmPassword?.message}
          leftIcon={<Lock className="h-4 w-4" />}
          autoComplete="new-password"
        />

        <Button
          type="submit"
          className="w-full"
          isLoading={isLoading}
        >
          Сохранить пароль
        </Button>
      </form>

      <div className="mt-6 text-center">
        <Link to={ROUTES.LOGIN} className="text-sm link inline-flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" />
          Вернуться к входу
        </Link>
      </div>
    </div>
  )
}