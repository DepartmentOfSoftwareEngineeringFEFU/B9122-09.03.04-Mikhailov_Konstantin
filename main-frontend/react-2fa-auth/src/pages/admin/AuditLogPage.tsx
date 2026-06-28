import { useEffect, useState, useRef } from 'react'
import { adminApi } from '@/api'
import { useApiError } from '@/hooks'
import {
  Card,
  CardContent,
  Spinner,
  Pagination,
  Input,
  Button,
  Badge,
} from '@/components/ui'
import { ScrollText, Search, RefreshCw, CheckCircle, XCircle } from 'lucide-react'
import type { AuditLogEntry } from '@/types'

const PAGE_SIZE = 20

export function AuditLogPage() {
  const { handleError } = useApiError()

  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [searchUserId, setSearchUserId] = useState('')

  const hasFetched = useRef(false)
  const totalPages = Math.ceil(total / PAGE_SIZE)

  const fetchAuditLog = async (page: number, userId?: string) => {
    setIsLoading(true)
    try {
      const params: Record<string, unknown> = {
        page,
        size: PAGE_SIZE,
      }

      if (userId) params.user_id = userId

      const response = await adminApi.getAuditLog(params)

      // Сервер возвращает массив напрямую в data
      if (Array.isArray(response)) {
        setAuditLog(response)
        setTotal(response.length)
      } else {
        setAuditLog([])
        setTotal(0)
      }
    } catch (error) {
      handleError(error, 'Ошибка загрузки аудит-лога')
      setAuditLog([])
      setTotal(0)
    } finally {
      setIsLoading(false)
    }
  }

  // Первоначальная загрузка
  useEffect(() => {
    if (hasFetched.current) return
    hasFetched.current = true
    fetchAuditLog(1)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setCurrentPage(1)
    fetchAuditLog(1, searchUserId)
  }

  const handleRefresh = () => {
    fetchAuditLog(currentPage, searchUserId)
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    fetchAuditLog(page, searchUserId)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  const getActionBadgeVariant = (action: string): 'info' | 'error' | 'warning' | 'success' | 'default' => {
    const actionLower = action?.toLowerCase() || ''
    if (actionLower.includes('failed')) return 'error'
    if (actionLower.includes('login') && actionLower.includes('success')) return 'success'
    if (actionLower.includes('register')) return 'info'
    if (actionLower.includes('deactivate') || actionLower.includes('delete')) return 'error'
    if (actionLower.includes('change') || actionLower.includes('update')) return 'warning'
    if (actionLower.includes('logout')) return 'default'
    return 'info'
  }

  const getActionLabel = (action: string): string => {
    const labels: Record<string, string> = {
      'user.login.success': 'Успешный вход',
      'user.login.failed': 'Неудачный вход',
      'user.registered': 'Регистрация',
      'user.logout': 'Выход',
      'user.logout.all': 'Выход со всех устройств',
      'user.deactivated': 'Блокировка',
      'user.activated': 'Разблокировка',
      'email.confirmed': 'Email подтверждён',
      'role.changed': 'Изменение роли',
      'password.changed': 'Смена пароля',
      'token.refreshed': 'Обновление токена',
      '2fa.enabled': '2FA включена',
      '2fa.disabled': '2FA отключена',
    }
    return labels[action] || action
  }

  const formatDetails = (details: Record<string, unknown> | null): string => {
    if (!details) return '—'
    
    const parts: string[] = []
    
    if (details.reason) parts.push(`Причина: ${details.reason}`)
    if (details.device) parts.push(`Устройство: ${details.device}`)
    if (details.old_role && details.new_role) {
      parts.push(`${details.old_role} → ${details.new_role}`)
    }
    if (details.username) parts.push(`Username: ${details.username}`)
    if (details.revoked_sessions) parts.push(`Сессий: ${details.revoked_sessions}`)
    
    return parts.length > 0 ? parts.join(', ') : '—'
  }

  const truncateUid = (uid: string | null): string => {
    if (!uid) return '—'
    return `${uid.slice(0, 8)}...`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <ScrollText className="h-6 w-6" />
            Аудит лог
          </h1>
          <p className="text-gray-500 mt-1">
            История всех действий в системе ({auditLog.length} записей)
          </p>
        </div>

        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Обновить
        </Button>
      </div>

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="flex-1">
              <Input
                placeholder="Поиск по ID пользователя (actor_uid)..."
                value={searchUserId}
                onChange={(e) => setSearchUserId(e.target.value)}
                leftIcon={<Search className="h-4 w-4" />}
              />
            </div>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? <Spinner size="sm" /> : 'Найти'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading && auditLog.length === 0 ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : auditLog.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              Записи не найдены
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                      Время
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                      Действие
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                      Статус
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                      Актор
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                      Цель
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                      IP
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                      Детали
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {auditLog.map((entry) => (
                    <tr
                      key={entry.id}
                      className="border-b border-gray-100 hover:bg-gray-50"
                    >
                      <td className="py-3 px-4 text-sm text-gray-500 whitespace-nowrap">
                        {formatDate(entry.created_at)}
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant={getActionBadgeVariant(entry.action)}>
                          {getActionLabel(entry.action)}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        {entry.success ? (
                          <CheckCircle className="h-5 w-5 text-green-500" />
                        ) : (
                          <XCircle className="h-5 w-5 text-red-500" />
                        )}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500 font-mono">
                        <span title={entry.actor_uid || undefined}>
                          {truncateUid(entry.actor_uid)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500 font-mono">
                        <span title={entry.target_uid || undefined}>
                          {truncateUid(entry.target_uid)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">
                        {entry.ip_address || '—'}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500 max-w-xs">
                        {formatDetails(entry.details)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
          isLoading={isLoading}
        />
      )}
    </div>
  )
}