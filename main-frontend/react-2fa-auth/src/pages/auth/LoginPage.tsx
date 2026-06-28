// src/pages/auth/LoginPage.tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { useAuthStore } from '@/store/auth.store';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/Card';
import { TwoFactorStep } from './TwoFactorStep';

const loginSchema = z.object({
  email: z.string().email('Введите корректный email'),
  password: z.string().min(1, 'Введите пароль'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, pendingTwoFactor } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);

  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    try {
      const result = await login(data.email, data.password);

      if (result === 'success') {
        toast.success('Вход выполнен успешно');
        navigate(from, { replace: true });
      }
      // Если result === '2fa_required', компонент перерисуется
      // и покажет TwoFactorStep (pendingTwoFactor станет не null)
    } catch (error: any) {
      const message =
        error.response?.data?.error?.message || 'Ошибка входа';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTwoFactorSuccess = () => {
    toast.success('Вход выполнен успешно');
    navigate(from, { replace: true });
  };

  // Если ждём 2FA — показываем форму ввода кода
  if (pendingTwoFactor) {
    return <TwoFactorStep onSuccess={handleTwoFactorSuccess} />;
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle>Вход</CardTitle>
        <CardDescription>Войдите в свой аккаунт</CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          <Input
            label="Email"
            type="email"
            placeholder="you@example.com"
            error={errors.email?.message}
            {...register('email')}
          />
          <Input
            label="Пароль"
            type="password"
            placeholder="••••••••"
            error={errors.password?.message}
            {...register('password')}
          />
        </CardContent>
        <CardFooter className="flex flex-col gap-3">
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Вход...' : 'Войти'}
          </Button>
          <div className="flex justify-between w-full text-sm">
            <a href="/forgot-password" className="text-blue-600 hover:underline">
              Забыли пароль?
            </a>
            <a href="/register" className="text-blue-600 hover:underline">
              Регистрация
            </a>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
}