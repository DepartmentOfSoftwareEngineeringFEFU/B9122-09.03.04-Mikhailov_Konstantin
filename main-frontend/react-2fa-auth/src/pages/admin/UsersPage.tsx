import { useEffect, useState, useRef } from 'react'
import { useAdmin } from '@/hooks'
import { Card, CardContent, Spinner, Pagination } from '@/components/ui'
import { UsersTable, UsersFilter } from './components'
import { Users } from 'lucide-react'
import type { UserRole } from '@/types'

const PAGE_SIZE = 10

interface FilterValues {
  search: string
  role: UserRole | ''
  is_active: string
}

export function UsersPage() {
  const {
    users,
    usersTotal,
    isLoading,
    loadUsers,
    changeRole,
    deactivateUser,
    activateUser,
    deleteUser,
  } = useAdmin()

  const [currentPage, setCurrentPage] = useState(1)
  const [filters, setFilters] = useState<FilterValues>({
    search: '',
    role: '',
    is_active: '',
  })

  // Используем ref чтобы избежать лишних перерисовок
  const isFirstMount = useRef(true)

  const totalPages = Math.ceil(usersTotal / PAGE_SIZE)

  const fetchUsers = () => {
    const params: Record<string, unknown> = {
      page: currentPage,
      size: PAGE_SIZE,
    }

    if (filters.search) params.search = filters.search
    if (filters.role) params.role = filters.role
    if (filters.is_active) params.is_active = filters.is_active === 'true'

    loadUsers(params)
  }

  // Загрузка при монтировании и изменении страницы/фильтров
  useEffect(() => {
    fetchUsers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage])

  // Отдельный эффект для первой загрузки
  useEffect(() => {
    if (isFirstMount.current) {
      isFirstMount.current = false
      return
    }
  }, [])

  const handleFilter = (newFilters: FilterValues) => {
    setFilters(newFilters)
    setCurrentPage(1)
    
    // Загружаем с новыми фильтрами
    const params: Record<string, unknown> = {
      page: 1,
      size: PAGE_SIZE,
    }

    if (newFilters.search) params.search = newFilters.search
    if (newFilters.role) params.role = newFilters.role
    if (newFilters.is_active) params.is_active = newFilters.is_active === 'true'

    loadUsers(params)
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleRefresh = () => {
    fetchUsers()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Users className="h-6 w-6" />
            Пользователи
          </h1>
          <p className="text-gray-500 mt-1">
            Всего пользователей: {usersTotal}
          </p>
        </div>
      </div>

      <Card>
        <CardContent className="p-6">
          <UsersFilter onFilter={handleFilter} isLoading={isLoading} />
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading && users.length === 0 ? (
            <div className="flex justify-center py-12">
              <Spinner size="lg" />
            </div>
          ) : (
            <UsersTable
              users={users}
              isLoading={isLoading}
              onChangeRole={changeRole}
              onDeactivate={deactivateUser}
              onActivate={activateUser}
              onDelete={deleteUser}
              onRefresh={handleRefresh}
            />
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