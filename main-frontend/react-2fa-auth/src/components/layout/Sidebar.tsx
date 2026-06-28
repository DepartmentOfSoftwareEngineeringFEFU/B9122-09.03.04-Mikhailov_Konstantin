import { NavLink, useLocation } from 'react-router-dom'
import { useAuth } from '@/hooks'
import { ROUTES } from '@/utils/constants'
import { cn } from '@/utils/cn'
import {
  LayoutDashboard,
  User,
  Users,
  ScrollText,
  Shield,
  X,
  Calculator
} from 'lucide-react'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

interface NavItem {
  label: string
  href: string
  icon: React.ReactNode
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  {
    label: 'Дашборд',
    href: ROUTES.DASHBOARD,
    icon: <LayoutDashboard className="h-5 w-5" />,
  },
  {
    label: 'Профиль',
    href: ROUTES.PROFILE,
    icon: <User className="h-5 w-5" />,
  },
  { 
    label: 'Прогноз', 
    href: '/prediction', 
    icon: <Calculator className="h-5 w-5"/> 
  },
]

const adminNavItems: NavItem[] = [
  {
    label: 'Пользователи',
    href: ROUTES.ADMIN_USERS,
    icon: <Users className="h-5 w-5" />,
    adminOnly: true,
  },
  {
    label: 'Аудит лог',
    href: ROUTES.ADMIN_AUDIT_LOG,
    icon: <ScrollText className="h-5 w-5" />,
    adminOnly: true,
  },
]

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { isAdmin } = useAuth()
  const location = useLocation()

  const NavLinkItem = ({ item }: { item: NavItem }) => (
    <NavLink
      to={item.href}
      onClick={onClose}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
          isActive
            ? 'bg-blue-50 text-blue-700'
            : 'text-gray-700 hover:bg-gray-100'
        )
      }
    >
      {item.icon}
      {item.label}
    </NavLink>
  )

  const sidebarContent = (
    <div className="flex flex-col h-full">
      {/* Logo for mobile */}
      <div className="flex items-center justify-between h-16 px-4 border-b border-gray-200 lg:hidden">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <Shield className="h-5 w-5 text-white" />
          </div>
          <span className="font-semibold text-gray-900">REFS</span>
        </div>
        <button
          onClick={onClose}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavLinkItem key={item.href} item={item} />
          ))}
        </div>

        {/* Admin section */}
        {isAdmin && (
          <div className="pt-6">
            <p className="px-3 mb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Администрирование
            </p>
            <div className="space-y-1">
              {adminNavItems.map((item) => (
                <NavLinkItem key={item.href} item={item} />
              ))}
            </div>
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          REFS v1.0
        </p>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 lg:hidden',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {sidebarContent}
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:fixed lg:inset-y-0 bg-white border-r border-gray-200">
        {sidebarContent}
      </aside>
    </>
  )
}