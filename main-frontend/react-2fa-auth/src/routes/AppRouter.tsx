import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/store/auth.store'
import { ROUTES } from '@/utils/constants'

// Layouts
import { Layout, AuthLayout } from '@/components/layout'

// Route guards
import { PrivateRoute } from './PrivateRoute'
import { AdminRoute } from './AdminRoute'
import { PublicRoute } from './PublicRoute'

// Auth pages
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { ForgotPasswordPage } from '@/pages/auth/ForgotPasswordPage'
import { ResetPasswordPage } from '@/pages/auth/ResetPasswordPage'
import { ConfirmEmailPage } from '@/pages/auth/ConfirmEmailPage'

// Protected pages
import { DashboardPage } from '@/pages/dashboard/DashboardPage'
import { ProfilePage } from '@/pages/profile/ProfilePage'
import { PredictionPage } from '@/pages/prediction/PredictionPage'

// Admin pages
import { UsersPage } from '@/pages/admin/UsersPage'
import { UserDetailPage } from '@/pages/admin/UserDetailPage'
import { AuditLogPage } from '@/pages/admin/AuditLogPage'

// Other
import { NotFoundPage } from '@/pages/NotFoundPage'

export function AppRouter() {
  const initialize = useAuthStore((state) => state.initialize)

  // Инициализация при загрузке приложения
  useEffect(() => {
    initialize()
  }, [initialize])

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes (Auth) — только для неавторизованных */}
        <Route
          element={
            <PublicRoute>
              <AuthLayout />
            </PublicRoute>
          }
        >
          <Route path={ROUTES.LOGIN} element={<LoginPage />} />
          <Route path={ROUTES.REGISTER} element={<RegisterPage />} />
          <Route path={ROUTES.FORGOT_PASSWORD} element={<ForgotPasswordPage />} />
        </Route>

        {/* Эти страницы доступны всем (с токеном в URL) */}
        <Route element={<AuthLayout />}>
          <Route path={ROUTES.RESET_PASSWORD} element={<ResetPasswordPage />} />
          <Route path={ROUTES.CONFIRM_EMAIL} element={<ConfirmEmailPage />} />
        </Route>

        {/* Protected routes */}
        <Route
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route path={ROUTES.DASHBOARD} element={<DashboardPage />} />
          <Route path={ROUTES.PROFILE} element={<ProfilePage />} />
          <Route path="/prediction" element={<PredictionPage />} />
          
          {/* Admin routes */}
          <Route
            path={ROUTES.ADMIN_USERS}
            element={
              <AdminRoute>
                <UsersPage />
              </AdminRoute>
            }
          />
          <Route
            path={ROUTES.ADMIN_USER_DETAIL}
            element={
              <AdminRoute>
                <UserDetailPage />
              </AdminRoute>
            }
          />
          <Route
            path={ROUTES.ADMIN_AUDIT_LOG}
            element={
              <AdminRoute>
                <AuditLogPage />
              </AdminRoute>
            }
          />
        </Route>

        {/* Redirects */}
        <Route path={ROUTES.HOME} element={<Navigate to={ROUTES.DASHBOARD} replace />} />
        <Route path={ROUTES.ADMIN} element={<Navigate to={ROUTES.ADMIN_USERS} replace />} />

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  )
}