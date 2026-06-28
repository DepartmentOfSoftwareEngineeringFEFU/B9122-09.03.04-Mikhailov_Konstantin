import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useProfile } from '@/hooks'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Input,
  Avatar,
  Badge,
} from '@/components/ui'
import { ROLE_LABELS } from '@/utils/constants'
import { User, Mail, Phone, Edit2, X, Check } from 'lucide-react'

const usernameSchema = z.object({
  username: z
    .string()
    .min(3, 'Минимум 3 символа')
    .max(30, 'Максимум 30 символов')
    .regex(/^[a-zA-Z0-9_]+$/, 'Только буквы, цифры и _'),
})

const phoneSchema = z.object({
  phone_number: z
    .string()
    .min(10, 'Минимум 10 символов')
    .regex(/^\+?[0-9]+$/, 'Некорректный формат'),
})

type UsernameFormData = z.infer<typeof usernameSchema>
type PhoneFormData = z.infer<typeof phoneSchema>

export function ProfileInfo() {
  const { user, isLoading, updateUsername, updatePhone } = useProfile()

  const [editingField, setEditingField] = useState<'username' | 'phone_number' | null>(null)

  const usernameForm = useForm<UsernameFormData>({
    resolver: zodResolver(usernameSchema),
    defaultValues: { username: user?.username || '' },
  })

  const phoneForm = useForm<PhoneFormData>({
    resolver: zodResolver(phoneSchema),
    defaultValues: { phone_number: user?.phone_number || '' },
  })

  const handleUsernameSubmit = async (data: UsernameFormData) => {
    const success = await updateUsername(data.username)
    if (success) {
      setEditingField(null)
    }
  }

  const handlePhoneSubmit = async (data: PhoneFormData) => {
    const success = await updatePhone(data.phone_number)
    if (success) {
      setEditingField(null)
    }
  }

  const cancelEdit = () => {
    setEditingField(null)
    usernameForm.reset({ username: user?.username || '' })
    phoneForm.reset({ phone_number: user?.phone_number || '' })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Профиль</CardTitle>
        <CardDescription>Основная информация о вашем аккаунте</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Avatar и роль */}
        <div className="flex items-center gap-4">
          <Avatar name={user?.username || user?.email} size="xl" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {user?.username || user?.email?.split('@')[0]}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={user?.role === 'ADMIN' || user?.role === 'OWNER' ? 'info' : 'default'}>
                {user?.role ? ROLE_LABELS[user.role] : 'Пользователь'}
              </Badge>
              {user?.is_email_verified ? (
                <Badge variant="success">Email подтверждён</Badge>
              ) : (
                <Badge variant="warning">Email не подтверждён</Badge>
              )}
            </div>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-6 space-y-4">
          {/* Email (не редактируется) */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Mail className="h-5 w-5 text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Email</p>
                <p className="font-medium">{user?.email}</p>
              </div>
            </div>
          </div>

          {/* Username */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3 flex-1">
              <div className="p-2 bg-gray-100 rounded-lg">
                <User className="h-5 w-5 text-gray-600" />
              </div>

              {editingField === 'username' ? (
                <form
                  onSubmit={usernameForm.handleSubmit(handleUsernameSubmit)}
                  className="flex items-center gap-2 flex-1"
                >
                  <Input
                    {...usernameForm.register('username')}
                    placeholder="username"
                    error={usernameForm.formState.errors.username?.message}
                    className="flex-1"
                    autoFocus
                  />
                  <Button type="submit" size="sm" isLoading={isLoading}>
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button type="button" size="sm" variant="ghost" onClick={cancelEdit}>
                    <X className="h-4 w-4" />
                  </Button>
                </form>
              ) : (
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Имя пользователя</p>
                  <p className="font-medium">{user?.username || '—'}</p>
                </div>
              )}
            </div>

            {editingField !== 'username' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingField('username')}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Phone */}
          <div className="flex items-center justify-between py-3">
            <div className="flex items-center gap-3 flex-1">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Phone className="h-5 w-5 text-gray-600" />
              </div>

              {editingField === 'phone_number' ? (
                <form
                  onSubmit={phoneForm.handleSubmit(handlePhoneSubmit)}
                  className="flex items-center gap-2 flex-1"
                >
                  <Input
                    {...phoneForm.register('phone_number')}
                    placeholder="+7 999 123 45 67"
                    error={phoneForm.formState.errors.phone_number?.message}
                    className="flex-1"
                    autoFocus
                  />
                  <Button type="submit" size="sm" isLoading={isLoading}>
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button type="button" size="sm" variant="ghost" onClick={cancelEdit}>
                    <X className="h-4 w-4" />
                  </Button>
                </form>
              ) : (
                <div className="flex-1">
                  <p className="text-sm text-gray-500">Телефон</p>
                  <p className="font-medium">{user?.phone_number || '—'}</p>
                </div>
              )}
            </div>

            {editingField !== 'phone_number' && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setEditingField('phone_number')}
              >
                <Edit2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}