import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'
import { useAuth, useApiError } from '@/hooks'
import { Button, Input } from '@/components/ui'
import { registerSchema, type RegisterFormData } from '@/utils/validation'
import { ROUTES } from '@/utils/constants'
import { Mail, Lock, User } from 'lucide-react'
import { useAuthStore } from '@/store/auth.store'


export function RegisterPage() {
  const navigate = useNavigate()
  const { register: registerUser, isLoading } = useAuthStore()
  const { handleError } = useApiError()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data.email, data.password, data.username || undefined)
      toast.success('Регистрация успешна!')
      navigate(ROUTES.LOGIN)
    } catch (error) {
      handleError(error, 'Ошибка регистрации')
    }
  }

  return (
    <div className="card">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Регистрация</h1>
        <p className="text-gray-500 mt-2">
          Создайте аккаунт для начала работы
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

        <Input
          {...register('username')}
          label="Имя пользователя"
          placeholder="username"
          error={errors.username?.message}
          leftIcon={<User className="h-4 w-4" />}
          hint="Только буквы, цифры и _"
          autoComplete="username"
        />

        <Input
          {...register('password')}
          type="password"
          label="Пароль"
          placeholder="Минимум 8 символов"
          error={errors.password?.message}
          leftIcon={<Lock className="h-4 w-4" />}
          hint="Заглавные, строчные буквы и цифры"
          autoComplete="new-password"
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
          Зарегистрироваться
        </Button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          Уже есть аккаунт?{' '}
          <Link to={ROUTES.LOGIN} className="link">
            Войти
          </Link>
        </p>
      </div>
    </div>
  )
}