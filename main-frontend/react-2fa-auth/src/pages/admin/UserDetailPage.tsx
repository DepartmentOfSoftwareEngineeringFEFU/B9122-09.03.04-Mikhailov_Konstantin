import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { adminApi } from '@/api'
import { useApiError } from '@/hooks'
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  Avatar,
  Spinner,
  Alert,
} from '@/components/ui'
import { ROUTES, ROLE_LABELS } from '@/utils/constants'
import type { User } from '@/types'
import {
  ArrowLeft,
  Mail,
  User as UserIcon,
  Phone,
  Shield,
  Calendar,
  Clock,
} from 'lucide-react'

export function UserDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { handleError } = useApiError()

  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(false)

  // Предотвращаем повторные запросы
  const hasFetched = useRef(false)

  useEffect(() => {
    // Если уже загружали или нет id — выходим
    if (hasFetched.current || !id) return
    hasFetched.current = true

    const fetchUser = async () => {
      setIsLoading(true)
      try {
        const data = await adminApi.getUser(id)
        setUser(data)
      } catch (err) {
        handleError(err, 'Ошибка загрузки пользователя')
        setError(true)
      } finally {
        setIsLoading(false)
      }
    }

    fetchUser()
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return '—'
    return new Date(dateString).toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getRoleLabel = (role: string) => {
    const upperRole = role?.toUpperCase()
    return ROLE_LABELS[upperRole] || role
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !user) {
    return (
      <div className="space-y-6">
        <Alert variant="error" title="Ошибка">
          Пользователь не найден
        </Alert>
        <Link to={ROUTES.ADMIN_USERS}>
          <Button variant="secondary" leftIcon={<ArrowLeft className="h-4 w-4" />}>
            Назад к списку
          </Button>
        </Link>
      </div>
    )
  }

  const roleUpper = user.role?.toUpperCase()

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          onClick={() => navigate(ROUTES.ADMIN_USERS)}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Профиль пользователя
          </h1>
          <p className="text-gray-500">{user.email}</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Основная информация */}
        <Card>
          <CardHeader>
            <CardTitle>Информация</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center gap-4">
              <Avatar name={user.username || user.email} size="xl" />
              <div>
                <h3 className="text-lg font-semibold">
                  {user.username || 'Без имени'}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <Badge
                    variant={
                      roleUpper === 'ADMIN' || roleUpper === 'OWNER'
                        ? 'info'
                        : 'default'
                    }
                  >
                    {getRoleLabel(user.role)}
                  </Badge>
                  <Badge variant={user.is_active ? 'success' : 'error'}>
                    {user.is_active ? 'Активен' : 'Заблокирован'}
                  </Badge>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <Mail className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Email</p>
                  <p className="font-medium">{user.email}</p>
                  <Badge
                    variant={user.is_email_verified ? 'success' : 'warning'}
                    className="mt-1"
                  >
                    {user.is_email_verified ? 'Подтверждён' : 'Не подтверждён'}
                  </Badge>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <UserIcon className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Имя пользователя</p>
                  <p className="font-medium">{user.username || '—'}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <Phone className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Телефон</p>
                  <p className="font-medium">{user.phone_number || '—'}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Безопасность и даты */}
        <Card>
          <CardHeader>
            <CardTitle>Безопасность и активность</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Shield className="h-5 w-5 text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Двухфакторная аутентификация</p>
                <Badge variant={user.two_factor_enabled ? 'success' : 'warning'}>
                  {user.two_factor_enabled ? 'Включена' : 'Выключена'}
                </Badge>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Calendar className="h-5 w-5 text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Дата регистрации</p>
                <p className="font-medium">{formatDate(user.created_at)}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-100 rounded-lg">
                <Clock className="h-5 w-5 text-gray-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Последнее обновление</p>
                <p className="font-medium">{formatDate(user.updated_at)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}