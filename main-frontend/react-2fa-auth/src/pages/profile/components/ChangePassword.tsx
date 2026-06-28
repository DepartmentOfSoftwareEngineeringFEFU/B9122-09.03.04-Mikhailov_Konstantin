import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useProfile } from '@/hooks'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
} from '@/components/ui'
import { changePasswordSchema, type ChangePasswordFormData } from '@/utils/validation'
import { Lock, Eye, EyeOff } from 'lucide-react'

export function ChangePassword() {
  const { isLoading, changePassword } = useProfile()
  const [isOpen, setIsOpen] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
  })

  const onSubmit = async (data: ChangePasswordFormData) => {
    const success = await changePassword(data.currentPassword, data.newPassword)
    if (success) {
      reset()
      setIsOpen(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lock className="h-5 w-5" />
          Пароль
        </CardTitle>
        <CardDescription>
          Регулярно меняйте пароль для безопасности
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!isOpen ? (
          <Button variant="outline" onClick={() => setIsOpen(true)}>
            Изменить пароль
          </Button>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              {...register('currentPassword')}
              type="password"
              label="Текущий пароль"
              placeholder="Введите текущий пароль"
              error={errors.currentPassword?.message}
              autoFocus
            />

            <Input
              {...register('newPassword')}
              type="password"
              label="Новый пароль"
              placeholder="Минимум 8 символов"
              error={errors.newPassword?.message}
              hint="Заглавные, строчные буквы и цифры"
            />

            <Input
              {...register('confirmPassword')}
              type="password"
              label="Подтверждение пароля"
              placeholder="Повторите новый пароль"
              error={errors.confirmPassword?.message}
            />

            <div className="flex gap-3">
              <Button type="submit" isLoading={isLoading}>
                Сохранить
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setIsOpen(false)
                  reset()
                }}
              >
                Отмена
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  )
}