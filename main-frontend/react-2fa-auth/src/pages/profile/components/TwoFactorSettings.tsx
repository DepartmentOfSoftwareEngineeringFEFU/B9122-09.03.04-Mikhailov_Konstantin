// src/pages/profile/TwoFactorSettings.tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { ShieldCheck, ShieldOff, Copy, Check } from 'lucide-react';
import { profileApi, type Setup2FAResponse } from '@/api/auth.api';
import { useAuthStore } from '@/store/auth.store';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal, ModalFooter } from '@/components/ui/Modal';

const totpCodeSchema = z.object({
  code: z
    .string()
    .length(6, 'Код должен содержать 6 цифр')
    .regex(/^\d{6}$/, 'Код должен содержать только цифры'),
});

const disableSchema = z.object({
  code: z
    .string()
    .length(6, 'Код должен содержать 6 цифр')
    .regex(/^\d{6}$/, 'Код должен содержать только цифры'),
  password: z.string().min(1, 'Введите пароль'),
});

type TotpCodeForm = z.infer<typeof totpCodeSchema>;
type DisableForm = z.infer<typeof disableSchema>;

export function TwoFactorSettings() {
  const { user, fetchProfile } = useAuthStore();
  const [setupData, setSetupData] = useState<Setup2FAResponse | null>(null);
  const [isSettingUp, setIsSettingUp] = useState(false);
  const [showDisableModal, setShowDisableModal] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const confirmForm = useForm<TotpCodeForm>({
    resolver: zodResolver(totpCodeSchema),
  });

  const disableForm = useForm<DisableForm>({
    resolver: zodResolver(disableSchema),
  });

  const twoFactorEnabled = user?.two_factor_enabled ?? false;

  // === Шаг 1: Нажали "Включить 2FA" ===
  const handleSetup = async () => {
    setIsLoading(true);
    try {
      const response = await profileApi.setup2FA();
      setSetupData(response.data.data);
      setIsSettingUp(true);
    } catch (error: any) {
      const message =
        error.response?.data?.error?.message || 'Ошибка настройки 2FA';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  // === Шаг 2: Подтверждаем код из приложения ===
  const handleConfirm = async (data: TotpCodeForm) => {
    setIsLoading(true);
    try {
      await profileApi.confirm2FA(data.code);
      toast.success('Двухфакторная аутентификация включена');
      setSetupData(null);
      setIsSettingUp(false);
      confirmForm.reset();
      await fetchProfile();
    } catch (error: any) {
      const message =
        error.response?.data?.error?.message || 'Неверный код';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  // === Отключение 2FA ===
  const handleDisable = async (data: DisableForm) => {
    setIsLoading(true);
    try {
      await profileApi.disable2FA(data.code, data.password);
      toast.success('Двухфакторная аутентификация отключена');
      setShowDisableModal(false);
      disableForm.reset();
      await fetchProfile();
    } catch (error: any) {
      const message =
        error.response?.data?.error?.message || 'Ошибка отключения 2FA';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopySecret = async () => {
    if (!setupData) return;
    try {
      await navigator.clipboard.writeText(setupData.secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.error('Не удалось скопировать');
    }
  };

  const handleCancelSetup = () => {
    setSetupData(null);
    setIsSettingUp(false);
    confirmForm.reset();
  };

  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5" />
            Двухфакторная аутентификация
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* === 2FA Выключена и нет процесса настройки === */}
          {!twoFactorEnabled && !isSettingUp && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Двухфакторная аутентификация добавляет дополнительный уровень
                защиты вашего аккаунта. При входе потребуется ввести код из
                приложения-аутентификатора.
              </p>
              <Button onClick={handleSetup} disabled={isLoading}>
                {isLoading ? 'Настройка...' : 'Включить 2FA'}
              </Button>
            </div>
          )}

          {/* === Процесс настройки: QR код + ввод кода === */}
          {!twoFactorEnabled && isSettingUp && setupData && (
            <div className="space-y-6">
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-4">
                  Отсканируйте QR-код в приложении-аутентификаторе
                  (Google Authenticator, Authy, и т.д.)
                </p>
                <img
                  src={`data:image/png;base64,${setupData.qr_code_base64}`}
                  alt="QR Code для 2FA"
                  className="mx-auto w-48 h-48"
                />
              </div>

              {/* Ручной ввод секрета */}
              <div className="space-y-2">
                <p className="text-xs text-gray-500">
                  Или введите ключ вручную:
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 rounded bg-gray-100 px-3 py-2 text-sm font-mono break-all">
                    {setupData.secret}
                  </code>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCopySecret}
                  >
                    {copied ? (
                      <Check className="h-4 w-4 text-green-600" />
                    ) : (
                      <Copy className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* Форма подтверждения */}
              <form
                onSubmit={confirmForm.handleSubmit(handleConfirm)}
                className="space-y-4"
              >
                <Input
                  label="Код из приложения"
                  placeholder="000000"
                  maxLength={6}
                  error={confirmForm.formState.errors.code?.message}
                  {...confirmForm.register('code')}
                />
                <div className="flex gap-3">
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? 'Проверка...' : 'Подтвердить и включить'}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={handleCancelSetup}
                  >
                    Отмена
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* === 2FA Включена === */}
          {twoFactorEnabled && (
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-600">
                <ShieldCheck className="h-5 w-5" />
                <span className="text-sm font-medium">
                  Двухфакторная аутентификация включена
                </span>
              </div>
              <Button
                variant="ghost"
                onClick={() => setShowDisableModal(true)}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <ShieldOff className="h-4 w-4 mr-2" />
                Отключить 2FA
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* === Модалка отключения 2FA === */}
      <Modal
        isOpen={showDisableModal}
        onClose={() => {
          setShowDisableModal(false);
          disableForm.reset();
        }}
        title="Отключить двухфакторную аутентификацию"
        size="md"
      >
        <form onSubmit={disableForm.handleSubmit(handleDisable)}>
          <div className="space-y-4 p-4">
            <p className="text-sm text-gray-600">
              Для отключения 2FA введите текущий код из приложения-аутентификатора
              и ваш пароль.
            </p>
            <Input
              label="Код из приложения"
              placeholder="000000"
              maxLength={6}
              error={disableForm.formState.errors.code?.message}
              {...disableForm.register('code')}
            />
            <Input
              label="Пароль"
              type="password"
              placeholder="Ваш текущий пароль"
              error={disableForm.formState.errors.password?.message}
              {...disableForm.register('password')}
            />
          </div>
          <ModalFooter>
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setShowDisableModal(false);
                disableForm.reset();
              }}
            >
              Отмена
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="bg-red-600 hover:bg-red-700"
            >
              {isLoading ? 'Отключение...' : 'Отключить 2FA'}
            </Button>
          </ModalFooter>
        </form>
      </Modal>
    </>
  );
}