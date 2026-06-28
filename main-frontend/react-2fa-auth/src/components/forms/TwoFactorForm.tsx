import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Button, Input } from '@/components/ui'
import { twoFactorSchema, type TwoFactorFormData } from '@/utils/validation'
import { ShieldCheck } from 'lucide-react'

interface TwoFactorFormProps {
  onSubmit: (code: string) => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}

export function TwoFactorForm({ onSubmit, onCancel, isLoading }: TwoFactorFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<TwoFactorFormData>({
    resolver: zodResolver(twoFactorSchema),
  })

  const handleFormSubmit = async (data: TwoFactorFormData) => {
    await onSubmit(data.code)
  }

  return (
    <div className="text-center">
      <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
        <ShieldCheck className="h-6 w-6 text-blue-600" />
      </div>

      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        Двухфакторная аутентификация
      </h2>

      <p className="text-gray-500 text-sm mb-6">
        Введите 6-значный код из приложения аутентификации
      </p>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        <Input
          {...register('code')}
          placeholder="000000"
          error={errors.code?.message}
          className="text-center text-2xl tracking-widest"
          maxLength={6}
          autoComplete="one-time-code"
          autoFocus
        />

        <div className="flex gap-3">
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            className="flex-1"
            disabled={isLoading}
          >
            Назад
          </Button>
          <Button
            type="submit"
            className="flex-1"
            isLoading={isLoading}
          >
            Подтвердить
          </Button>
        </div>
      </form>
    </div>
  )
}