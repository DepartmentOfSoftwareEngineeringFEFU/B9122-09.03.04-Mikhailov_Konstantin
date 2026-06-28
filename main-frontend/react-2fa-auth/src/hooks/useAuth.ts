// hooks/useAuth.ts

import { useAuthStore } from "@/store/auth.store";
import { useCallback } from "react";

export const useAuth = () => {
  const {
    user,
    isAuthenticated,
    isLoading,
    isInitialized,
    is2FAPending,
    register,
    authToken,
    login,
    complete2FA,
    cancel2FA,
    logout,
    logoutAll,
    refreshUser,
  } = useAuthStore();

  // Вычисляемые свойства
  const isAdmin = ["ADMIN", "OWNER"].includes(user?.role ?? "");
  const isModerator = ["MODERATOR", "ADMIN", "OWNER"].includes(
    user?.role ?? "",
  );
  const is2FAEnabled = user?.two_factor_enabled ?? false;

  // Обёртки с обработкой ошибок (опционально)
  const handleLogin = useCallback(
    async (email: string, password: string) => {
      try {
        await login(email, password);
      } catch (error) {
        throw error;
      }
    },
    [login],
  );

  const handleComplete2FA = useCallback(
    async (totpCode: string) => {
      try {
        await complete2FA(totpCode);
      } catch (error) {
        throw error;
      }
    },
    [complete2FA],
  );

  const handleRegister = useCallback(
    async (username: string, email: string, password: string) => {
      try {
        await register(username, email, password);
      } catch (error) {
        throw error;
      }
    },
    [register],
  );

  return {
    // Состояние
    user,
    isAuthenticated,
    isLoading,
    isInitialized,
    is2FAPending,
    hasAuthToken: !!authToken, // Для проверки, можно ли показывать форму 2FA

    // Вычисляемые значения
    isAdmin,
    isModerator,
    is2FAEnabled,
    isEmailVerified: user?.is_email_verified ?? false,

    // Методы
    login: handleLogin,
    complete2FA: handleComplete2FA,
    cancel2FA,
    logout,
    logoutAll,
    refreshUser,
  };
};
