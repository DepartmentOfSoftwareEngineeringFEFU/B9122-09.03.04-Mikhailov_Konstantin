import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { useApiError } from '@/hooks'
import { authApi } from '@/api'
import { Button, Input, Alert } from '@/components/ui'
import { forgotPasswordSchema, type ForgotPasswordFormData } from '@/utils/validation'
import { ROUTES } from '@/utils/constants'
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react'

export function ForgotPasswordPage() {
  const { handleError } = useApiError()
  const [isLoading, setIsLoading] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [submittedEmail, setSubmittedEmail] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
  })

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true)
    try {
      await authApi.requestPasswordReset({ email: data.email })
      setSubmittedEmail(data.email)
      setIsSuccess(true)
    } catch (error) {
      handleError(error, 'Ошибка отправки')
    } finally {
      setIsLoading(false)
    }
  }

  if (isSuccess) {
    return (
      <div className="card text-center">
        <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="h-6 w-6 text-green-600" />
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Проверьте почту
        </h1>

        <p className="text-gray-500 mb-6">
          Мы отправили инструкции по восстановлению пароля на{' '}
          <span className="font-medium text-gray-900">{submittedEmail}</span>
        </p>

        <Alert variant="info" className="mb-6 text-left">
          Если письмо не пришло, проверьте папку «Спам» или попробуйте отправить запрос повторно.
        </Alert>

        <div className="space-y-3">
          <Button
            variant="secondary"
            className="w-full"
            onClick={() => setIsSuccess(false)}
          >
            Отправить повторно
          </Button>

          <Link to={ROUTES.LOGIN} className="block">
            <Button variant="ghost" className="w-full">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Вернуться к входу
            </Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          Восстановление пароля
        </h1>
        <p className="text-gray-500 mt-2">
          Введите email для получения инструкций
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <Input
          {...register('email')}
          type="email"
          label="Email"
          placeholder="your@email.com"
          error={errors.email?.message}
          leftIcon={<Mail className="h-4 w-4" />}
          autoComplete="email"
          autoFocus
        />

        <Button
          type="submit"
          className="w-full"
          isLoading={isLoading}
        >
          Отправить инструкции
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