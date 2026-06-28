import { useState } from 'react'
import { Input, Select, Button } from '@/components/ui'
import { Search, X, Filter } from 'lucide-react'
import type { UserRole } from '@/types'

interface FilterValues {
  search: string
  role: UserRole | ''
  is_active: string
}

interface UsersFilterProps {
  onFilter: (filters: FilterValues) => void
  isLoading: boolean
}

export function UsersFilter({ onFilter, isLoading }: UsersFilterProps) {
  const [filters, setFilters] = useState<FilterValues>({
    search: '',
    role: '',
    is_active: '',
  })
  const [isOpen, setIsOpen] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onFilter(filters)
  }

  const handleReset = () => {
    const emptyFilters = { search: '', role: '' as const, is_active: '' }
    setFilters(emptyFilters)
    onFilter(emptyFilters)
  }

  const hasFilters = filters.search || filters.role || filters.is_active

  const roleOptions = [
    { value: '', label: 'Все роли' },
    { value: 'USER', label: 'Пользователь' },
    { value: 'MODERATOR', label: 'Модератор' },
    { value: 'ADMIN', label: 'Администратор' },
    { value: 'OWNER', label: 'Владелец' },
  ]

  const statusOptions = [
    { value: '', label: 'Все статусы' },
    { value: 'true', label: 'Активные' },
    { value: 'false', label: 'Заблокированные' },
  ]

  return (
    <div className="space-y-4">
      {/* Основная строка поиска */}
      <form onSubmit={handleSubmit} className="flex gap-3">
        <div className="flex-1">
          <Input
            placeholder="Поиск по email или имени..."
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            leftIcon={<Search className="h-4 w-4" />}
          />
        </div>

        <Button type="submit" isLoading={isLoading}>
          Найти
        </Button>

        <Button
          type="button"
          variant={isOpen ? 'secondary' : 'outline'}
          onClick={() => setIsOpen(!isOpen)}
        >
          <Filter className="h-4 w-4" />
        </Button>

        {hasFilters && (
          <Button type="button" variant="ghost" onClick={handleReset}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </form>

      {/* Расширенные фильтры */}
      {isOpen && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
          <Select
            label="Роль"
            options={roleOptions}
            value={filters.role}
            onChange={(e) =>
              setFilters({ ...filters, role: e.target.value as UserRole | '' })
            }
          />

          <Select
            label="Статус"
            options={statusOptions}
            value={filters.is_active}
            onChange={(e) => setFilters({ ...filters, is_active: e.target.value })}
          />
        </div>
      )}
    </div>
  )
}