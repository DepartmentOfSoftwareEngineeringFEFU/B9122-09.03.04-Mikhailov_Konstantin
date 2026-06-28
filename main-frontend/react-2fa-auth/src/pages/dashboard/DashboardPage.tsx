import { useAuth } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { ROLE_LABELS } from '@/utils/constants'
import { Shield, Mail, Phone, Clock } from 'lucide-react'

export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Дашборд</h1>
        <p className="text-gray-500 mt-1">Добро пожаловать в систему</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-blue-600" />
              Email
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium">{user?.email}</p>
            <Badge variant={user?.is_email_verified ? 'success' : 'warning'} className="mt-2">
              {user?.is_email_verified ? 'Подтверждён' : 'Не подтверждён'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-600" />
              Роль
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium">
              {user?.role ? ROLE_LABELS[user.role] : '—'}
            </p>
            <Badge variant={user?.two_factor_enabled ? 'success' : 'warning'} className="mt-2">
              2FA: {user?.two_factor_enabled ? 'Включена' : 'Выключена'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-blue-600" />
              Дата регистрации
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-medium">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString('ru-RU')
                : '—'}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}