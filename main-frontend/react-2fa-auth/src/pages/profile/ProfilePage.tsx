import {
  ProfileInfo,
  ChangePassword,
  TwoFactorSettings,
  SessionsList,
} from './components'

export function ProfilePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Настройки профиля</h1>
        <p className="text-gray-500 mt-1">
          Управляйте своим аккаунтом и настройками безопасности
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Левая колонка */}
        <div className="space-y-6">
          <ProfileInfo />
          <ChangePassword />
        </div>

        {/* Правая колонка */}
        <div className="space-y-6">
          <TwoFactorSettings />
          <SessionsList />
        </div>
      </div>
    </div>
  )
}