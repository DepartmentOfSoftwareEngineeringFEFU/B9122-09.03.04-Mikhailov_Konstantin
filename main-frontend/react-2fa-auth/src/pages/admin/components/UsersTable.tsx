import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Avatar, Badge, Button, Modal, ModalFooter, Alert, Select } from '@/components/ui'
import { ROUTES, ROLE_LABELS } from '@/utils/constants'
import type { User, UserRole } from '@/types'
import {
  Eye,
  Shield,
  ShieldOff,
  Trash2,
  UserCog,
  MoreVertical,
} from 'lucide-react'

interface UsersTableProps {
  users: User[]
  isLoading: boolean
  onChangeRole: (userId: string, role: UserRole) => Promise<boolean>
  onDeactivate: (userId: string) => Promise<boolean>
  onActivate: (userId: string) => Promise<boolean>
  onDelete: (userId: string) => Promise<boolean>
  onRefresh: () => void
}

export function UsersTable({
  users,
  isLoading,
  onChangeRole,
  onDeactivate,
  onActivate,
  onDelete,
  onRefresh,
}: UsersTableProps) {
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [modalType, setModalType] = useState<'role' | 'block' | 'unblock' | 'delete' | null>(null)
  const [newRole, setNewRole] = useState<UserRole>('USER')
  const [actionMenuUser, setActionMenuUser] = useState<string | null>(null)

  const openModal = (user: User, type: 'role' | 'block' | 'unblock' | 'delete') => {
    setSelectedUser(user)
    setModalType(type)
    setNewRole(user.role)
    setActionMenuUser(null)
  }

  const closeModal = () => {
    setSelectedUser(null)
    setModalType(null)
  }

  const handleAction = async () => {
    if (!selectedUser) return

    let success = false

    switch (modalType) {
      case 'role':
        success = await onChangeRole(selectedUser.uid, newRole)
        break
      case 'block':
        success = await onDeactivate(selectedUser.uid)
        break
      case 'unblock':
        success = await onActivate(selectedUser.uid)
        break
      case 'delete':
        success = await onDelete(selectedUser.uid)
        break
    }

    if (success) {
      closeModal()
      onRefresh()
    }
  }

  const roleOptions = [
    { value: 'USER', label: 'Пользователь' },
    { value: 'MODERATOR', label: 'Модератор' },
    { value: 'ADMIN', label: 'Администратор' },
    { value: 'OWNER', label: 'Владелец' },
  ]

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    })
  }

  if (users.length === 0 && !isLoading) {
    return (
      <div className="text-center py-12 text-gray-500">
        Пользователи не найдены
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                Пользователь
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                Роль
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                Статус
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                2FA
              </th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">
                Регистрация
              </th>
              <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">
                Действия
              </th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.uid} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-3 px-4">
                  <div className="flex items-center gap-3">
                    <Avatar name={user.username || user.email} size="sm" />
                    <div>
                      <p className="font-medium text-gray-900">
                        {user.username || '—'}
                      </p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <Badge
                    variant={
                      user.role === 'ADMIN' || user.role === 'OWNER'
                        ? 'info'
                        : user.role === 'MODERATOR'
                        ? 'warning'
                        : 'default'
                    }
                  >
                    {ROLE_LABELS[user.role]}
                  </Badge>
                </td>
                <td className="py-3 px-4">
                  <Badge variant={user.is_active ? 'success' : 'error'}>
                    {user.is_active ? 'Активен' : 'Заблокирован'}
                  </Badge>
                </td>
                <td className="py-3 px-4">
                  <Badge variant={user.two_factor_enabled ? 'success' : 'default'}>
                    {user.two_factor_enabled ? 'Вкл' : 'Выкл'}
                  </Badge>
                </td>
                <td className="py-3 px-4 text-sm text-gray-500">
                  {formatDate(user.created_at)}
                </td>
                <td className="py-3 px-4">
                  <div className="flex items-center justify-end gap-2 relative">
                    <Link to={ROUTES.ADMIN_USER_DETAIL.replace(':id', user.uid)}>
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </Link>

                    <div className="relative">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setActionMenuUser(actionMenuUser === user.uid ? null : user.uid)
                        }
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>

                      {actionMenuUser === user.uid && (
                        <>
                          <div
                            className="fixed inset-0 z-10"
                            onClick={() => setActionMenuUser(null)}
                          />
                          <div className="absolute right-0 mt-1 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
                            <button
                              onClick={() => openModal(user, 'role')}
                              className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                            >
                              <UserCog className="h-4 w-4" />
                              Изменить роль
                            </button>

                            {user.is_active ? (
                              <button
                                onClick={() => openModal(user, 'block')}
                                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-yellow-600 hover:bg-yellow-50"
                              >
                                <ShieldOff className="h-4 w-4" />
                                Заблокировать
                              </button>
                            ) : (
                              <button
                                onClick={() => openModal(user, 'unblock')}
                                className="flex items-center gap-2 w-full px-4 py-2 text-sm text-green-600 hover:bg-green-50"
                              >
                                <Shield className="h-4 w-4" />
                                Разблокировать
                              </button>
                            )}

                            <button
                              onClick={() => openModal(user, 'delete')}
                              className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                            >
                              <Trash2 className="h-4 w-4" />
                              Удалить
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Модалка изменения роли */}
      <Modal
        isOpen={modalType === 'role'}
        onClose={closeModal}
        title="Изменение роли"
        description={`Изменить роль пользователя ${selectedUser?.email}`}
      >
        <Select
          label="Новая роль"
          options={roleOptions}
          value={newRole}
          onChange={(e) => setNewRole(e.target.value as UserRole)}
        />
        <ModalFooter>
          <Button variant="secondary" onClick={closeModal}>
            Отмена
          </Button>
          <Button onClick={handleAction} isLoading={isLoading}>
            Сохранить
          </Button>
        </ModalFooter>
      </Modal>

      {/* Модалка блокировки */}
      <Modal
        isOpen={modalType === 'block'}
        onClose={closeModal}
        title="Блокировка пользователя"
      >
        <Alert variant="warning">
          Вы уверены, что хотите заблокировать пользователя{' '}
          <strong>{selectedUser?.email}</strong>?
          <br />
          Пользователь не сможет войти в систему.
        </Alert>
        <ModalFooter>
          <Button variant="secondary" onClick={closeModal}>
            Отмена
          </Button>
          <Button variant="danger" onClick={handleAction} isLoading={isLoading}>
            Заблокировать
          </Button>
        </ModalFooter>
      </Modal>

      {/* Модалка разблокировки */}
      <Modal
        isOpen={modalType === 'unblock'}
        onClose={closeModal}
        title="Разблокировка пользователя"
      >
        <Alert variant="info">
          Разблокировать пользователя <strong>{selectedUser?.email}</strong>?
        </Alert>
        <ModalFooter>
          <Button variant="secondary" onClick={closeModal}>
            Отмена
          </Button>
          <Button onClick={handleAction} isLoading={isLoading}>
            Разблокировать
          </Button>
        </ModalFooter>
      </Modal>

      {/* Модалка удаления */}
      <Modal
        isOpen={modalType === 'delete'}
        onClose={closeModal}
        title="Удаление пользователя"
      >
        <Alert variant="error">
          Вы уверены, что хотите удалить пользователя{' '}
          <strong>{selectedUser?.email}</strong>?
          <br />
          Это действие нельзя отменить!
        </Alert>
        <ModalFooter>
          <Button variant="secondary" onClick={closeModal}>
            Отмена
          </Button>
          <Button variant="danger" onClick={handleAction} isLoading={isLoading}>
            Удалить
          </Button>
        </ModalFooter>
      </Modal>
    </>
  )
}