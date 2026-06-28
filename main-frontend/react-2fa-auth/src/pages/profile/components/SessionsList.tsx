// src/pages/profile/components/SessionsList.tsx
import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { Monitor, Smartphone, Globe, LogOut, Loader2 } from 'lucide-react';
import { authApi } from '@/api/auth.api';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Modal, ModalFooter } from '@/components/ui/Modal';
import { storage } from '@/utils/storage';

interface Session {
  device: string;
  ip_address: string | null;
  created_at: string;
  last_used_at: string | null;
}

export function SessionsList() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showLogoutAllModal, setShowLogoutAllModal] = useState(false);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const fetchSessions = async () => {
    setIsLoading(true);
    try {
      const response = await authApi.getSessions();
      // ⚠️ API возвращает { status, data, meta, timestamp }
      // Сессии находятся в response.data.data
      const sessionsData = response.data.data;
      
      // Проверяем что это массив
      if (Array.isArray(sessionsData)) {
        setSessions(sessionsData);
      } else {
        console.error('Sessions is not an array:', sessionsData);
        setSessions([]);
      }
    } catch (error: any) {
      console.error('Failed to fetch sessions:', error);
      toast.error('Не удалось загрузить сессии');
      setSessions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const handleLogoutAll = async () => {
    setIsLoggingOut(true);
    try {
      await authApi.logoutAll();
      toast.success('Вы вышли со всех устройств');
      setShowLogoutAllModal(false);
      // После logoutAll пользователь будет разлогинен,
      // перенаправление произойдёт автоматически через interceptor
    } catch (error: any) {
      const message =
        error.response?.data?.error?.message || 'Ошибка выхода';
      toast.error(message);
    } finally {
      storage.clearTokens()
      setIsLoggingOut(false);
      window.location.href = '/login';
    }
  };

  const getDeviceIcon = (device: string) => {
    const deviceLower = device.toLowerCase();
    if (deviceLower.includes('mobile') || deviceLower.includes('android') || deviceLower.includes('iphone')) {
      return <Smartphone className="h-5 w-5 text-gray-500" />;
    }
    return <Monitor className="h-5 w-5 text-gray-500" />;
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Неизвестно';
    return new Date(dateString).toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5" />
            Активные сессии
          </CardTitle>
          {sessions.length > 1 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLogoutAllModal(true)}
              className="text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Выйти везде
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : sessions.length === 0 ? (
            <p className="text-center text-gray-500 py-4">
              Нет активных сессий
            </p>
          ) : (
            <div className="space-y-3">
              {sessions.map((session, index) => (
                <SessionItem
                  key={`${session.device}-${session.created_at}-${index}`}
                  session={session}
                  isFirst={index === 0}
                  formatDate={formatDate}
                  getDeviceIcon={getDeviceIcon}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Модалка подтверждения выхода везде */}
      <Modal
        isOpen={showLogoutAllModal}
        onClose={() => setShowLogoutAllModal(false)}
        title="Выйти со всех устройств?"
        size="sm"
      >
        <div className="p-4">
          <p className="text-sm text-gray-600">
            Вы будете разлогинены на всех устройствах, включая текущее.
            Потребуется повторный вход.
          </p>
        </div>
        <ModalFooter>
          <Button
            variant="ghost"
            onClick={() => setShowLogoutAllModal(false)}
          >
            Отмена
          </Button>
          <Button
            onClick={handleLogoutAll}
            disabled={isLoggingOut}
            className="bg-red-600 hover:bg-red-700"
          >
            {isLoggingOut ? 'Выход...' : 'Выйти везде'}
          </Button>
        </ModalFooter>
      </Modal>
    </>
  );
}

// === Компонент отдельной сессии ===

interface SessionItemProps {
  session: Session;
  isFirst: boolean;
  formatDate: (date: string | null) => string;
  getDeviceIcon: (device: string) => React.ReactNode;
}

function SessionItem({ session, isFirst, formatDate, getDeviceIcon }: SessionItemProps) {
  return (
    <div
      className={`
        flex items-start gap-3 p-3 rounded-lg border
        ${isFirst ? 'border-green-200 bg-green-50' : 'border-gray-200'}
      `}
    >
      <div className="mt-0.5">
        {getDeviceIcon(session.device)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm truncate">
            {session.device || 'Неизвестное устройство'}
          </span>
          {isFirst && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">
              Текущая
            </span>
          )}
        </div>
        <div className="text-xs text-gray-500 mt-1 space-y-0.5">
          {session.ip_address && (
            <p>IP: {session.ip_address}</p>
          )}
          <p>Вход: {formatDate(session.created_at)}</p>
          {session.last_used_at && (
            <p>Активность: {formatDate(session.last_used_at)}</p>
          )}
        </div>
      </div>
    </div>
  );
}