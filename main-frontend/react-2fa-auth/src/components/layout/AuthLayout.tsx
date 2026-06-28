import { Outlet, Link } from 'react-router-dom'
import { Shield } from 'lucide-react'
import { ROUTES } from '@/utils/constants'

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <Link to={ROUTES.HOME} className="flex items-center gap-2 w-fit">
            <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <Shield className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900">REFS</span>
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8 py-12">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-gray-500">
            &copy; {new Date().getFullYear()} REFS. Все права защищены.
          </p>
        </div>
      </footer>
    </div>
  )
}